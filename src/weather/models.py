from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class ReportMode(Enum):
    """Modus der Wetterberichterstattung"""
    EVENING = "evening"  # Abendbericht
    MORNING = "morning"  # Morgenbericht
    DAY = "day"         # Tageswarnung

@dataclass
class WeatherPoint:
    """Ein einzelner Wettermesspunkt"""
    latitude: float
    longitude: float
    elevation: float
    time: datetime
    temperature: float
    feels_like: float
    precipitation: float
    thunderstorm_probability: Optional[float]
    wind_speed: float
    wind_direction: float
    cloud_cover: float
    rain_probability: Optional[float] = None  # Neue Feld für Regenwahrscheinlichkeit

@dataclass
class WeatherData:
    """Wetterdaten für einen Zeitraum"""
    points: List[WeatherPoint]
    rain_time_threshold: Optional[str] = None
    rain_time_max: Optional[str] = None
    thunder_time_threshold: Optional[str] = None
    thunder_time_max: Optional[str] = None
    
    def get_last_point(self) -> Optional[WeatherPoint]:
        """Gibt den letzten Messpunkt zurück"""
        return self.points[-1] if self.points else None
    
    def get_max_values(self) -> Dict[str, float]:
        """Berechnet die Maximalwerte über alle Punkte"""
        if not self.points:
            return {}
        return {
            "temperature": max((p.temperature for p in self.points), default=0),
            "feels_like": max((p.feels_like for p in self.points), default=0),
            "precipitation": max((p.precipitation for p in self.points), default=0),
            "thunderstorm_probability": max(((p.thunderstorm_probability or 0) for p in self.points), default=0),
            "wind_speed": max((p.wind_speed for p in self.points), default=0),
            "cloud_cover": max((p.cloud_cover for p in self.points), default=0)
        }

    def get_min_values(self) -> Dict[str, float]:
        """Berechnet die Minimalwerte über alle Punkte"""
        if not self.points:
            return {}
        return {
            "temperature": min((p.temperature for p in self.points), default=0),
            "feels_like": min((p.feels_like for p in self.points), default=0),
            "precipitation": min((p.precipitation for p in self.points), default=0),
            "thunderstorm_probability": min(((p.thunderstorm_probability or 0) for p in self.points), default=0),
            "wind_speed": min((p.wind_speed for p in self.points), default=0),
            "cloud_cover": min((p.cloud_cover for p in self.points), default=0)
        }

@dataclass
class StageWeather:
    """Wetterdaten für eine Etappe"""
    today: WeatherData
    tomorrow: Optional[WeatherData] = None
    day_after_tomorrow: Optional[WeatherData] = None

@dataclass
class WeatherReport:
    """Generierter Wetterbericht"""
    mode: ReportMode
    stage_name: str
    date: datetime
    night_temperature: Optional[float]  # Nur für Abendbericht
    max_temperature: float
    max_feels_like: float
    max_precipitation: float
    max_thunderstorm_probability: Optional[float]
    max_wind_speed: float
    max_cloud_cover: float
    next_day_thunderstorm: Optional[float]  # Gewitter +1
    text: str  # Der generierte Berichtstext
    max_precipitation_probability: Optional[float] = None  # Regenwahrscheinlichkeit
    thunderstorm_plus1: Optional[float] = None  # Gewitter +2 (übernächster Tag)
    # Neue Felder für Zeitpunkte
    rain_time_threshold: Optional[str] = None
    rain_time_max: Optional[str] = None
    thunder_time_threshold: Optional[str] = None
    thunder_time_max: Optional[str] = None 