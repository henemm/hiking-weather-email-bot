from datetime import datetime
from typing import Optional
from src.weather.models import WeatherReport, ReportMode

class ReportGenerator:
    """Generiert lesbare Wetterberichte aus den Wetterdaten"""
    
    def __init__(self, thresholds: dict):
        """
        Initialisiert den Report-Generator.
        
        Args:
            thresholds: Dictionary mit Schwellenwerten
        """
        self.thresholds = thresholds
    
    def _format_temperature(self, temp: float) -> str:
        """Formatiert eine Temperatur mit Grad-Symbol"""
        return f"{temp:.1f}°C"
    
    def _format_percentage(self, value: Optional[float]) -> str:
        """Formatiert einen Prozentwert"""
        if value is None:
            return "unbekannt"
        return f"{value:.0f}%"
    
    def _format_mm(self, value: float) -> str:
        """Formatiert einen Wert in Millimetern"""
        return f"{value:.1f}mm"
    
    def _format_kmh(self, value: float) -> str:
        """Formatiert einen Wert in km/h"""
        return f"{value:.0f}km/h"
    
    def _get_risk_level(self, value: float, threshold: float) -> str:
        """Bestimmt das Risikoniveau basierend auf einem Schwellenwert"""
        if value > threshold * 1.5:
            return "hoch"
        elif value > threshold:
            return "mittel"
        return "niedrig"
    
    def _get_risk_text(self, value: float, threshold: float, unit: str) -> str:
        """Generiert einen Risikotext"""
        level = self._get_risk_level(value, threshold)
        if level == "hoch":
            return f"sehr {unit}"
        elif level == "mittel":
            return unit
        return f"gering {unit}"
    
    def generate_evening_report(self, report: WeatherReport) -> str:
        """Generiert einen Abendbericht"""
        lines = [
            f"Wetterbericht für {report.stage_name} am {report.date.strftime('%d.%m.%Y')}",
            "",
            "Nachttemperatur:",
            f"  {self._format_temperature(report.night_temperature)}",
            "",
            "Risiken für morgen:",
            f"  Regen: {self._get_risk_text(report.max_precipitation, self.thresholds['regen'], 'Regen')} ({self._format_mm(report.max_precipitation)})",
            f"  Gewitter: {self._get_risk_text(report.max_thunderstorm_probability or 0, self.thresholds['gewitter'], 'Gewitter')} ({self._format_percentage(report.max_thunderstorm_probability)})",
            f"  Wind: {self._get_risk_text(report.max_wind_speed, self.thresholds['wind'], 'Wind')} ({self._format_kmh(report.max_wind_speed)})",
            f"  Hitze: {self._get_risk_text(report.max_feels_like, self.thresholds['hitze'], 'Hitze')} ({self._format_temperature(report.max_feels_like)})",
        ]
        
        if report.next_day_thunderstorm:
            lines.extend([
                "",
                "Gewitterwahrscheinlichkeit für übermorgen:",
                f"  {self._format_percentage(report.next_day_thunderstorm)}"
            ])
        
        if report.thunderstorm_plus1 is not None:
            lines.extend([
                "",
                "Thunderstorm probability for the day after tomorrow:",
                f"  {self._format_percentage(report.thunderstorm_plus1)}"
            ])
        
        return "\n".join(lines)
    
    def generate_morning_report(self, report: WeatherReport) -> str:
        """Generiert einen Morgenbericht"""
        lines = [
            f"Wetterbericht für {report.stage_name} am {report.date.strftime('%d.%m.%Y')}",
            "",
            "Risiken für heute:",
            f"  Regen: {self._get_risk_text(report.max_precipitation, self.thresholds['regen'], 'Regen')} ({self._format_mm(report.max_precipitation)})",
            f"  Gewitter: {self._get_risk_text(report.max_thunderstorm_probability or 0, self.thresholds['gewitter'], 'Gewitter')} ({self._format_percentage(report.max_thunderstorm_probability)})",
            f"  Wind: {self._get_risk_text(report.max_wind_speed, self.thresholds['wind'], 'Wind')} ({self._format_kmh(report.max_wind_speed)})",
            f"  Hitze: {self._get_risk_text(report.max_feels_like, self.thresholds['hitze'], 'Hitze')} ({self._format_temperature(report.max_feels_like)})",
        ]
        
        if report.next_day_thunderstorm:
            lines.extend([
                "",
                "Gewitterwahrscheinlichkeit für morgen:",
                f"  {self._format_percentage(report.next_day_thunderstorm)}"
            ])
        
        return "\n".join(lines)
    
    def generate_day_warning(self, report: WeatherReport) -> str:
        """Generiert eine Tageswarnung"""
        lines = [
            f"⚠️ Wetterwarnung für {report.stage_name} am {report.date.strftime('%d.%m.%Y')}",
            "",
            "Signifikante Verschlechterung:",
        ]
        
        if report.max_precipitation > self.thresholds["regen"]:
            lines.append(f"  Regen: {self._format_mm(report.max_precipitation)}")
        if report.max_thunderstorm_probability and report.max_thunderstorm_probability > self.thresholds["gewitter"]:
            lines.append(f"  Gewitter: {self._format_percentage(report.max_thunderstorm_probability)}")
        if report.max_wind_speed > self.thresholds["wind"]:
            lines.append(f"  Wind: {self._format_kmh(report.max_wind_speed)}")
        
        return "\n".join(lines)
    
    def generate_report(self, report: WeatherReport) -> str:
        """
        Generiert einen Wetterbericht basierend auf dem Modus.
        
        Args:
            report: WeatherReport-Objekt
            
        Returns:
            Formatierter Berichtstext
        """
        if report.mode == ReportMode.EVENING:
            return self.generate_evening_report(report)
        elif report.mode == ReportMode.MORNING:
            return self.generate_morning_report(report)
        else:  # ReportMode.DAY
            return self.generate_day_warning(report) 