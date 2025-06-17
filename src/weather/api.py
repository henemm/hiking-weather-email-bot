import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.weather.models import WeatherPoint, WeatherData

logger = logging.getLogger(__name__)

class WeatherAPIError(Exception):
    """Basis-Exception für API-Fehler"""
    pass

class WeatherAPIRequestError(WeatherAPIError):
    """Fehler bei der API-Anfrage"""
    pass

class WeatherAPIParseError(WeatherAPIError):
    """Fehler beim Parsen der API-Antwort"""
    pass

class WeatherAPIClient:
    """Client für die Open-Meteo API"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt eine API-Anfrage durch.
        
        Args:
            params: API-Parameter
            
        Returns:
            API-Antwort als Dictionary
            
        Raises:
            WeatherAPIRequestError: Bei Fehlern der API-Anfrage
        """
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise WeatherAPIRequestError(f"API-Anfrage fehlgeschlagen: {str(e)}")
        except ValueError as e:
            raise WeatherAPIParseError(f"Ungültige API-Antwort: {str(e)}")
    
    def _parse_weather_point(
        self,
        time: str,
        latitude: float,
        longitude: float,
        elevation: float,
        data: Dict[str, Any]
    ) -> WeatherPoint:
        """
        Parst einen einzelnen Wettermesspunkt aus der API-Antwort.
        
        Args:
            time: Zeitstempel
            latitude: Breitengrad
            longitude: Längengrad
            elevation: Höhe
            data: Wetterdaten
            
        Returns:
            WeatherPoint-Objekt
            
        Raises:
            WeatherAPIParseError: Bei fehlenden oder ungültigen Daten
        """
        try:
            return WeatherPoint(
                latitude=latitude,
                longitude=longitude,
                elevation=elevation,
                time=datetime.fromisoformat(time.replace("Z", "+00:00")),
                temperature=data["temperature_2m"],
                feels_like=data["apparent_temperature"],
                precipitation=data["precipitation"],
                thunderstorm_probability=data.get("thunderstorm_probability"),
                wind_speed=data["windspeed_10m"],
                wind_direction=data["winddirection_10m"],
                cloud_cover=data["cloudcover"]
            )
        except (KeyError, ValueError) as e:
            raise WeatherAPIParseError(f"Fehler beim Parsen der Wetterdaten: {str(e)}")
    
    def get_weather(
        self,
        latitude: float,
        longitude: float,
        elevation: float,
        start_date: datetime,
        end_date: datetime
    ) -> WeatherData:
        """
        Holt Wetterdaten für einen Zeitraum.
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
            elevation: Höhe
            start_date: Startdatum
            end_date: Enddatum
            
        Returns:
            WeatherData-Objekt
            
        Raises:
            WeatherAPIError: Bei API-Fehlern
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation,
            "hourly": [
                "temperature_2m",
                "apparent_temperature",
                "precipitation",
                "thunderstorm_probability",
                "windspeed_10m",
                "winddirection_10m",
                "cloudcover"
            ],
            "timezone": "auto",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        
        try:
            response = self._make_request(params)
            hourly = response["hourly"]
            
            points = []
            for i in range(len(hourly["time"])):
                point_data = {
                    key: hourly[key][i]
                    for key in hourly.keys()
                    if key != "time"
                }
                points.append(self._parse_weather_point(
                    hourly["time"][i],
                    latitude,
                    longitude,
                    elevation,
                    point_data
                ))
            
            return WeatherData(points=points)
            
        except (KeyError, IndexError) as e:
            raise WeatherAPIParseError(f"Unerwartetes API-Antwortformat: {str(e)}") 