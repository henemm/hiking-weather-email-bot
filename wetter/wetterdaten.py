from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests
import logging
from .config import ConfigError
from src.weather.api import WeatherAPIClient
from src.weather.adapter import convert_to_legacy_format

logger = logging.getLogger(__name__)

class WeatherDataError(Exception):
    """Basis-Exception für Wetterdaten-Fehler"""
    pass

class APIError(WeatherDataError):
    """Fehler bei der API-Kommunikation"""
    pass

class DataProcessingError(WeatherDataError):
    """Fehler bei der Verarbeitung der API-Antwort"""
    pass

def windrichtung_zu_text(grad: float) -> str:
    """
    Konvertiert Windrichtung in Grad zu Himmelsrichtung.
    
    Args:
        grad: Windrichtung in Grad (0-360)
        
    Returns:
        Himmelsrichtung als Text (N, NO, O, SO, S, SW, W, NW)
        
    Raises:
        ValueError: Bei ungültiger Windrichtung
    """
    if not 0 <= grad <= 360:
        raise ValueError("Windrichtung muss zwischen 0 und 360 Grad liegen")
    
    # Normalisiere 360 auf 0
    if grad == 360:
        grad = 0
        
    if 337.5 <= grad < 360 or 0 <= grad < 22.5:
        return "N"
    elif 22.5 <= grad < 67.5:
        return "NO"
    elif 67.5 <= grad < 112.5:
        return "O"
    elif 112.5 <= grad < 157.5:
        return "SO"
    elif 157.5 <= grad < 202.5:
        return "S"
    elif 202.5 <= grad < 247.5:
        return "SW"
    elif 247.5 <= grad < 292.5:
        return "W"
    elif 292.5 <= grad < 337.5:
        return "NW"
    else:
        return "Unbekannt"

def hole_wetterdaten(lat: float, lon: float, config: Optional[dict] = None) -> Dict[str, Any]:
    """Holt Wetterdaten von der Open-Meteo API."""
    # Explizite Prüfung auf ungültige Koordinaten
    if lat is None or lon is None or (lat == 0.0 and lon == 0.0):
        raise ValueError("Ungültige Koordinaten für Wetterdatenabruf")
    # Gültigkeitsprüfung für Breite und Länge
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise ValueError("Koordinaten außerhalb des gültigen Bereichs")
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability,wind_speed_10m,wind_gusts_10m,thunderstorm_probability",
        "daily": "temperature_2m_min,temperature_2m_max,apparent_temperature_max,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max",
        "timezone": "auto",
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, dict) or 'hourly' not in data:
            raise DataProcessingError("Ungültiges Antwortformat von der API")
        hourly = data['hourly']
        if not isinstance(hourly, dict) or 'time' not in hourly:
            raise DataProcessingError("Ungültiges Antwortformat von der API")
            
        # Hilfsfunktionen für sichere Aggregation
        def safe_max(lst, default=None):
            return max(lst) if lst and isinstance(lst, list) else default
        def safe_min(lst, default=None):
            return min(lst) if lst and isinstance(lst, list) else default
        def first_positive_time(values, times):
            if not values or not times:
                return None
            for v, t in zip(values, times):
                if v > 0:
                    return t
            return None

        # Schwellenwerte aus der Konfiguration holen (mit Fallbacks)
        schwelle_regen = 20  # Default, falls nicht in config
        schwelle_gewitter = 30  # Default, falls nicht in config
        if config and 'Schwellen' in config:
            schwelle_regen = config['Schwellen'].get('regen', schwelle_regen)
            schwelle_gewitter = config['Schwellen'].get('gewitter', schwelle_gewitter)

        # Modus auslesen
        modus = config.get('modus') if config else None
        if modus == 'abend':
            index_tageswert = 1  # morgen
            index_gewitter_plus1 = 2  # übermorgen
        else:
            index_tageswert = 0  # heute
            index_gewitter_plus1 = 1  # morgen

        def first_time_over_threshold(values, times, threshold):
            if not values or not times:
                return None
            for v, t in zip(values, times):
                if v is not None and v >= threshold:
                    return t
            return None

        def time_of_max(values, times):
            if not values or not times:
                return None
            # Filtere None-Werte heraus
            filtered = [(i, v) for i, v in enumerate(values) if v is not None]
            if not filtered:
                return None
            max_idx = max(filtered, key=lambda x: x[1])[0]
            return times[max_idx] if 0 <= max_idx < len(times) else None

        daily = data.get('daily', {})
        hourly = data.get('hourly', {})
        times = hourly.get('time', [])
        regen_vals = hourly.get('precipitation_probability', [])
        gewitter_vals = hourly.get('thunderstorm_probability', [])

        # Für Tageswerte: Nur das relevante Element (heute/morgen) für jeden Punkt, dann Maximum über alle Punkte
        hitze = safe_max([daily.get('apparent_temperature_max', [])[index_tageswert] if daily.get('apparent_temperature_max') and len(daily.get('apparent_temperature_max')) > index_tageswert else None])
        regen = safe_max([daily.get('precipitation_probability_max', [])[index_tageswert] if daily.get('precipitation_probability_max') and len(daily.get('precipitation_probability_max')) > index_tageswert else None])
        wind = safe_max([daily.get('wind_speed_10m_max', [])[index_tageswert] if daily.get('wind_speed_10m_max') and len(daily.get('wind_speed_10m_max')) > index_tageswert else None])
        gewitter = safe_max([daily.get('thunderstorm_probability_max', [])[index_tageswert] if daily.get('thunderstorm_probability_max') and len(daily.get('thunderstorm_probability_max')) > index_tageswert else None])

        # Gewitter +1
        gewitter_plus1 = safe_max([daily.get('thunderstorm_probability_max', [])[index_gewitter_plus1] if daily.get('thunderstorm_probability_max') and len(daily.get('thunderstorm_probability_max')) > index_gewitter_plus1 else None])

        # Nachttemperatur: Nur der letzte Punkt der Etappe (Schlafplatz), immer [0] (heute)
        # Nutze apparent_temperature_min, falls vorhanden, sonst temperature_2m_min
        if 'apparent_temperature_min' in daily and daily['apparent_temperature_min']:
            nacht_temp = safe_min([daily['apparent_temperature_min'][0]])
        elif 'temperature_2m_min' in daily and daily['temperature_2m_min']:
            nacht_temp = safe_min([daily['temperature_2m_min'][0]])
        else:
            nacht_temp = None

        # Rückgabe ist ein flaches Dictionary mit allen Keys auf oberster Ebene
        return {
            'nacht_temp': nacht_temp,
            'hitze': hitze,
            'regen': regen,
            'wind': wind,
            'gewitter': gewitter,
            'regen_ab': first_time_over_threshold(regen_vals, times, schwelle_regen),
            'gewitter_ab': first_time_over_threshold(gewitter_vals, times, schwelle_gewitter),
            'regen_max_zeit': time_of_max(regen_vals, times),
            'gewitter_max_zeit': time_of_max(gewitter_vals, times),
            'gewitter_plus1': gewitter_plus1,
            'max_feels_like': safe_max(daily.get('apparent_temperature_max', [])),
        }
    except requests.RequestException as e:
        logger.error(f"API-Fehler: {str(e)}")
        raise APIError(f"API-Fehler: {str(e)}")
    except (KeyError, ValueError) as e:
        logger.error(f"Ungültiges Antwortformat von der API: {str(e)}")
        raise DataProcessingError(f"Ungültiges Antwortformat von der API: {str(e)}")
    except Exception as e:
        if isinstance(e, (APIError, DataProcessingError)):
            raise
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        raise WeatherDataError(f"Unerwarteter Fehler: {str(e)}") 