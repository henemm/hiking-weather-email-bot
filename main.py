#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json  # Wird für Testdaten benötigt
import logging
import sys
import traceback
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import os
from dotenv import load_dotenv
import datetime
import yaml
import math

from wetter import wetterdaten, kurztext
from wetter.config import ConfigError
from emailversand import sende_email, EmailError
from src.etappen import lade_heutige_etappe, lade_etappen
from wetter.fetch import hole_wetterdaten, fetch_weather_data
from wetter.kurztext import generiere_kurznachricht
from wetter.delta import delta_warnung

# Debug-Ausgaben für .env-Ladung
print("Aktuelles Arbeitsverzeichnis:", os.getcwd())
print("Suche .env-Datei in:", os.path.join(os.getcwd(), '.env'))
load_dotenv()
print("GMAIL_APP_PW vorhanden:", bool(os.getenv("GMAIL_APP_PW")))

# Logging konfigurieren
def setup_logging() -> None:
    """Konfiguriert das Logging-System"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'weather_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

class WeatherBotError(Exception):
    """Basis-Exception für WeatherBot-Fehler"""
    pass

class DataError(WeatherBotError):
    """Fehler bei der Datenverarbeitung"""
    pass

class ReportError(WeatherBotError):
    """Fehler bei der Berichterstellung"""
    pass

def parse_args() -> argparse.Namespace:
    """
    Parst die Kommandozeilenargumente.
    
    Returns:
        Namespace mit den geparsten Argumenten
        
    Raises:
        SystemExit: Bei ungültigen Argumenten
    """
    parser = argparse.ArgumentParser(description="Wetterwarnung für Wanderungen")
    parser.add_argument("--modus", choices=["abend", "morgen", "tag"], required=True,
                       help="Art der Wettermeldung")
    parser.add_argument("--dry-run", action="store_true",
                       help="Nur Ausgabe, kein Versand")
    parser.add_argument("--input", help="Pfad zu Testdaten (JSON)")
    parser.add_argument("--inreach", action="store_true",
                       help="Nachricht für InReach kürzen")
    
    try:
        return parser.parse_args()
    except Exception as e:
        logger.error(f"Fehler beim Parsen der Argumente: {str(e)}")
        parser.print_help()
        sys.exit(1)

def lade_konfiguration() -> Dict[str, Any]:
    """Lädt die Konfiguration aus der YAML-Datei."""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("Konfigurationsdatei config.yaml nicht gefunden")
        sys.exit(1)
    except yaml.YAMLError:
        logger.error("Ungültiges YAML-Format in config.yaml")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
        sys.exit(1)

def hole_wetterdaten_fuer_punkte(punkte, datum: Optional[datetime.date] = None):
    daten = []
    for punkt in punkte:
        lat = punkt["lat"]
        lon = punkt["lon"]
        d = wetterdaten.hole_wetterdaten(lat, lon)
        daten.append(d)
    def safe_max(values, default=0):
        vals = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
        return max(vals) if vals else default
    def safe_min(values, default=0):
        vals = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
        return min(vals) if vals else default
    if daten:
        wetter = {}
        if datum:
            tag_str = datum.strftime("%Y-%m-%d")
            def get_hourly_for_day(d, key):
                times = d.get("hourly", {}).get("time", [])
                values = d.get("hourly", {}).get(key, [])
                filtered = [v for t, v in zip(times, values) if t.startswith(tag_str)]
                return filtered if filtered else []
            def get_daily_for_day(d, key):
                if "daily" in d and key in d["daily"] and "time" in d["daily"]:
                    for i, t in enumerate(d["daily"]["time"]):
                        if t == tag_str:
                            return d["daily"][key][i]
                return None
            # Maximalwerte über alle Punkte und Stunden
            temp_vals = [v for d in daten for v in get_hourly_for_day(d, "temperature_2m")]
            temp_gefuehlt_vals = [v for d in daten for v in get_hourly_for_day(d, "apparent_temperature")]
            wind_vals = [v for d in daten for v in get_hourly_for_day(d, "wind_speed_10m")]
            regen_vals = [v for d in daten for v in get_hourly_for_day(d, "precipitation_probability")]
            gewitter_vals = [v for d in daten for v in get_hourly_for_day(d, "thunderstorm_probability") if v is not None]
            # Fallback auf daily falls keine Stundenwerte vorhanden
            if not temp_vals:
                temp_vals = [get_daily_for_day(d, "temperature_2m_max") for d in daten]
            if not temp_gefuehlt_vals:
                temp_gefuehlt_vals = [get_daily_for_day(d, "apparent_temperature_max") for d in daten]
            if not wind_vals:
                wind_vals = [get_daily_for_day(d, "wind_speed_10m_max") for d in daten]
            if not regen_vals:
                regen_vals = [get_daily_for_day(d, "precipitation_probability_max") for d in daten]
            if not gewitter_vals:
                gewitter_vals = [0]
            wetter["temp"] = safe_max(temp_vals, 0)
            wetter["temp_gefuehlt"] = safe_max(temp_gefuehlt_vals, 0)
            wetter["wind_geschwindigkeit"] = safe_max(wind_vals, 0)
            wetter["wind_richtung"] = "NO"  # Platzhalter
            wetter["regen"] = safe_max(regen_vals, 0)
            wetter["gewitter"] = safe_max(gewitter_vals, 0)
            wetter["regen_zeit"] = datum.strftime("%Y-%m-%dT00:00")
            wetter["gewitter_zeit"] = datum.strftime("%Y-%m-%dT00:00")
            # Nachttemperatur: Minimum über alle Punkte (aus daily)
            nacht_temp_vals = [get_daily_for_day(d, "temperature_2m_min") for d in daten]
            wetter["nacht_temp"] = safe_min(nacht_temp_vals, 0)
        else:
            # Abendmodus: wie gehabt, ggf. anpassen falls gewünscht
            wetter["temp"] = safe_max([d.get("hourly", {}).get("temperature_2m", [None])[0] for d in daten], 0)
            wetter["temp_gefuehlt"] = safe_max([d.get("hourly", {}).get("apparent_temperature", [None])[0] for d in daten], 0)
            wetter["wind_geschwindigkeit"] = safe_max([d.get("hourly", {}).get("wind_speed_10m", [None])[0] for d in daten], 0)
            wetter["wind_richtung"] = "NO"
            wetter["regen"] = safe_max([d.get("hourly", {}).get("precipitation_probability", [None])[0] for d in daten], 0)
            wetter["gewitter"] = safe_max([d.get("hourly", {}).get("thunderstorm_probability", [None])[0] for d in daten], 0)
            wetter["regen_zeit"] = daten[0].get("hourly", {}).get("time", [""])[0] if daten and "hourly" in daten[0] and "time" in daten[0]["hourly"] else ""
            wetter["gewitter_zeit"] = daten[0].get("hourly", {}).get("time", [""])[0] if daten and "hourly" in daten[0] and "time" in daten[0]["hourly"] else ""
        return {"wetter": wetter}
    else:
        return {"wetter": {"temp": 0, "temp_gefuehlt": 0, "wind_geschwindigkeit": 0, "wind_richtung": "", "regen": 0, "gewitter": 0, "regen_zeit": "", "gewitter_zeit": "", "nacht_temp": 0}}

def generiere_wetterbericht(wetterdaten, modus="abend", start_date=None, etappen_data=None):
    """Generiert den Wetterbericht basierend auf den Wetterdaten und dem Modus."""
    try:
        if modus == "morgen":
            return kurztext.generiere_kurznachricht(
                wetterdaten, 
                modus="morgen",
                start_date=start_date,
                etappen_data=etappen_data
            )
        else:
            return kurztext.generiere_kurznachricht(
                wetterdaten,
                start_date=start_date,
                etappen_data=etappen_data
            )
    except Exception as e:
        logger.error(f"Fehler beim Generieren des Wetterberichts: {str(e)}")
        return None

def sende_inreach_nachricht(nachricht, inreach_email, smtp_server, smtp_port, benutzername, passwort, smtp_config):
    """Sendet die InReach-Nachricht."""
    try:
        sende_email(
            nachricht,
            inreach_email,
            smtp_server,
            smtp_port,
            benutzername,
            passwort
        )
        return True
    except Exception as e:
        logger.error(f"Fehler beim Senden der InReach-Nachricht: {str(e)}")
        return False

def max_ohne_none(liste, default=0):
    werte = [v for v in liste if v is not None]
    return max(werte) if werte else default

def lade_abend_wetterdaten(config: Dict[str, Any]) -> Dict[str, Any]:
    etappen = lade_etappen()
    if not etappen:
        raise ValueError("Etappendaten konnten nicht geladen werden")
    startdatum_str = config["startdatum"]
    startdatum = datetime.datetime.strptime(startdatum_str, "%Y-%m-%d").date()
    heute = datetime.date.today()
    differenz = (heute - startdatum).days
    if differenz < 0 or differenz >= len(etappen):
        raise ValueError("Kein gültiger Etappentag – liegt außerhalb des definierten Zeitraums.")
    # Heutige Etappe
    etappe_heute = etappen[differenz]
    letzter_punkt = etappe_heute["punkte"][-1]
    # Nachttemperatur für heute, letzter Punkt
    daten_nacht = fetch_weather_data(letzter_punkt["lat"], letzter_punkt["lon"], heute)
    nacht_temp = daten_nacht["daily"]["temperature_2m_min"][0] if daten_nacht["daily"]["temperature_2m_min"][0] is not None else 0
    nacht_temp_gefuehlt = daten_nacht["daily"].get("apparent_temperature_min", [nacht_temp])[0]
    # Morgige Etappe
    if differenz + 1 >= len(etappen):
        raise ValueError("Keine morgige Etappe mehr vorhanden.")
    etappe_morgen = etappen[differenz + 1]
    punkte_morgen = etappe_morgen["punkte"]
    morgen = heute + datetime.timedelta(days=1)
    alle_daten_morgen = [fetch_weather_data(p["lat"], p["lon"], morgen) for p in punkte_morgen]
    # Maximalwerte für morgen
    hitze = max([d["daily"]["apparent_temperature_max"][0] for d in alle_daten_morgen if d["daily"]["apparent_temperature_max"][0] is not None], default=0)
    regen = max([d["daily"]["precipitation_probability_max"][0] for d in alle_daten_morgen if d["daily"]["precipitation_probability_max"][0] is not None], default=0)
    wind = max([d["daily"]["wind_speed_10m_max"][0] for d in alle_daten_morgen if d["daily"]["wind_speed_10m_max"][0] is not None], default=0)
    gewitter = max_ohne_none([max_ohne_none(d["hourly"]["thunderstorm_probability"]) for d in alle_daten_morgen if d["hourly"]["thunderstorm_probability"]], default=0)
    # Gewittergefahr +1 (übermorgen)
    if differenz + 2 < len(etappen):
        etappe_uebermorgen = etappen[differenz + 2]
        punkte_uebermorgen = etappe_uebermorgen["punkte"]
        uebermorgen = heute + datetime.timedelta(days=2)
        alle_daten_uebermorgen = [fetch_weather_data(p["lat"], p["lon"], uebermorgen) for p in punkte_uebermorgen]
        gewitter_plus1 = max_ohne_none([max_ohne_none(d["hourly"]["thunderstorm_probability"]) for d in alle_daten_uebermorgen if d["hourly"]["thunderstorm_probability"]], default=0)
    else:
        gewitter_plus1 = None
    return {
        "wetter": {
            "nacht_temp": nacht_temp,
            "nacht_temp_gefuehlt": nacht_temp_gefuehlt,
            "hitze": hitze,
            "regen": regen,
            "wind": wind,
            "gewitter": gewitter,
            "gewitter_plus1": gewitter_plus1
        }
    }

def lade_morgen_wetterdaten(etappe: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    etappen = lade_etappen()
    if not etappen:
        raise DataError("Etappendaten konnten nicht geladen werden")
    startdatum_str = config["startdatum"]
    startdatum = datetime.datetime.strptime(startdatum_str, "%Y-%m-%d").date()
    heute = datetime.date.today()
    differenz = (heute - startdatum).days
    if differenz < 0 or differenz >= len(etappen):
        raise ValueError("Kein gültiger Etappentag – liegt außerhalb des definierten Zeitraums.")
    # Heutige Etappe
    etappe_heute = etappen[differenz]
    punkte_heute = etappe_heute["punkte"]
    alle_daten_heute = [fetch_weather_data(p["lat"], p["lon"], heute) for p in punkte_heute]
    # Maximalwerte für heute
    hitze = max([d["daily"]["apparent_temperature_max"][0] for d in alle_daten_heute if d["daily"]["apparent_temperature_max"][0] is not None], default=0)
    regen = max([d["daily"]["precipitation_probability_max"][0] for d in alle_daten_heute if d["daily"]["precipitation_probability_max"][0] is not None], default=0)
    wind = max([d["daily"]["wind_speed_10m_max"][0] for d in alle_daten_heute if d["daily"]["wind_speed_10m_max"][0] is not None], default=0)
    gewitter = max_ohne_none([max_ohne_none(d["hourly"]["thunderstorm_probability"]) for d in alle_daten_heute if d["hourly"]["thunderstorm_probability"]], default=0)
    # Gewittergefahr +1 (morgen)
    if differenz + 1 < len(etappen):
        etappe_morgen = etappen[differenz + 1]
        punkte_morgen = etappe_morgen["punkte"]
        morgen = heute + datetime.timedelta(days=1)
        alle_daten_morgen = [fetch_weather_data(p["lat"], p["lon"], morgen) for p in punkte_morgen]
        gewitter_plus1 = max_ohne_none([max_ohne_none(d["hourly"]["thunderstorm_probability"]) for d in alle_daten_morgen if d["hourly"]["thunderstorm_probability"]], default=0)
    else:
        gewitter_plus1 = None
    return {
        "wetter": {
            "hitze": hitze,
            "regen": regen,
            "wind": wind,
            "gewitter": gewitter,
            "gewitter_plus1": gewitter_plus1
        }
    }

def lade_daten(args: argparse.Namespace, etappe: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lädt Wetterdaten entweder aus Testdatei oder API.
    
    Args:
        args: Kommandozeilenargumente
        etappe: Aktuelle Etappe
        config: Konfiguration
        
    Returns:
        Dictionary mit Wetterdaten
        
    Raises:
        DataError: Bei Problemen mit den Daten
    """
    try:
        if args.input:
            input_path = Path(args.input)
            if not input_path.exists():
                raise DataError(f"Testdaten-Datei nicht gefunden: {args.input}")
            with input_path.open("r") as f:
                daten = json.load(f)
            # Delta-Logik für Tagmodus mit Testdaten
            if args.modus == "tag" and "morgen" in daten and "tag" in daten:
                # Vergleiche die Werte wie im Live-Betrieb
                morgen = daten["morgen"]
                tag = daten["tag"]
                # Prüfe auf Verschlechterung (z.B. Regen, Gewitter, Wind, Hitze)
                schwellen = config["schwellen"]
                warnungen = []
                # Regen
                delta_regen = tag.get("regen", 0) - morgen.get("regen", 0)
                if abs(delta_regen) >= schwellen["delta_prozent"]:
                    if delta_regen > 0:
                        warnungen.append(f"Regenrisiko stark gestiegen: {morgen.get('regen', 0)}% → {tag.get('regen', 0)}%")
                    else:
                        warnungen.append(f"Regenrisiko deutlich gesunken: {morgen.get('regen', 0)}% → {tag.get('regen', 0)}%")
                # Gewitter
                delta_gewitter = tag.get("gewitter", 0) - morgen.get("gewitter", 0)
                if abs(delta_gewitter) >= schwellen["delta_prozent"]:
                    if delta_gewitter > 0:
                        warnungen.append(f"Gewitterrisiko stark gestiegen: {morgen.get('gewitter', 0)}% → {tag.get('gewitter', 0)}%")
                    else:
                        warnungen.append(f"Gewitterrisiko deutlich gesunken: {morgen.get('gewitter', 0)}% → {tag.get('gewitter', 0)}%")
                
                # Gewitterzeit-Verschiebung
                gewitter_ab_morgen = morgen.get("gewitter_ab")
                gewitter_ab_tag = tag.get("gewitter_ab")
                if gewitter_ab_morgen and gewitter_ab_tag:
                    try:
                        zeit_morgen = datetime.datetime.strptime(gewitter_ab_morgen, "%H:%M")
                        zeit_tag = datetime.datetime.strptime(gewitter_ab_tag, "%H:%M")
                        delta_minuten = abs((zeit_tag - zeit_morgen).total_seconds() / 60)
                        if delta_minuten >= 60:  # Wenn sich die Zeit um mehr als 1 Stunde verschiebt
                            if zeit_tag > zeit_morgen:
                                warnungen.append(f"Gewitterwarnung verzögert: {gewitter_ab_morgen} → {gewitter_ab_tag}")
                            else:
                                warnungen.append(f"Gewitterwarnung vorgezogen: {gewitter_ab_morgen} → {gewitter_ab_tag}")
                    except ValueError:
                        logger.warning(f"Ungültiges Zeitformat für Gewitterwarnung: {gewitter_ab_morgen} oder {gewitter_ab_tag}")
                
                # Wind
                delta_wind = tag.get("wind", 0) - morgen.get("wind", 0)
                if abs(delta_wind) >= schwellen["delta_prozent"]:
                    if delta_wind > 0:
                        warnungen.append(f"Wind stark gestiegen: {morgen.get('wind', 0)} km/h → {tag.get('wind', 0)} km/h")
                    else:
                        warnungen.append(f"Wind deutlich abgeflaut: {morgen.get('wind', 0)} km/h → {tag.get('wind', 0)} km/h")
                # Hitze
                delta_hitze = tag.get("hitze", 0) - morgen.get("hitze", 0)
                if abs(delta_hitze) >= schwellen["delta_prozent"]:
                    if delta_hitze > 0:
                        warnungen.append(f"Hitze stark gestiegen: {morgen.get('hitze', 0)}°C → {tag.get('hitze', 0)}°C")
                    else:
                        warnungen.append(f"Temperaturen deutlich gesunken: {morgen.get('hitze', 0)}°C → {tag.get('hitze', 0)}°C")
                if warnungen:
                    return {"wetter": tag}
                else:
                    return {"wetter": {}}  # Leere Ausgabe
        elif args.modus == "abend":
            daten = lade_abend_wetterdaten(config)
        elif args.modus == "morgen":
            daten = lade_morgen_wetterdaten(etappe, config)
        else:
            daten = hole_wetterdaten_fuer_punkte(etappe["punkte"])
        if not isinstance(daten, dict):
            raise DataError("Ungültiges Datenformat: Kein Dictionary")
        if "wetter" not in daten:
            raise DataError("Ungültiges Datenformat: 'wetter' fehlt")
        wetter = daten["wetter"]
        return daten
    except Exception as e:
        logger.error(f"Fehler beim Laden der Wetterdaten: {str(e)}")
        raise DataError(f"Fehler beim Laden der Wetterdaten: {str(e)}")

def wetter_dict_fuer_inreach(wetter: dict, etappe: dict) -> dict:
    """Mappt die Keys des Wetter-Dicts auf die von generiere_kurznachricht erwarteten Namen."""
    # Entferne "GR20" aus dem Etappennamen
    etappenname = etappe.get("name", "").replace("GR20 ", "")
    return {
        "etappenname": etappenname,
        "nachttemperatur": wetter.get("nacht_temp"),
        "hitze": wetter.get("hitze"),
        "regen": wetter.get("regen"),
        "regen_ab": wetter.get("regen_ab"),
        "regen_max_zeit": wetter.get("regen_max_zeit"),
        "wind": wetter.get("wind"),
        "gewitter": wetter.get("gewitter"),
        "gewitter_ab": wetter.get("gewitter_ab"),
        "gewitter_max_zeit": wetter.get("gewitter_max_zeit"),
        "gewitter_plus1": wetter.get("gewitter_plus1"),
        # Pflichtfelder für generiere_kurznachricht:
        "temp": wetter.get("temp", 0),
        "temp_gefuehlt": wetter.get("temp_gefuehlt", 0),
        "wind_geschwindigkeit": wetter.get("wind_geschwindigkeit", 0),
        "wind_richtung": wetter.get("wind_richtung", "")
    }

def generiere_bericht(
    etappe: Dict[str, Any],
    wetter: Dict[str, Any],
    args: argparse.Namespace
) -> Tuple[str, bool]:
    """
    Generiert den Wetterbericht.
    
    Args:
        etappe: Aktuelle Etappe
        wetter: Wetterdaten
        args: Kommandozeilenargumente
        
    Returns:
        Tuple aus (Berichtstext, Erfolg)
    """
    if args.inreach:
        return generiere_kurznachricht(
            wetterdaten=wetter,
            modus=args.modus,
            inreach=args.inreach,
            etappenname=etappe["name"]
        ), True
    elif args.modus == "morgen":
        # Für den Morgenmodus direkt generiere_kurznachricht aufrufen
        return generiere_kurznachricht(
            wetterdaten=wetter,
            modus="morgen",
            inreach=args.inreach,
            etappenname=etappe["name"]
        ), True
    else:
        # Werfen explizit Exception bei fehlenden Keys
        try:
            return generiere_kurznachricht(
                wetterdaten=wetter,
                modus=args.modus,
                inreach=args.inreach,
                etappenname=etappe["name"]
            ), True
        except Exception as e:
            logger.error(f"Fehler beim Generieren des Berichts: {str(e)}")
            raise ReportError(f"Fehler beim Generieren des Wetterberichts: {str(e)}")

def wetterdaten_dict(wetter, etappe, config):
    return {
        "etappe": etappe["name"],
        "regen": wetter.get("regen"),
        "regen_ab": wetter.get("regen_ab"),
        "regen_max_zeit": wetter.get("regen_max_zeit"),
        "wind": wetter.get("wind"),
        "gewitter": wetter.get("gewitter"),
        "gewitter_ab": wetter.get("gewitter_ab"),
        "gewitter_max_zeit": wetter.get("gewitter_max_zeit"),
        "gewitter_plus1": wetter.get("gewitter_plus1"),
        "regen_schwelle": config["schwellen"]["regen"],
        "gewitter_schwelle": config["schwellen"]["gewitter"]
    }

def sende_bericht(bericht: str, args: argparse.Namespace, config: dict) -> bool:
    """
    Sendet den Bericht per E-Mail.
    """
    try:
        logger.info("Versuche, den Bericht per E-Mail zu versenden...")
        smtp_config = config['smtp']
        sende_email(bericht, smtp_config)
        logger.info("Bericht erfolgreich per E-Mail versendet.")
        return True
    except EmailError as e:
        logger.error(f"Fehler beim E-Mail-Versand: {str(e)}")
        return False

def main() -> None:
    """Hauptfunktion des WeatherBots."""
    try:
        # Logging einrichten
        setup_logging()
        
        # Argumente parsen
        args = parse_args()
        logger.info(f"Starte WeatherBot im Modus: {args.modus}")
        
        # Konfiguration laden
        config = lade_konfiguration()
        
        # Heutige Etappe laden
        etappe = lade_heutige_etappe(config)
        if not etappe:
            logger.error("Konnte heutige Etappe nicht laden")
            sys.exit(1)
            
        # Wetterdaten laden
        wetter = lade_daten(args, etappe, config)
        if not wetter:
            logger.error("Konnte Wetterdaten nicht laden")
            sys.exit(1)
            
        # Bericht generieren
        bericht, ist_warnung = generiere_bericht(etappe, wetter, args)
        if not bericht:
            logger.error("Konnte Bericht nicht generieren")
            sys.exit(1)
            
        # Bericht senden
        if not args.dry_run:
            if not sende_bericht(bericht, args, config):
                logger.error("Konnte Bericht nicht senden")
                sys.exit(1)
            logger.info("Bericht erfolgreich gesendet")
        else:
            logger.info("Dry Run - Bericht wird nicht gesendet")
            print("\n--- Wetterbericht (Dry Run) ---")
            print(bericht)
            
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()