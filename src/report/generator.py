import logging
from datetime import datetime
from typing import Optional, Dict, Any
from src.weather.models import WeatherReport, ReportMode, WeatherData
import yaml
import os

logger = logging.getLogger(__name__)

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
    
    def _format_rain_inreach(self, mm: float, prob: Optional[float]) -> str:
        if mm and prob is not None:
            return f"{self._format_mm(mm)}/{self._format_percentage(prob)}"
        elif mm:
            return f"{self._format_mm(mm)}"
        elif prob is not None:
            return f"{self._format_percentage(prob)}"
        else:
            return "-"
    
    def _format_risk_value(self, value1, value2, unit1, unit2=None):
        """Hilfsfunktion: Zeigt nur beide Werte, wenn sie sich unterscheiden und sinnvoll sind."""
        if value1 is None and value2 is None:
            return "–"
        if value2 is None or value1 == value2:
            return f"{value1}{unit1}" if value1 is not None else f"{value2}{unit2}"
        return f"{value1}{unit1}, {value2}{unit2 if unit2 else ''}"
    
    def _format_time(self, timestr: str) -> str:
        """Formatiert einen ISO-String zu HH:MM."""
        if not timestr:
            return "-"
        try:
            return datetime.fromisoformat(timestr).strftime("%H:%M")
        except Exception:
            # Fallback, falls das Format nicht passt
            return timestr[-8:-3] if len(timestr) >= 8 else timestr
    
    def generate_evening_report(self, report: WeatherReport) -> str:
        """Generiert einen Abendbericht mit Zeitpunkten und richtiger Reihenfolge"""
        etappe = report.stage_name
        gewitter = self._format_thunder(report.max_thunderstorm_probability, report.thunder_time_threshold, report.thunder_time_max)
        regen = self._format_rain(report.max_precipitation, report.rain_time_threshold, report.rain_time_max)
        wind = self._format_wind(report.max_wind_speed)
        hitze = self._format_heat(report.max_feels_like)
        nacht = self._format_night_temp(report.night_temperature)
        return f"{etappe} | {gewitter} | {regen} | {wind} | {hitze} | {nacht}"
    
    def generate_evening_inreach(self, report: WeatherReport, rain_prob_threshold, rain_prob_time_threshold, rain_amt_threshold, rain_amt_time_threshold, rain_prob_max, rain_prob_time_max, rain_amt_max, rain_amt_time_max, thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max):
        etappe = report.stage_name
        def fmt(val, unit=None):
            if val is None or (isinstance(val, (float, int)) and val == 0):
                return "-"
            return f"{val}{unit}" if unit else str(val)
        def fmt_time_short(timestr):
            """Format time as HH only for InReach format"""
            if not timestr:
                return None
            try:
                # Try to parse as ISO format first
                return datetime.fromisoformat(timestr).strftime("%H")
            except Exception:
                # If that fails, try to extract hours from HH:MM format
                if ':' in timestr:
                    return timestr.split(':')[0]
                # If no colon, try to get first two characters
                return timestr[:2] if len(timestr) >= 2 else timestr
        def fmt_val_time(val, time, unit=None):
            v = fmt(val, unit)
            if v == "-":
                return "-"
            if not time:
                return v
            t = fmt_time_short(time)
            if t is None:
                return v
            return f"{v}@{t}"
        def fmt_risk_with_time(threshold_val, threshold_time, max_val, max_time, unit=None):
            """Format risk value, showing only one value if threshold equals maximum"""
            if threshold_val is None and max_val is None:
                return "-"
            if threshold_val == max_val and threshold_time == max_time:
                # Same value and time - show only once
                return fmt_val_time(threshold_val, threshold_time, unit)
            else:
                # Different values or times - show both
                threshold_str = fmt_val_time(threshold_val, threshold_time, unit)
                max_str = fmt_val_time(max_val, max_time, unit)
                if threshold_str == "-" and max_str != "-":
                    return max_str
                elif threshold_str != "-" and max_str == "-":
                    return threshold_str
                elif threshold_str == "-" and max_str == "-":
                    return "-"
                else:
                    return f"{threshold_str} ({max_str})"
        
        # Gewitter
        gewitter = fmt_risk_with_time(thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max, '%')
        
        # Regen - combine probability and amount
        rain_prob_str = fmt_risk_with_time(rain_prob_threshold, rain_prob_time_threshold, rain_prob_max, rain_prob_time_max, '%')
        rain_amt_str = fmt_risk_with_time(rain_amt_threshold, rain_amt_time_threshold, rain_amt_max, rain_amt_time_max, 'mm')
        
        if rain_prob_str == "-" and rain_amt_str == "-":
            regen = "-"
        elif rain_prob_str == "-":
            regen = rain_amt_str
        elif rain_amt_str == "-":
            regen = rain_prob_str
        else:
            regen = f"{rain_prob_str} {rain_amt_str}"
        
        wind = fmt(report.max_wind_speed, "km/h")
        hitze = fmt(report.max_feels_like, "°C")
        nacht = fmt(report.night_temperature, "°C")
        return f"{etappe} | Gewitter {gewitter} | Regen {regen} | Wind {wind} | Hitze {hitze} | Nacht {nacht}"
    
    def generate_evening_email_html(self, report: WeatherReport, rain_prob_threshold: Optional[float], rain_prob_time_threshold: Optional[str], rain_amt_threshold: Optional[float], rain_amt_time_threshold: Optional[str], rain_prob_max: Optional[float], rain_prob_time_max: Optional[str], rain_amt_max: Optional[float], rain_amt_time_max: Optional[str], thunder_prob_threshold: Optional[float], thunder_time_threshold: Optional[str], thunder_prob_max: Optional[float], thunder_time_max: Optional[str]) -> str:
        return report.text

    def generate_evening_email_plaintext(self, report: WeatherReport, rain_prob_threshold: Optional[float], rain_prob_time_threshold: Optional[str], rain_amt_threshold: Optional[float], rain_amt_time_threshold: Optional[str], rain_prob_max: Optional[float], rain_prob_time_max: Optional[str], rain_amt_max: Optional[float], rain_amt_time_max: Optional[str], thunder_prob_threshold: Optional[float], thunder_time_threshold: Optional[str], thunder_prob_max: Optional[float], thunder_time_max: Optional[str]) -> str:
        return report.text
    
    def generate_morning_report(self, report: WeatherReport) -> str:
        def fmt(val, unit=None):
            if val is None or (isinstance(val, (float, int)) and val == 0):
                return "-"
            return f"{val}{unit}" if unit else str(val)
        def fmt_time(timestr):
            if not timestr:
                return None
            try:
                return datetime.fromisoformat(timestr).strftime("%H:%M")
            except Exception:
                return timestr[-5:] if len(timestr) >= 5 else timestr
        def fmt_val_time(val, time, unit=None):
            v = fmt(val, unit)
            t = fmt_time(time)
            if v == "-":
                return "-"
            if t is None:
                return v
            return f"{v}@{t}"
        def fmt_risk_with_time(threshold_val, threshold_time, max_val, max_time, unit=None):
            """Format risk value, showing only one value if threshold equals maximum"""
            if threshold_val is None and max_val is None:
                return "-"
            if threshold_val == max_val and threshold_time == max_time:
                # Same value and time - show only once
                return fmt_val_time(threshold_val, threshold_time, unit)
            else:
                # Different values or times - show both
                threshold_str = fmt_val_time(threshold_val, threshold_time, unit)
                max_str = fmt_val_time(max_val, max_time, unit)
                if threshold_str == "-" and max_str != "-":
                    return max_str
                elif threshold_str != "-" and max_str == "-":
                    return threshold_str
                elif threshold_str == "-" and max_str == "-":
                    return "-"
                else:
                    return f"{threshold_str} ({max_str})"
        
        # Regenwahrscheinlichkeit
        regen_prob = fmt_risk_with_time(report.rain_prob_threshold, report.rain_prob_time_threshold, report.rain_prob_max, report.rain_prob_time_max, "%")
        # Niederschlagsmenge
        regen_amt = fmt_risk_with_time(report.rain_amt_threshold, report.rain_amt_time_threshold, report.rain_amt_max, report.rain_amt_time_max, "mm")
        # Gewitterwahrscheinlichkeit
        gew = fmt_risk_with_time(report.thunder_prob_threshold, report.thunder_prob_time_threshold, report.thunder_prob_max, report.thunder_prob_time_max, "%")
        # Wind
        wind = fmt(report.max_wind_speed, "km/h")
        # Hitze
        hitze = fmt(report.max_feels_like, "°C")
        # Übermorgen Gewitter
        gew_plus1 = fmt(report.next_day_thunderstorm, "%")
        lines = [
            f"Wetterbericht für {report.stage_name} am {report.date.strftime('%d.%m.%Y')}",
            "",
            "Risiken für heute:",
            f"  Regenwahrscheinlichkeit: {regen_prob}",
            f"  Niederschlagsmenge: {regen_amt}",
            f"  Gewitterwahrscheinlichkeit: {gew}",
            f"  Wind: {wind}",
            f"  Hitze: {hitze}",
            "",
            "Gewitterwahrscheinlichkeit für morgen:",
            f"  {gew_plus1}"
        ]
        return "\n".join(lines)
    
    def generate_morning_inreach(self, report: WeatherReport, rain_prob_threshold, rain_prob_time_threshold, rain_amt_threshold, rain_amt_time_threshold, rain_prob_max, rain_prob_time_max, rain_amt_max, rain_amt_time_max, thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max):
        etappe = report.stage_name
        def fmt(val, unit=None):
            if val is None or (isinstance(val, (float, int)) and val == 0):
                return "-"
            return f"{val}{unit}" if unit else str(val)
        def fmt_time_short(timestr):
            """Format time as HH only for InReach format"""
            if not timestr:
                return None
            try:
                # Try to parse as ISO format first
                return datetime.fromisoformat(timestr).strftime("%H")
            except Exception:
                # If that fails, try to extract hours from HH:MM format
                if ':' in timestr:
                    return timestr.split(':')[0]
                # If no colon, try to get first two characters
                return timestr[:2] if len(timestr) >= 2 else timestr
        def fmt_val_time(val, time, unit=None):
            v = fmt(val, unit)
            if v == "-":
                return "-"
            if not time:
                return v
            t = fmt_time_short(time)
            if t is None:
                return v
            return f"{v}@{t}"
        def fmt_risk_with_time(threshold_val, threshold_time, max_val, max_time, unit=None):
            """Format risk value, showing only one value if threshold equals maximum"""
            if threshold_val is None and max_val is None:
                return "-"
            if threshold_val == max_val and threshold_time == max_time:
                # Same value and time - show only once
                return fmt_val_time(threshold_val, threshold_time, unit)
            else:
                # Different values or times - show both
                threshold_str = fmt_val_time(threshold_val, threshold_time, unit)
                max_str = fmt_val_time(max_val, max_time, unit)
                if threshold_str == "-" and max_str != "-":
                    return max_str
                elif threshold_str != "-" and max_str == "-":
                    return threshold_str
                elif threshold_str == "-" and max_str == "-":
                    return "-"
                else:
                    return f"{threshold_str} ({max_str})"
        
        # Gewitter
        gewitter = fmt_risk_with_time(thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max, '%')
        
        # Regen - combine probability and amount
        rain_prob_str = fmt_risk_with_time(rain_prob_threshold, rain_prob_time_threshold, rain_prob_max, rain_prob_time_max, '%')
        rain_amt_str = fmt_risk_with_time(rain_amt_threshold, rain_amt_time_threshold, rain_amt_max, rain_amt_time_max, 'mm')
        
        if rain_prob_str == "-" and rain_amt_str == "-":
            regen = "-"
        elif rain_prob_str == "-":
            regen = rain_amt_str
        elif rain_amt_str == "-":
            regen = rain_prob_str
        else:
            regen = f"{rain_prob_str} {rain_amt_str}"
        
        wind = fmt(report.max_wind_speed, "km/h")
        hitze = fmt(report.max_feels_like, "°C")
        return f"{etappe} | Gewitter {gewitter} | Regen {regen} | Wind {wind} | Hitze {hitze}"
    
    def generate_morning_email_html(self, report: WeatherReport, rain_prob_threshold: Optional[float], rain_prob_time_threshold: Optional[str], rain_amt_threshold: Optional[float], rain_amt_time_threshold: Optional[str], rain_prob_max: Optional[float], rain_prob_time_max: Optional[str], rain_amt_max: Optional[float], rain_amt_time_max: Optional[str], thunder_prob_threshold: Optional[float], thunder_time_threshold: Optional[str], thunder_prob_max: Optional[float], thunder_time_max: Optional[str]) -> str:
        return report.text

    def generate_morning_email_plaintext(self, report: WeatherReport, rain_prob_threshold: Optional[float], rain_prob_time_threshold: Optional[str], rain_amt_threshold: Optional[float], rain_amt_time_threshold: Optional[str], rain_prob_max: Optional[float], rain_prob_time_max: Optional[str], rain_amt_max: Optional[float], rain_amt_time_max: Optional[str], thunder_prob_threshold: Optional[float], thunder_time_threshold: Optional[str], thunder_prob_max: Optional[float], thunder_time_max: Optional[str]) -> str:
        return report.text
    
    def generate_day_warning(self, report: WeatherReport) -> str:
        """Generiert eine Tageswarnung mit Zeitpunkten und richtiger Reihenfolge"""
        etappe = report.stage_name
        gewitter = self._format_thunder(report.max_thunderstorm_probability, report.thunder_time_threshold, report.thunder_time_max)
        regen = self._format_rain(report.max_precipitation, report.rain_time_threshold, report.rain_time_max)
        wind = self._format_wind(report.max_wind_speed)
        hitze = self._format_heat(report.max_feels_like)
        return f"{etappe} | {gewitter} | {regen} | {wind} | {hitze}"
    
    def generate_day_inreach(self, report: WeatherReport, rain_prob_threshold, rain_prob_time_threshold, rain_amt_threshold, rain_amt_time_threshold, rain_prob_max, rain_prob_time_max, rain_amt_max, rain_amt_time_max, thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max):
        etappe = report.stage_name
        def fmt(val, unit=None):
            if val is None or (isinstance(val, (float, int)) and val == 0):
                return "-"
            return f"{val}{unit}" if unit else str(val)
        def fmt_time_short(timestr):
            """Format time as HH only for InReach format"""
            if not timestr:
                return None
            try:
                # Try to parse as ISO format first
                return datetime.fromisoformat(timestr).strftime("%H")
            except Exception:
                # If that fails, try to extract hours from HH:MM format
                if ':' in timestr:
                    return timestr.split(':')[0]
                # If no colon, try to get first two characters
                return timestr[:2] if len(timestr) >= 2 else timestr
        def fmt_val_time(val, time, unit=None):
            v = fmt(val, unit)
            if v == "-":
                return "-"
            if not time:
                return v
            t = fmt_time_short(time)
            if t is None:
                return v
            return f"{v}@{t}"
        def fmt_risk_with_time(threshold_val, threshold_time, max_val, max_time, unit=None):
            """Format risk value, showing only one value if threshold equals maximum"""
            if threshold_val is None and max_val is None:
                return "-"
            if threshold_val == max_val and threshold_time == max_time:
                # Same value and time - show only once
                return fmt_val_time(threshold_val, threshold_time, unit)
            else:
                # Different values or times - show both
                threshold_str = fmt_val_time(threshold_val, threshold_time, unit)
                max_str = fmt_val_time(max_val, max_time, unit)
                if threshold_str == "-" and max_str != "-":
                    return max_str
                elif threshold_str != "-" and max_str == "-":
                    return threshold_str
                elif threshold_str == "-" and max_str == "-":
                    return "-"
                else:
                    return f"{threshold_str} ({max_str})"
        
        # Gewitter
        gewitter = fmt_risk_with_time(thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max, '%')
        
        # Regen - combine probability and amount
        rain_prob_str = fmt_risk_with_time(rain_prob_threshold, rain_prob_time_threshold, rain_prob_max, rain_prob_time_max, '%')
        rain_amt_str = fmt_risk_with_time(rain_amt_threshold, rain_amt_time_threshold, rain_amt_max, rain_amt_time_max, 'mm')
        
        if rain_prob_str == "-" and rain_amt_str == "-":
            regen = "-"
        elif rain_prob_str == "-":
            regen = rain_amt_str
        elif rain_amt_str == "-":
            regen = rain_prob_str
        else:
            regen = f"{rain_prob_str} {rain_amt_str}"
        
        wind = fmt(report.max_wind_speed, "km/h")
        hitze = fmt(report.max_feels_like, "°C")
        return f"{etappe} | Gewitter {gewitter} | Regen {regen} | Wind {wind} | Hitze {hitze}"
    
    def generate_day_email_html(self, report: WeatherReport, rain_prob_threshold: Optional[float], rain_prob_time_threshold: Optional[str], rain_amt_threshold: Optional[float], rain_amt_time_threshold: Optional[str], rain_prob_max: Optional[float], rain_prob_time_max: Optional[str], rain_amt_max: Optional[float], rain_amt_time_max: Optional[str], thunder_prob_threshold: Optional[float], thunder_time_threshold: Optional[str], thunder_prob_max: Optional[float], thunder_time_max: Optional[str]) -> str:
        return report.text

    def generate_day_email_plaintext(self, report: WeatherReport, rain_prob_threshold: Optional[float], rain_prob_time_threshold: Optional[str], rain_amt_threshold: Optional[float], rain_amt_time_threshold: Optional[str], rain_prob_max: Optional[float], rain_prob_time_max: Optional[str], rain_amt_max: Optional[float], rain_amt_time_max: Optional[str], thunder_prob_threshold: Optional[float], thunder_time_threshold: Optional[str], thunder_prob_max: Optional[float], thunder_time_max: Optional[str]) -> str:
        return report.text
    
    def generate_evening_report_long(self, report: WeatherReport) -> str:
        def fmt(val, unit=None):
            if val is None or (isinstance(val, (float, int)) and val == 0):
                return "-"
            return f"{val}{unit}" if unit else str(val)
        def fmt_time(timestr):
            if not timestr:
                return None
            try:
                return datetime.fromisoformat(timestr).strftime("%H:%M")
            except Exception:
                return timestr[-5:] if len(timestr) >= 5 else timestr
        def fmt_val_time(val, time, unit=None):
            v = fmt(val, unit)
            t = fmt_time(time)
            if v == "-":
                return "-"
            if t is None:
                return v
            return f"{v}@{t}"
        def fmt_risk_with_time(threshold_val, threshold_time, max_val, max_time, unit=None):
            """Format risk value, showing only one value if threshold equals maximum"""
            if threshold_val is None and max_val is None:
                return "-"
            if threshold_val == max_val and threshold_time == max_time:
                # Same value and time - show only once
                return fmt_val_time(threshold_val, threshold_time, unit)
            else:
                # Different values or times - show both
                threshold_str = fmt_val_time(threshold_val, threshold_time, unit)
                max_str = fmt_val_time(max_val, max_time, unit)
                if threshold_str == "-" and max_str != "-":
                    return max_str
                elif threshold_str != "-" and max_str == "-":
                    return threshold_str
                elif threshold_str == "-" and max_str == "-":
                    return "-"
                else:
                    return f"{threshold_str} ({max_str})"
        
        # Regenwahrscheinlichkeit
        regen_prob = fmt_risk_with_time(report.rain_prob_threshold, report.rain_prob_time_threshold, report.rain_prob_max, report.rain_prob_time_max, "%")
        # Niederschlagsmenge
        regen_amt = fmt_risk_with_time(report.rain_amt_threshold, report.rain_amt_time_threshold, report.rain_amt_max, report.rain_amt_time_max, "mm")
        # Gewitterwahrscheinlichkeit
        gew = fmt_risk_with_time(report.thunder_prob_threshold, report.thunder_prob_time_threshold, report.thunder_prob_max, report.thunder_prob_time_max, "%")
        # Wind
        wind = fmt(report.max_wind_speed, "km/h")
        # Hitze
        hitze = fmt(report.max_feels_like, "°C")
        # Nacht
        nacht = fmt(report.night_temperature, "°C")
        # Übermorgen Gewitter
        gew_plus1 = fmt(report.next_day_thunderstorm, "%")
        lines = [
            f"Wetterbericht für {report.stage_name} am {report.date.strftime('%d.%m.%Y')}",
            "",
            "Nachttemperatur:",
            f"  {nacht}",
            "",
            "Risiken für morgen:",
            f"  Regenwahrscheinlichkeit: {regen_prob}",
            f"  Niederschlagsmenge: {regen_amt}",
            f"  Gewitterwahrscheinlichkeit: {gew}",
            f"  Wind: {wind}",
            f"  Hitze: {hitze}",
            "",
            "Gewitterwahrscheinlichkeit für übermorgen:",
            f"  {gew_plus1}"
        ]
        return "\n".join(lines)

    def generate_report(self, report: WeatherReport) -> str:
        """
        Generiert einen Wetterbericht basierend auf dem Modus.
        Wenn args.inreach gesetzt ist, wird das kompakte Format verwendet,
        ansonsten das ausführliche Langtext-Format.
        """
        if report.mode == ReportMode.EVENING:
            return self.generate_evening_report_long(report)
        elif report.mode == ReportMode.MORNING:
            return self.generate_morning_report(report)
        else:  # ReportMode.DAY
            return self.generate_day_warning(report)

    def _format_thunder(self, prob, time_threshold, time_max):
        if prob is None or prob == 0.0:
            return "-"
        risk = self._get_risk_level(prob, self.thresholds['gewitter'])
        val = self._format_percentage(prob)
        if time_threshold:
            return f"{risk} ({val}@{time_threshold})"
        elif time_max:
            return f"{risk} ({val}@{time_max})"
        else:
            return f"{risk} ({val})"

    def _format_rain(self, amount, time_threshold, time_max):
        if amount is None or amount == 0.0:
            return "-"
        risk = self._get_risk_level(amount, self.thresholds['regen'])
        val = self._format_mm(amount)
        if time_threshold:
            return f"{risk} ({val}@{time_threshold})"
        elif time_max:
            return f"{risk} ({val}@{time_max})"
        else:
            return f"{risk} ({val})"

    def _format_wind(self, speed):
        risk = self._get_risk_level(speed, self.thresholds['wind'])
        val = self._format_kmh(speed)
        return f"{risk} ({val})"

    def _format_heat(self, temp):
        risk = self._get_risk_level(temp, self.thresholds['hitze'])
        val = self._format_temperature(temp)
        return f"{risk} ({val})"

    def _format_night_temp(self, temp):
        if temp is None:
            return "nicht verfügbar"
        return f"{self._format_temperature(temp)}"

    def generate_inreach(self, report: WeatherReport) -> str:
        """Generiert die Kurztext-/InReach-Variante je nach Modus."""
        # Extrahiere Schwellen- und Maximalwerte aus dem Report
        rain_prob_threshold = getattr(report, 'rain_prob_threshold', None)
        rain_prob_time_threshold = getattr(report, 'rain_prob_time_threshold', None)
        rain_amt_threshold = getattr(report, 'rain_amt_threshold', None)
        rain_amt_time_threshold = getattr(report, 'rain_amt_time_threshold', None)
        rain_prob_max = getattr(report, 'rain_prob_max', None)
        rain_prob_time_max = getattr(report, 'rain_prob_time_max', None)
        rain_amt_max = getattr(report, 'rain_amt_max', None)
        rain_amt_time_max = getattr(report, 'rain_amt_time_max', None)
        thunder_prob_threshold = getattr(report, 'thunder_prob_threshold', None)
        thunder_prob_time_threshold = getattr(report, 'thunder_prob_time_threshold', None)
        thunder_prob_max = getattr(report, 'thunder_prob_max', None)
        thunder_prob_time_max = getattr(report, 'thunder_prob_time_max', None)
        
        if report.mode.name == "EVENING":
            return self.generate_evening_inreach(report, rain_prob_threshold, rain_prob_time_threshold, rain_amt_threshold, rain_amt_time_threshold, rain_prob_max, rain_prob_time_max, rain_amt_max, rain_amt_time_max, thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max)
        elif report.mode.name == "MORNING":
            return self.generate_morning_inreach(report, rain_prob_threshold, rain_prob_time_threshold, rain_amt_threshold, rain_amt_time_threshold, rain_prob_max, rain_prob_time_max, rain_amt_max, rain_amt_time_max, thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max)
        elif report.mode.name == "DAY":
            return self.generate_day_inreach(report, rain_prob_threshold, rain_prob_time_threshold, rain_amt_threshold, rain_amt_time_threshold, rain_prob_max, rain_prob_time_max, rain_amt_max, rain_amt_time_max, thunder_prob_threshold, thunder_prob_time_threshold, thunder_prob_max, thunder_prob_time_max)
        else:
            return "-"

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def determine_risk_level(max_values: Dict[str, float], next_day_thunderstorm: Optional[float], thunderstorm_plus1: Optional[float]) -> str:
    """
    Bestimmt das Risikolevel basierend auf den Maximalwerten und der Spezifikation.
    Nutzt Schwellenwerte aus config.yaml für Regen, Gewitter, Wind und Hitze. Gibt das höchste gefundene Level zurück.
    """
    config = load_config()
    thresholds = config['schwellen']

    def risk_level(value, threshold):
        if value is None:
            return 0  # niedrig
        if value > threshold * 1.5:
            return 2  # hoch
        elif value > threshold:
            return 1  # mittel
        return 0  # niedrig

    levels = [
        risk_level(max_values.get('precipitation', 0), thresholds['regen']),
        risk_level(max_values.get('thunderstorm_probability', 0), thresholds['gewitter']),
        risk_level(max_values.get('wind_speed', 0), thresholds['wind']),
        risk_level(max_values.get('feels_like', 0), thresholds['hitze'])
    ]
    # Consider next day/plus1 thunderstorm for warning
    if next_day_thunderstorm is not None:
        levels.append(risk_level(next_day_thunderstorm, thresholds['gewitter']))
    if thunderstorm_plus1 is not None:
        levels.append(risk_level(thunderstorm_plus1, thresholds['gewitter']))

    max_level = max(levels)
    if max_level == 2:
        return "hoch"
    elif max_level == 1:
        return "mittel"
    else:
        return "niedrig"

def _format_value_with_time(value, time, unit):
    if value is None or time is None:
        return "unbekannt"
    return f"{value}{unit}@{time}"

def _format_prob_and_amount(prob, prob_time, amount, amount_time):
    # e.g. 25% 2mm @10
    if prob is None and amount is None:
        return "unbekannt"
    parts = []
    if prob is not None and prob_time is not None:
        parts.append(f"{prob}%")
    if amount is not None and amount_time is not None:
        parts.append(f"{amount}mm")
    if parts and (prob_time or amount_time):
        # Use the first available time
        t = prob_time or amount_time
        return f"{' '.join(parts)} @{t}"
    return ' '.join(parts)

def _format_prob_and_amount_pair(prob1, time1, amount1, prob2, time2, amount2):
    # e.g. 25% 2mm @10 (60% 5mm @15)
    first = _format_prob_and_amount(prob1, time1, amount1, time1)
    second = _format_prob_and_amount(prob2, time2, amount2, time2)
    return f"{first} ({second})"

def generate_report_text(
    mode: ReportMode,
    stage_name: str,
    date: datetime,
    max_values: Dict[str, float],
    min_values: Dict[str, float],
    rain_prob_time_threshold: Optional[str],
    rain_prob_time_max: Optional[str],
    rain_amt_time_threshold: Optional[str],
    rain_amt_time_max: Optional[str],
    thunder_time_threshold: Optional[str],
    thunder_time_max: Optional[str],
    next_day_thunderstorm: Optional[float] = None,
    thunderstorm_plus1: Optional[float] = None,
    rain_prob_threshold: Optional[float] = None,
    rain_prob_max: Optional[float] = None,
    rain_amt_threshold: Optional[float] = None,
    rain_amt_max: Optional[float] = None,
    thunder_prob_threshold: Optional[float] = None,
    thunder_prob_max: Optional[float] = None
) -> str:
    report_lines = []
    report_lines.append(f"Wetterbericht für {stage_name} am {date.strftime('%d.%m.%Y')}")
    report_lines.append("")
    if mode == ReportMode.EVENING:
        report_lines.append("Nachttemperatur:")
        report_lines.append(f"  {min_values.get('temperature', 0)}°C")
        report_lines.append("")
        report_lines.append("Risiken für morgen:")
        report_lines.append(f"  Regenwahrscheinlichkeit: {_format_value_with_time(rain_prob_threshold, rain_prob_time_threshold, '%')} ({_format_value_with_time(rain_prob_max, rain_prob_time_max, '%')})")
        report_lines.append(f"  Niederschlagsmenge: {_format_value_with_time(rain_amt_threshold, rain_amt_time_threshold, 'mm')} ({_format_value_with_time(rain_amt_max, rain_amt_time_max, 'mm')})")
        report_lines.append(f"  Gewitterwahrscheinlichkeit: {_format_value_with_time(thunder_prob_threshold, thunder_time_threshold, '%')} ({_format_value_with_time(thunder_prob_max, thunder_time_max, '%')})")
        report_lines.append(f"  Wind: {max_values.get('wind_speed', 0)}km/h")
        report_lines.append(f"  Hitze: {max_values.get('feels_like', 0)}°C")
        report_lines.append("")
        if thunderstorm_plus1 is not None:
            report_lines.append("Gewitterwahrscheinlichkeit für übermorgen:")
            report_lines.append(f"  {thunderstorm_plus1}%")
    elif mode == ReportMode.MORNING:
        report_lines.append("Risiken für heute:")
        report_lines.append(f"  Regenwahrscheinlichkeit: {_format_value_with_time(rain_prob_threshold, rain_prob_time_threshold, '%')} ({_format_value_with_time(rain_prob_max, rain_prob_time_max, '%')})")
        report_lines.append(f"  Niederschlagsmenge: {_format_value_with_time(rain_amt_threshold, rain_amt_time_threshold, 'mm')} ({_format_value_with_time(rain_amt_max, rain_amt_time_max, 'mm')})")
        report_lines.append(f"  Gewitterwahrscheinlichkeit: {_format_value_with_time(thunder_prob_threshold, thunder_time_threshold, '%')} ({_format_value_with_time(thunder_prob_max, thunder_time_max, '%')})")
        report_lines.append(f"  Wind: {max_values.get('wind_speed', 0)}km/h")
        report_lines.append(f"  Hitze: {max_values.get('feels_like', 0)}°C")
        report_lines.append("")
        if next_day_thunderstorm is not None:
            report_lines.append("Gewitterwahrscheinlichkeit für morgen:")
            report_lines.append(f"  {next_day_thunderstorm}%")
    elif mode == ReportMode.DAY:
        report_lines.append(f"⚠️ Wetterwarnung für {stage_name} am {date.strftime('%d.%m.%Y')}")
        report_lines.append("")
        report_lines.append("Signifikante Verschlechterung:")
        report_lines.append(f"  Regenwahrscheinlichkeit: {_format_value_with_time(rain_prob_threshold, rain_prob_time_threshold, '%')} ({_format_value_with_time(rain_prob_max, rain_prob_time_max, '%')})")
        report_lines.append(f"  Niederschlagsmenge: {_format_value_with_time(rain_amt_threshold, rain_amt_time_threshold, 'mm')} ({_format_value_with_time(rain_amt_max, rain_amt_time_max, 'mm')})")
        report_lines.append(f"  Gewitterwahrscheinlichkeit: {_format_value_with_time(thunder_prob_threshold, thunder_time_threshold, '%')} ({_format_value_with_time(thunder_prob_max, thunder_time_max, '%')})")
        report_lines.append(f"  Wind: {max_values.get('wind_speed', 0)}km/h")
        report_lines.append(f"  Hitze: {max_values.get('feels_like', 0)}°C")
    return "\n".join(report_lines)

def extract_threshold_and_max_values(weather_data: WeatherData, threshold_config: dict):
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

    rain_prob_thresh = threshold_config.get('regen', 0)
    rain_amt_thresh = threshold_config.get('regenmenge', 0)
    thunder_thresh = threshold_config.get('gewitter', 0)

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
    return dict(
        rain_prob_threshold=rain_prob_threshold,
        rain_prob_time_threshold=rain_prob_time_threshold,
        rain_amt_threshold=rain_amt_threshold,
        rain_amt_time_threshold=rain_amt_time_threshold,
        rain_prob_max=rain_prob_max,
        rain_prob_time_max=rain_prob_time_max,
        rain_amt_max=rain_amt_max,
        rain_amt_time_max=rain_amt_time_max,
        thunder_prob_threshold=thunder_prob_threshold,
        thunder_time_threshold=thunder_time_threshold,
        thunder_prob_max=thunder_prob_max,
        thunder_time_max=thunder_time_max
    )

def generate_report(mode: ReportMode, stage_name: str, date: datetime, weather_data: WeatherData, next_day_thunderstorm: Optional[float] = None, thunderstorm_plus1: Optional[float] = None) -> WeatherReport:
    import yaml, os
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    thresholds = config['schwellen']
    max_values = weather_data.get_max_values()
    min_values = weather_data.get_min_values()
    extracted = extract_threshold_and_max_values(weather_data, thresholds)
    text = generate_report_text(
        mode, stage_name, date, max_values, min_values,
        extracted['rain_prob_time_threshold'], extracted['rain_prob_time_max'],
        extracted['rain_amt_time_threshold'], extracted['rain_amt_time_max'],
        extracted['thunder_time_threshold'], extracted['thunder_time_max'],
        next_day_thunderstorm, thunderstorm_plus1,
        extracted['rain_prob_threshold'], extracted['rain_prob_max'],
        extracted['rain_amt_threshold'], extracted['rain_amt_max'],
        extracted['thunder_prob_threshold'], extracted['thunder_prob_max']
    )
    return WeatherReport(
        mode=mode,
        stage_name=stage_name,
        date=date,
        night_temperature=min_values.get("temperature") if mode == ReportMode.EVENING else None,
        max_temperature=max_values.get("temperature", 0),
        max_feels_like=max_values.get("feels_like", 0),
        max_precipitation=max_values.get("precipitation", 0),
        max_thunderstorm_probability=max_values.get("thunderstorm_probability"),
        max_wind_speed=max_values.get("wind_speed", 0),
        max_cloud_cover=max_values.get("cloud_cover", 0),
        next_day_thunderstorm=next_day_thunderstorm,
        thunderstorm_plus1=thunderstorm_plus1,
        text=text,
        rain_time_threshold=extracted['rain_amt_time_threshold'],
        rain_time_max=extracted['rain_amt_time_max'],
        thunder_time_threshold=extracted['thunder_time_threshold'],
        thunder_time_max=extracted['thunder_time_max']
    )

if __name__ == "__main__":
    from datetime import datetime
    from src.weather.models import WeatherPoint, WeatherData, ReportMode
    import yaml
    config = yaml.safe_load(open('config.yaml'))
    wd = WeatherData(points=[
        WeatherPoint(latitude=47.3769, longitude=8.5417, elevation=400, time=datetime(2023,1,1,10,0), temperature=18, feels_like=16, precipitation=2, rain_probability=25, thunderstorm_probability=25, wind_speed=10, wind_direction=180, cloud_cover=50),
        WeatherPoint(latitude=47.3769, longitude=8.5417, elevation=400, time=datetime(2023,1,1,15,0), temperature=22, feels_like=20, precipitation=5, rain_probability=60, thunderstorm_probability=60, wind_speed=15, wind_direction=200, cloud_cover=70)
    ])
    stage = 'Etappe 1'
    date = datetime(2023,1,1)
    thresholds = config['schwellen']
    extracted = extract_threshold_and_max_values(wd, thresholds)
    from src.report.generator import ReportGenerator
    rg = ReportGenerator(thresholds)
    rep = generate_report(ReportMode.EVENING, stage, date, wd)
    print('\n--- KURZTEXT ABEND ---')
    print(rg.generate_evening_inreach(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    ))
    print('\n--- EMAIL HTML ABEND ---')
    print(rg.generate_evening_email_html(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    ))
    print('\n--- EMAIL PLAINTEXT ABEND ---')
    print(rg.generate_evening_email_plaintext(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    ))
    rep = generate_report(ReportMode.MORNING, stage, date, wd, next_day_thunderstorm=30)
    print('\n--- KURZTEXT MORGEN ---')
    print(rg.generate_morning_inreach(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    ))
    print('\n--- EMAIL HTML MORGEN ---')
    print(rg.generate_morning_email_html(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    ))
    print('\n--- EMAIL PLAINTEXT MORGEN ---')
    print(rg.generate_morning_email_plaintext(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    ))
    rep = generate_report(ReportMode.DAY, stage, date, wd, thunderstorm_plus1=70)
    print('\n--- KURZTEXT TAG ---')
    print(rg.generate_day_inreach(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    ))
    print('\n--- EMAIL HTML TAG ---')
    print(rg.generate_day_email_html(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    ))
    print('\n--- EMAIL PLAINTEXT TAG ---')
    print(rg.generate_day_email_plaintext(
        rep,
        extracted['rain_prob_threshold'], extracted['rain_prob_time_threshold'],
        extracted['rain_amt_threshold'], extracted['rain_amt_time_threshold'],
        extracted['rain_prob_max'], extracted['rain_prob_time_max'],
        extracted['rain_amt_max'], extracted['rain_amt_time_threshold'],
        extracted['thunder_prob_threshold'], extracted['thunder_time_threshold'],
        extracted['thunder_prob_max'], extracted['thunder_time_max']
    )) 