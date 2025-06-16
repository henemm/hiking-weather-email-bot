from typing import Dict, Any, Optional
from datetime import datetime
import requests
import logging
from .config import ConfigError

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
    """Holt Wetterdaten von der API."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,windspeed_10m,winddirection_10m,precipitation,thunderstorm",
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
            
        return {
            'temp': hourly.get('temperature_2m', 0),
            'temp_gefuehlt': hourly.get('apparent_temperature', 0),
            'wind_geschwindigkeit': hourly.get('windspeed_10m', 0),
            'wind_richtung': windrichtung_zu_text(hourly.get('winddirection_10m', 0)),
            'regen': hourly.get('precipitation', 0),
            'gewitter': hourly.get('thunderstorm', False),
            'regen_zeit': hourly.get('precipitation_time'),
            'gewitter_zeit': hourly.get('thunderstorm_time')
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