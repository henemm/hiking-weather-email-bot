#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import sys
import traceback
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import os
from dotenv import load_dotenv
import datetime
import requests
from wetter import wetterdaten, kurztext, config
from emailversand import sende_email, EmailError

from config import config, ConfigError
from etappen import lade_heutige_etappe, lade_etappen
from wetter.fetch import hole_wetterdaten, fetch_weather_data
from wetter.analyse import generiere_wetterbericht
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

def lade_konfiguration():
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

def lade_etappen():
    """Lädt die Etappendaten aus der YAML-Datei."""
    try:
        with open('etappen.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("Etappendatei etappen.yaml nicht gefunden")
        return None
    except yaml.YAMLError:
        logger.error("Ungültiges YAML-Format in etappen.yaml")
        return None
    except Exception as e:
        logger.error(f"Fehler beim Laden der Etappendaten: {str(e)}")
        return None

def hole_wetterdaten(ort, api_key):
    """Holt die Wetterdaten von der OpenWeatherMap API."""
    try:
        return wetterdaten.hole_wetterdaten(ort, api_key)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Wetterdaten: {str(e)}")
        return None

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

def sende_email(empfaenger, betreff, nachricht, smtp_server, smtp_port, benutzername, passwort):
    """Sendet die E-Mail mit dem Wetterbericht."""
    try:
        email_sender.sende_email(
            empfaenger=empfaenger,
            betreff=betreff,
            nachricht=nachricht,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            benutzername=benutzername,
            passwort=passwort
        )
        return True
    except Exception as e:
        logger.error(f"Fehler beim Senden der E-Mail: {str(e)}")
        return False

def sende_inreach_nachricht(nachricht, inreach_email, smtp_server, smtp_port, benutzername, passwort):
    """Sendet die InReach-Nachricht."""
    try:
        email_sender.sende_email(
            empfaenger=inreach_email,
            betreff="",  # Leerer Betreff für InReach
            nachricht=nachricht,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            benutzername=benutzername,
            passwort=passwort
        )
        return True
    except Exception as e:
        logger.error(f"Fehler beim Senden der InReach-Nachricht: {str(e)}")
        return False

def lade_abend_wetterdaten(config):
    etappen = lade_etappen()
    startdatum = config["startdatum"]
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
    
    # Morgige Etappe (E2)
    if differenz + 1 >= len(etappen):
        raise ValueError("Keine morgige Etappe mehr vorhanden.")
    etappe_morgen = etappen[differenz + 1]
    punkte_morgen = etappe_morgen["punkte"]
    morgen = heute + datetime.timedelta(days=1)
    alle_daten_morgen = []
    for punkt in punkte_morgen:
        daten = fetch_weather_data(punkt["lat"], punkt["lon"], morgen)
        alle_daten_morgen.append(daten)
    
    # Übernächste Etappe (E3)
    daten_uebermorgen = None
    if differenz + 2 < len(etappen):
        etappe_uebermorgen = etappen[differenz + 2]
        punkte_uebermorgen = etappe_uebermorgen["punkte"]
        uebermorgen = heute + datetime.timedelta(days=2)
        alle_daten_uebermorgen = []
        for punkt in punkte_uebermorgen:
            daten = fetch_weather_data(punkt["lat"], punkt["lon"], uebermorgen)
            alle_daten_uebermorgen.append(daten)
        # Aggregation für E3 Gewitter
        gewitter_values_e3 = [max(d["hourly"]["thunderstorm_probability"]) for d in alle_daten_uebermorgen if d["hourly"]["thunderstorm_probability"] and all(x is not None for x in d["hourly"]["thunderstorm_probability"])]
        gewitter_e3 = max(gewitter_values_e3) if gewitter_values_e3 else 0
        daten_uebermorgen = {"gewitter_plus1": gewitter_e3}
    else:
        daten_uebermorgen = {"gewitter_plus1": None}
    
    # Aggregation für E2 Tageswerte
    hitze_values = [d["daily"]["apparent_temperature_max"][0] for d in alle_daten_morgen if d["daily"]["apparent_temperature_max"][0] is not None]
    regen_values = [d["daily"]["precipitation_probability_max"][0] for d in alle_daten_morgen if d["daily"]["precipitation_probability_max"][0] is not None]
    wind_values = [d["daily"]["wind_speed_10m_max"][0] for d in alle_daten_morgen if d["daily"]["wind_speed_10m_max"][0] is not None]
    gewitter_values = [max(d["hourly"]["thunderstorm_probability"]) for d in alle_daten_morgen if d["hourly"]["thunderstorm_probability"] and all(x is not None for x in d["hourly"]["thunderstorm_probability"])]
    
    # Schwellenwerte aus config
    regen_schwelle = config["schwellen"]["regen"]
    gewitter_schwelle = config["schwellen"]["gewitter"]
    
    # Frühester Zeitpunkt, an dem Schwellenwert überschritten wird (über alle Punkte)
    regen_ab_candidates = []
    gewitter_ab_candidates = []
    regen_max_zeit_candidates = []
    for d in alle_daten_morgen:
        times = d["hourly"]["time"]
        regen_vals = d["hourly"]["precipitation_probability"]
        gewitter_vals = d["hourly"]["thunderstorm_probability"]
        # Regen
        for t, v in zip(times, regen_vals):
            if v is not None and v >= regen_schwelle:
                regen_ab_candidates.append(t)
                break
        # Zeitpunkt des maximalen Regenrisikos
        if regen_vals:
            max_regen_idx = regen_vals.index(max(regen_vals))
            regen_max_zeit_candidates.append(times[max_regen_idx])
        # Gewitter
        for t, v in zip(times, gewitter_vals):
            if v is not None and v >= gewitter_schwelle:
                gewitter_ab_candidates.append(t)
                break
    
    regen_ab = min(regen_ab_candidates) if regen_ab_candidates else None
    gewitter_ab = min(gewitter_ab_candidates) if gewitter_ab_candidates else None
    regen_max_zeit = min(regen_max_zeit_candidates) if regen_max_zeit_candidates else None
    
    # Setze Defaults, wenn keine Werte vorhanden sind
    hitze = max(hitze_values) if hitze_values else 0
    regen = max(regen_values) if regen_values else 0
    wind = max(wind_values) if wind_values else 0
    gewitter = max(gewitter_values) if gewitter_values else 0
    
    return {
        "wetter": {
            "nacht_temp": nacht_temp,
            "hitze": hitze,
            "regen": regen,
            "wind": wind,
            "gewitter": gewitter,
            "regen_ab": regen_ab,
            "gewitter_ab": gewitter_ab,
            "regen_max_zeit": regen_max_zeit,
            "gewitter_plus1": daten_uebermorgen["gewitter_plus1"]
        }
    }

def lade_morgen_wetterdaten(etappe: Dict[str, Any]) -> Dict[str, Any]:
    """Lade Wetterdaten für den Morgenbericht."""
    wetterdaten = hole_wetterdaten(etappe["punkte"], config["api_key"])
    wetter = wetterdaten["wetter"]

    # Gewittervorhersage für den nächsten Tag (analog zu lade_abend_wetterdaten)
    etappen = lade_etappen()
    heute = datetime.date.today()
    # Finde Index der aktuellen Etappe
    idx = None
    for i, e in enumerate(etappen):
        if e["name"] == etappe["name"]:
            idx = i
            break
    if idx is not None and idx + 1 < len(etappen):
        etappe_morgen = etappen[idx + 1]
        punkte_morgen = etappe_morgen["punkte"]
        morgen = heute + datetime.timedelta(days=1)
        alle_daten_morgen = []
        for punkt in punkte_morgen:
            daten = fetch_weather_data(punkt["lat"], punkt["lon"], morgen)
            alle_daten_morgen.append(daten)
        gewitter_values_plus1 = [max(d["hourly"]["thunderstorm_probability"]) for d in alle_daten_morgen if d["hourly"]["thunderstorm_probability"] and all(x is not None for x in d["hourly"]["thunderstorm_probability"])]
        gewitter_plus1 = max(gewitter_values_plus1) if gewitter_values_plus1 else 0
    else:
        gewitter_plus1 = None

    return {
        "etappe": etappe["name"],
        "regen": wetter.get("regen"),
        "regen_ab": wetter.get("regen_ab"),
        "regen_max_zeit": wetter.get("regen_max_zeit"),
        "wind": wetter.get("wind"),
        "gewitter": wetter.get("gewitter"),
        "gewitter_ab": wetter.get("gewitter_ab"),
        "gewitter_max_zeit": wetter.get("gewitter_max_zeit"),
        "gewitter_plus1": gewitter_plus1,
        "regen_schwelle": config["schwellen"]["regen"],
        "gewitter_schwelle": config["schwellen"]["gewitter"]
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
            daten = lade_morgen_wetterdaten(etappe)
        else:
            daten = hole_wetterdaten(etappe["punkte"], config["api_key"])
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
        "gewitter_plus1": wetter.get("gewitter_plus1")
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
    try:
        if args.inreach:
            return generiere_kurznachricht(wetter_dict_fuer_inreach(wetter, etappe)), True
        else:
            return generiere_wetterbericht(
                wetter["nacht_temp"],
                wetter["hitze"],
                wetter["regen"],
                wetter["wind"],
                wetter["gewitter"],
                wetter.get("regen_ab"),
                wetter.get("gewitter_ab"),
                wetter.get("regen_max_zeit"),
                wetter.get("gewitter_max_zeit"),
                etappe.get("name")
            ), True
    except Exception as e:
        logger.error(f"Fehler beim Generieren des Berichts: {str(e)}")
        return f"Fehler beim Generieren des Wetterberichts: {str(e)}", False

def sende_bericht(bericht: str, args: argparse.Namespace) -> bool:
    """
    Sendet den Bericht per E-Mail.
    """
    try:
        logger.info("Versuche, den Bericht per E-Mail zu versenden...")
        sende_email(bericht)
        logger.info("Bericht erfolgreich per E-Mail versendet.")
        return True
    except EmailError as e:
        logger.error(f"Fehler beim E-Mail-Versand: {str(e)}")
        return False

def main() -> None:
    """Hauptfunktion"""
    setup_logging()
    
    try:
        args = parse_args()
        logger.info(f"Starte WeatherBot im Modus: {args.modus}")
        
        # Etappe laden
        try:
            etappe = lade_heutige_etappe(config)
            logger.info(f"Etappe geladen: {etappe['name']}")
        except ValueError as e:
            logger.error(f"Fehler beim Laden der Etappe: {str(e)}")
            return

        # Wetterdaten laden
        try:
            daten = lade_daten(args, etappe, config)
            wetter = daten["wetter"]
            logger.info("Wetterdaten erfolgreich geladen")
        except DataError as e:
            logger.error(f"Fehler beim Laden der Wetterdaten: {str(e)}")
            return

        # Wetterbericht generieren
        bericht, success = generiere_bericht(etappe, wetter, args)
        if not success:
            return

        # Ausgabe und ggf. Versand
        print(bericht)
        if not args.dry_run:
            try:
                sende_bericht(bericht, args)
            except Exception as e:
                logger.error(f"Fehler beim Versenden des Berichts: {str(e)}")
                return

    except ConfigError as e:
        logger.error(f"Konfigurationsfehler: {str(e)}")
        return
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        logger.error(traceback.format_exc())
        return

if __name__ == "__main__":
    main()