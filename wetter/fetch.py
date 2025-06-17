import json
import logging
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from src.config import config

logger = logging.getLogger(__name__)


class WeatherAPIError(Exception):
    """Basis-Exception für Wetter-API-Fehler"""

    pass


class WeatherAPIRateLimitError(WeatherAPIError):
    """Rate Limit überschritten"""

    pass


class WeatherAPIResponseError(WeatherAPIError):
    """Ungültige API-Antwort"""

    pass


class WeatherAPIConnectionError(WeatherAPIError):
    """Verbindungsfehler zur API"""

    pass


def get_cache_path() -> Path:
    """Gibt den Pfad zum Cache-Verzeichnis zurück"""
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cached_data(location: Dict[str, float], date: date) -> Optional[Dict[str, Any]]:
    """
    Versucht, Daten aus dem Cache zu laden.

    Args:
        location: Dictionary mit lat/lon
        date: Das Zieldatum

    Returns:
        Gecachte Daten oder None
    """
    cache_file = (
        get_cache_path()
        / f"weather_{location['lat']}_{location['lon']}_{date.isoformat()}.json"
    )

    if not cache_file.exists():
        return None

    try:
        # Prüfe ob Cache noch gültig ist (max. 1 Stunde alt)
        if time.time() - cache_file.stat().st_mtime > 3600:
            cache_file.unlink()
            return None

        with cache_file.open("r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Fehler beim Lesen des Cache: {str(e)}")
        return None


def save_to_cache(location: Dict[str, float], date: date, data: Dict[str, Any]) -> None:
    """
    Speichert Daten im Cache.

    Args:
        location: Dictionary mit lat/lon
        date: Das Zieldatum
        data: Die zu cachenden Daten
    """
    try:
        cache_file = (
            get_cache_path()
            / f"weather_{location['lat']}_{location['lon']}_{date.isoformat()}.json"
        )
        with cache_file.open("w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Fehler beim Schreiben des Cache: {str(e)}")


def find_threshold_crossing(
    times: List[str], values: List[float], threshold: float, start_hour: int = 0
) -> Optional[Tuple[str, float]]:
    """
    Findet den ersten Zeitpunkt, an dem ein Wert über einen Schwellenwert steigt.

    Args:
        times: Liste von Zeitstempeln
        values: Liste von Werten
        threshold: Schwellenwert
        start_hour: Stunde, ab der gesucht werden soll

    Returns:
        Tuple aus (Zeitstempel, Wert) oder None
    """
    for time_str, value in zip(times, values):
        hour = datetime.fromisoformat(time_str).hour
        if hour >= start_hour and value >= threshold:
            return time_str, value
    return None


def fetch_weather_data(
    lat: float,
    lon: float,
    datum: date,
    modus: str = "tag",
) -> Dict[str, Any]:
    """Holt Wetterdaten von der Open-Meteo API."""
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": str(lat),
        "longitude": str(lon),
        "start_date": datum.isoformat(),
        "end_date": datum.isoformat(),
        "timezone": "auto",
        "daily": "temperature_2m_min,temperature_2m_max,apparent_temperature_max,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max",
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability,wind_speed_10m,wind_gusts_10m,thunderstorm_probability",
    }
    max_retries = 3
    retry_delay = 1  # Sekunden
    for attempt in range(max_retries):
        try:
            response = requests.get(base_url, params=params)
            if response.status_code == 429:
                raise WeatherAPIRateLimitError("Rate Limit überschritten")
            response.raise_for_status()
            data = response.json()
            if (
                not isinstance(data, dict)
                or "daily" not in data
                or "hourly" not in data
            ):
                raise WeatherAPIResponseError("Ungültiges API-Antwortformat")
            logger.info(f"API-Antwort: {data}")
            return data
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise WeatherAPIConnectionError(f"API-Aufruf fehlgeschlagen: {str(e)}")
            time.sleep(retry_delay * (2**attempt))
    raise WeatherAPIConnectionError("API-Aufruf fehlgeschlagen nach mehreren Versuchen")


def hole_wetterdaten(punkte: List[Dict[str, float]], modus: str = "tag") -> Dict[str, Any]:
    """Holt Wetterdaten für mehrere Punkte und aggregiert sie."""
    heute = date.today()
    alle_daten = []
    for punkt in punkte:
        try:
            daten = fetch_weather_data(punkt["lat"], punkt["lon"], heute, modus)
            alle_daten.append(daten)
        except WeatherAPIError as e:
            # API-Fehler direkt weiterleiten
            raise
        except Exception as e:
            msg = (
                f"Fehler beim Abrufen der Daten für "
                f"Punkt {punkt['lat']},{punkt['lon']}: {str(e)}"
            )
            logger.warning(msg)
    if not alle_daten:
        raise ValueError("Keine Wetterdaten verfügbar")
    # Aggregiere Werte, ignoriere None und setze Defaults
    if modus == "abend":
        # Nachttemperatur: Nur der letzte Punkt der heutigen Etappe (Schlafplatz) zählt!
        letzter_punkt = alle_daten[-1] if alle_daten else None
        nacht_temp = None
        if letzter_punkt and 'daily' in letzter_punkt:
            daily = letzter_punkt['daily']
            if 'apparent_temperature_min' in daily and daily['apparent_temperature_min']:
                nacht_temp = daily['apparent_temperature_min'][0]
            elif 'temperature_2m_min' in daily and daily['temperature_2m_min']:
                nacht_temp = daily['temperature_2m_min'][0]
            else:
                nacht_temp = None
    else:
        nacht_temp = None
    hitze_values = [d["daily"]["apparent_temperature_max"][0] for d in alle_daten if d["daily"]["apparent_temperature_max"][0] is not None]
    regen_values = [d["daily"]["precipitation_probability_max"][0] for d in alle_daten if d["daily"]["precipitation_probability_max"][0] is not None]
    wind_values = [d["daily"]["wind_speed_10m_max"][0] for d in alle_daten if d["daily"]["wind_speed_10m_max"][0] is not None]
    gewitter_values = [max(d["hourly"]["thunderstorm_probability"]) for d in alle_daten if d["hourly"]["thunderstorm_probability"] and all(x is not None for x in d["hourly"]["thunderstorm_probability"])]
    # Schwellenwerte aus config
    regen_schwelle = config["schwellen"]["regen"]
    gewitter_schwelle = config["schwellen"]["gewitter"]
    # Frühester Zeitpunkt, an dem überhaupt Regen/Gewitter möglich ist (über alle Punkte)
    regen_ab_candidates = []
    gewitter_ab_candidates = []
    for d in alle_daten:
        times = d["hourly"]["time"]
        regen_vals = d["hourly"]["precipitation_probability"]
        gewitter_vals = d["hourly"]["thunderstorm_probability"]
        # Regen: erste Stunde mit >0%
        for t, v in zip(times, regen_vals):
            if v is not None and v > 0:
                regen_ab_candidates.append(t)
                break
        # Gewitter: erste Stunde mit >0%
        for t, v in zip(times, gewitter_vals):
            if v is not None and v > 0:
                gewitter_ab_candidates.append(t)
                break
    regen_ab = min(regen_ab_candidates) if regen_ab_candidates else None
    gewitter_ab = min(gewitter_ab_candidates) if gewitter_ab_candidates else None
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
        }
    }
