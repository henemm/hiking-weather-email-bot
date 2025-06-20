from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.weather.models import (
    WeatherData,
    StageWeather,
    WeatherReport,
    ReportMode,
    WeatherPoint
)

class WeatherAggregator:
    """Aggregiert Wetterdaten nach den spezifizierten Regeln"""
    
    def __init__(self, thresholds: Dict[str, float]):
        """
        Initialisiert den Aggregator.
        
        Args:
            thresholds: Dictionary mit Schwellenwerten
        """
        self.thresholds = thresholds
    
    def _get_night_temperature(self, data: WeatherData) -> Optional[float]:
        """
        Holt die Nachttemperatur vom letzten Punkt.
        
        Args:
            data: Wetterdaten
            
        Returns:
            Nachttemperatur oder None
        """
        last_point = data.get_last_point()
        return last_point.temperature if last_point else None
    
    def _get_max_values(self, data: WeatherData) -> Dict[str, float]:
        """
        Berechnet die Maximalwerte über alle Punkte.
        
        Args:
            data: Wetterdaten
            
        Returns:
            Dictionary mit Maximalwerten
        """
        return data.get_max_values()
    
    def _get_next_day_thunderstorm(self, data: Optional[WeatherData]) -> Optional[float]:
        """
        Holt die Gewitterwahrscheinlichkeit für den nächsten Tag.
        
        Args:
            data: Wetterdaten für den nächsten Tag
            
        Returns:
            Maximale Gewitterwahrscheinlichkeit oder None
        """
        if not data:
            return None
        max_values = self._get_max_values(data)
        return max_values.get("thunderstorm_probability")
    
    def _extract_threshold_and_max_values(self, weather_data: WeatherData) -> Dict[str, Any]:
        """
        Extrahiert Schwellen- und Maximalwerte aus Wetterdaten.
        
        Args:
            weather_data: Wetterdaten
            
        Returns:
            Dictionary mit Schwellen- und Maximalwerten
        """
        rain_prob_threshold = None
        rain_prob_max = None
        rain_amt_threshold = None
        rain_amt_max = None
        thunder_prob_threshold = None
        thunder_prob_max = None
        rain_prob_time_threshold = None
        rain_prob_time_max = None
        rain_amt_time_threshold = None
        rain_amt_time_max = None
        thunder_time_threshold = None
        thunder_time_max = None

        rain_prob_thresh = self.thresholds.get('regen', 0)
        rain_amt_thresh = self.thresholds.get('regenmenge', 0)
        thunder_thresh = self.thresholds.get('gewitter', 0)

        max_rain_prob = -1
        max_rain_amt = -1
        max_thunder_prob = -1
        
        for p in weather_data.points:
            # Niederschlagsmenge (mm)
            if p.precipitation is not None:
                if rain_amt_threshold is None and p.precipitation >= rain_amt_thresh:
                    rain_amt_threshold = p.precipitation
                    rain_amt_time_threshold = p.time.strftime('%H:%M')
                if p.precipitation > max_rain_amt:
                    max_rain_amt = p.precipitation
                    rain_amt_max = p.precipitation
                    rain_amt_time_max = p.time.strftime('%H:%M')
            
            # Regenwahrscheinlichkeit (%)
            if hasattr(p, 'rain_probability') and p.rain_probability is not None:
                if rain_prob_threshold is None and p.rain_probability >= rain_prob_thresh:
                    rain_prob_threshold = int(p.rain_probability)
                    rain_prob_time_threshold = p.time.strftime('%H:%M')
                if p.rain_probability > max_rain_prob:
                    max_rain_prob = int(p.rain_probability)
                    rain_prob_max = int(p.rain_probability)
                    rain_prob_time_max = p.time.strftime('%H:%M')
            
            # Gewitterwahrscheinlichkeit
            if p.thunderstorm_probability is not None:
                if thunder_prob_threshold is None and p.thunderstorm_probability >= thunder_thresh:
                    thunder_prob_threshold = int(p.thunderstorm_probability)
                    thunder_time_threshold = p.time.strftime('%H:%M')
                if p.thunderstorm_probability > max_thunder_prob:
                    max_thunder_prob = int(p.thunderstorm_probability)
                    thunder_prob_max = int(p.thunderstorm_probability)
                    thunder_time_max = p.time.strftime('%H:%M')
        
        # Fallback: if no threshold exceeded, use max values
        if rain_amt_threshold is None and rain_amt_max is not None:
            rain_amt_threshold = rain_amt_max
            rain_amt_time_threshold = rain_amt_time_max
        if rain_prob_threshold is None and rain_prob_max is not None:
            rain_prob_threshold = rain_prob_max
            rain_prob_time_threshold = rain_prob_time_max
        if thunder_prob_threshold is None and thunder_prob_max is not None:
            thunder_prob_threshold = thunder_prob_max
            thunder_time_threshold = thunder_time_max
        
        return {
            'rain_prob_threshold': rain_prob_threshold,
            'rain_prob_time_threshold': rain_prob_time_threshold,
            'rain_amt_threshold': rain_amt_threshold,
            'rain_amt_time_threshold': rain_amt_time_threshold,
            'rain_prob_max': rain_prob_max,
            'rain_prob_time_max': rain_prob_time_max,
            'rain_amt_max': rain_amt_max,
            'rain_amt_time_max': rain_amt_time_max,
            'thunder_prob_threshold': thunder_prob_threshold,
            'thunder_time_threshold': thunder_time_threshold,
            'thunder_prob_max': thunder_prob_max,
            'thunder_time_max': thunder_time_max
        }
    
    def aggregate_evening_report(
        self,
        stage_name: str,
        date: datetime,
        weather: StageWeather
    ) -> WeatherReport:
        """
        Erstellt einen Abendbericht.
        
        Args:
            stage_name: Name der Etappe
            date: Datum
            weather: Wetterdaten
            
        Returns:
            WeatherReport-Objekt
        """
        # Nachttemperatur vom letzten Punkt der heutigen Etappe
        night_temp = self._get_night_temperature(weather.today)
        
        # Maximalwerte für die morgige Etappe
        max_values = self._get_max_values(weather.tomorrow) if weather.tomorrow else {}
        
        # Gewitterwahrscheinlichkeit für übermorgen
        thunderstorm_plus1 = self._get_next_day_thunderstorm(weather.day_after_tomorrow)
        
        # Zeitpunkte aus den Wetterdaten extrahieren (angenommen, WeatherData hat ein Attribut .meta oder .extras mit diesen Infos)
        rain_time_threshold = weather.tomorrow.rain_time_threshold if weather.tomorrow else None
        rain_time_max = weather.tomorrow.rain_time_max if weather.tomorrow else None
        thunder_time_threshold = weather.tomorrow.thunder_time_threshold if weather.tomorrow else None
        thunder_time_max = weather.tomorrow.thunder_time_max if weather.tomorrow else None
        
        # Schwellen- und Maximalwerte extrahieren
        threshold_values = self._extract_threshold_and_max_values(weather.tomorrow) if weather.tomorrow else {}
        
        return WeatherReport(
            mode=ReportMode.EVENING,
            stage_name=stage_name,
            date=date,
            night_temperature=night_temp,
            max_temperature=max_values.get("temperature", 0),
            max_feels_like=max_values.get("feels_like", 0),
            max_precipitation=max_values.get("precipitation", 0),
            max_precipitation_probability=max_values.get("precipitation_probability", None),
            max_thunderstorm_probability=max_values.get("thunderstorm_probability"),
            max_wind_speed=max_values.get("wind_speed", 0),
            max_cloud_cover=max_values.get("cloud_cover", 0),
            next_day_thunderstorm=self._get_next_day_thunderstorm(weather.tomorrow),
            thunderstorm_plus1=thunderstorm_plus1,
            text="",  # Wird später generiert
            rain_time_threshold=rain_time_threshold,
            rain_time_max=rain_time_max,
            thunder_time_threshold=thunder_time_threshold,
            thunder_time_max=thunder_time_max,
            # Schwellen- und Maximalwerte
            rain_prob_threshold=threshold_values.get('rain_prob_threshold'),
            rain_prob_time_threshold=threshold_values.get('rain_prob_time_threshold'),
            rain_amt_threshold=threshold_values.get('rain_amt_threshold'),
            rain_amt_time_threshold=threshold_values.get('rain_amt_time_threshold'),
            rain_prob_max=threshold_values.get('rain_prob_max'),
            rain_prob_time_max=threshold_values.get('rain_prob_time_max'),
            rain_amt_max=threshold_values.get('rain_amt_max'),
            rain_amt_time_max=threshold_values.get('rain_amt_time_max'),
            thunder_prob_threshold=threshold_values.get('thunder_prob_threshold'),
            thunder_prob_time_threshold=threshold_values.get('thunder_time_threshold'),
            thunder_prob_max=threshold_values.get('thunder_prob_max'),
            thunder_prob_time_max=threshold_values.get('thunder_time_max')
        )
    
    def aggregate_morning_report(
        self,
        stage_name: str,
        date: datetime,
        weather: StageWeather
    ) -> WeatherReport:
        """
        Erstellt einen Morgenbericht.
        
        Args:
            stage_name: Name der Etappe
            date: Datum
            weather: Wetterdaten
            
        Returns:
            WeatherReport-Objekt
        """
        # Maximalwerte für die heutige Etappe
        max_values = self._get_max_values(weather.today)
        
        # Gewitterwahrscheinlichkeit für morgen
        next_day_thunderstorm = self._get_next_day_thunderstorm(weather.tomorrow)
        
        # Schwellen- und Maximalwerte extrahieren
        threshold_values = self._extract_threshold_and_max_values(weather.today)
        
        return WeatherReport(
            mode=ReportMode.MORNING,
            stage_name=stage_name,
            date=date,
            night_temperature=None,  # Keine Nachttemperatur im Morgenbericht
            max_temperature=max_values.get("temperature", 0),
            max_feels_like=max_values.get("feels_like", 0),
            max_precipitation=max_values.get("precipitation", 0),
            max_precipitation_probability=max_values.get("precipitation_probability", None),
            max_thunderstorm_probability=max_values.get("thunderstorm_probability"),
            max_wind_speed=max_values.get("wind_speed", 0),
            max_cloud_cover=max_values.get("cloud_cover", 0),
            next_day_thunderstorm=next_day_thunderstorm,
            text="",  # Wird später generiert
            # Schwellen- und Maximalwerte
            rain_prob_threshold=threshold_values['rain_prob_threshold'],
            rain_prob_time_threshold=threshold_values['rain_prob_time_threshold'],
            rain_amt_threshold=threshold_values['rain_amt_threshold'],
            rain_amt_time_threshold=threshold_values['rain_amt_time_threshold'],
            rain_prob_max=threshold_values['rain_prob_max'],
            rain_prob_time_max=threshold_values['rain_prob_time_max'],
            rain_amt_max=threshold_values['rain_amt_max'],
            rain_amt_time_max=threshold_values['rain_amt_time_max'],
            thunder_prob_threshold=threshold_values['thunder_prob_threshold'],
            thunder_prob_time_threshold=threshold_values['thunder_time_threshold'],
            thunder_prob_max=threshold_values['thunder_prob_max'],
            thunder_prob_time_max=threshold_values['thunder_time_max']
        )
    
    def aggregate_day_warning(
        self,
        stage_name: str,
        date: datetime,
        weather: StageWeather
    ) -> WeatherReport:
        """
        Erstellt eine Tageswarnung bei signifikanter Verschlechterung.
        
        Args:
            stage_name: Name der Etappe
            date: Datum
            weather: Wetterdaten
            
        Returns:
            WeatherReport-Objekt oder None wenn keine Warnung nötig
        """
        # Maximalwerte für die heutige Etappe
        max_values = self._get_max_values(weather.today)
        
        # Prüfe auf signifikante Verschlechterung
        if (max_values.get("precipitation", 0) > self.thresholds["regen"] or
            max_values.get("thunderstorm_probability", 0) > self.thresholds["gewitter"] or
            max_values.get("wind_speed", 0) > self.thresholds["wind"]):
            
            # Schwellen- und Maximalwerte extrahieren
            threshold_values = self._extract_threshold_and_max_values(weather.today)
            
            return WeatherReport(
                mode=ReportMode.DAY,
                stage_name=stage_name,
                date=date,
                night_temperature=None,
                max_temperature=max_values.get("temperature", 0),
                max_feels_like=max_values.get("feels_like", 0),
                max_precipitation=max_values.get("precipitation", 0),
                max_precipitation_probability=max_values.get("precipitation_probability", None),
                max_thunderstorm_probability=max_values.get("thunderstorm_probability"),
                max_wind_speed=max_values.get("wind_speed", 0),
                max_cloud_cover=max_values.get("cloud_cover", 0),
                next_day_thunderstorm=None,  # Keine Vorhersage für morgen
                text="",  # Wird später generiert
                # Schwellen- und Maximalwerte
                rain_prob_threshold=threshold_values['rain_prob_threshold'],
                rain_prob_time_threshold=threshold_values['rain_prob_time_threshold'],
                rain_amt_threshold=threshold_values['rain_amt_threshold'],
                rain_amt_time_threshold=threshold_values['rain_amt_time_threshold'],
                rain_prob_max=threshold_values['rain_prob_max'],
                rain_prob_time_max=threshold_values['rain_prob_time_max'],
                rain_amt_max=threshold_values['rain_amt_max'],
                rain_amt_time_max=threshold_values['rain_amt_time_max'],
                thunder_prob_threshold=threshold_values['thunder_prob_threshold'],
                thunder_prob_time_threshold=threshold_values['thunder_time_threshold'],
                thunder_prob_max=threshold_values['thunder_prob_max'],
                thunder_prob_time_max=threshold_values['thunder_time_max']
            )
        
        return None 