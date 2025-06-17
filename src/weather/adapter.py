from typing import Dict, Any
from src.weather.models import WeatherData, WeatherPoint

def convert_to_legacy_format(weather_data: WeatherData) -> Dict[str, Any]:
    """
    Konvertiert die neuen Datenmodelle in das alte Format.
    
    Args:
        weather_data: WeatherData-Objekt
        
    Returns:
        Dictionary im alten Format
    """
    if not weather_data.points:
        return {
            'temp': 0,
            'temp_gefuehlt': 0,
            'wind_geschwindigkeit': 0,
            'wind_richtung': 'N',
            'regen': 0,
            'gewitter': 0,
            'regen_zeit': '',
            'gewitter_zeit': ''
        }
    
    # Nehme den letzten Punkt für aktuelle Werte
    last_point = weather_data.points[-1]
    
    # Berechne Maximalwerte
    max_values = weather_data.get_max_values()
    
    return {
        'temp': last_point.temperature,
        'temp_gefuehlt': last_point.feels_like,
        'wind_geschwindigkeit': last_point.wind_speed,
        'wind_richtung': _convert_wind_direction(last_point.wind_direction),
        'regen': last_point.precipitation,
        'gewitter': last_point.thunderstorm_probability or 0,
        'regen_zeit': last_point.time.isoformat(),
        'gewitter_zeit': last_point.time.isoformat()
    }

def _convert_wind_direction(degrees: float) -> str:
    """Konvertiert Windrichtung in Grad zu Himmelsrichtung"""
    directions = ['N', 'NO', 'O', 'SO', 'S', 'SW', 'W', 'NW']
    index = round(degrees / 45) % 8
    return directions[index] 