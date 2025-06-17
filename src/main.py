import logging
import sys
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from src.config import get_config
from src.etappen import lade_heutige_etappe
from src.weather.api import WeatherAPIClient
from src.weather.aggregator import WeatherAggregator
from src.weather.models import StageWeather, WeatherData, ReportMode, WeatherPoint
from src.report.generator import ReportGenerator
from src.email_sender import sende_email, EmailError

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/hiking-weather-bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def hole_wetterdaten(
    api_client: WeatherAPIClient,
    etappe: dict,
    start_date: datetime,
    end_date: datetime
) -> WeatherData:
    """
    Holt Wetterdaten für eine Etappe.
    
    Args:
        api_client: API-Client
        etappe: Etappendaten
        start_date: Startdatum
        end_date: Enddatum
        
    Returns:
        WeatherData-Objekt
    """
    return api_client.get_weather(
        latitude=etappe["punkte"][0]["lat"],
        longitude=etappe["punkte"][0]["lon"],
        elevation=etappe.get("elevation"),
        start_date=start_date,
        end_date=end_date
    )

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Wetterwarnung für Wanderungen")
    parser.add_argument("--modus", choices=["evening", "morning", "day"], required=True,
                       help="Type of weather report (evening, morning, day)")
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

def create_weather_data(day_data: Dict[str, Any]) -> WeatherData:
    """Konvertiert die Testdaten in das WeatherData-Modell."""
    points = []
    for hour_data in day_data.get("hourly", []):
        point = WeatherPoint(
            latitude=hour_data.get("latitude", 0),
            longitude=hour_data.get("longitude", 0),
            elevation=hour_data.get("elevation", 0),
            time=datetime.fromisoformat(hour_data["time"]),
            temperature=hour_data.get("temperature_2m", 0),
            feels_like=hour_data.get("apparent_temperature", 0),
            precipitation=hour_data.get("precipitation_probability", 0),
            thunderstorm_probability=hour_data.get("thunderstorm_probability", 0),
            wind_speed=hour_data.get("wind_speed_10m", 0),
            wind_direction=hour_data.get("wind_direction_10m", 0),
            cloud_cover=hour_data.get("cloud_cover", 0)
        )
        points.append(point)
    
    # Extrahiere Zeitpunkte für Regen und Gewitter
    rain_time_threshold = None
    rain_time_max = None
    thunder_time_threshold = None
    thunder_time_max = None
    
    # Finde Zeitpunkt des Maximums für Regen und Gewitter
    max_rain = 0
    max_thunder = 0
    for point in points:
        if point.precipitation > max_rain:
            max_rain = point.precipitation
            rain_time_max = point.time.isoformat()
        if point.thunderstorm_probability > max_thunder:
            max_thunder = point.thunderstorm_probability
            thunder_time_max = point.time.isoformat()
    
    # Finde ersten Zeitpunkt über Schwellenwert
    for point in points:
        if point.precipitation > 20 and not rain_time_threshold:  # 20% Schwellenwert
            rain_time_threshold = point.time.isoformat()
        if point.thunderstorm_probability > 30 and not thunder_time_threshold:  # 30% Schwellenwert
            thunder_time_threshold = point.time.isoformat()
    
    return WeatherData(
        points=points,
        rain_time_threshold=rain_time_threshold,
        rain_time_max=rain_time_max,
        thunder_time_threshold=thunder_time_threshold,
        thunder_time_max=thunder_time_max
    )

def main():
    """Hauptfunktion"""
    # Kommandozeilenargumente parsen
    args = parse_args()
    mode = ReportMode(args.modus)
    try:
        config = get_config()
        logger.info(f"Starte im {mode.value}-Modus")
        etappe = lade_heutige_etappe(config)
        logger.info(f"Lade Etappe: {etappe['name']}")
        # Wetterdaten aus Testdatei laden, falls --input gesetzt
        if args.input:
            with open(args.input, 'r') as f:
                testdata = json.load(f)
            
            weather = StageWeather(
                today=create_weather_data(testdata.get('today')),
                tomorrow=create_weather_data(testdata.get('tomorrow')),
                day_after_tomorrow=create_weather_data(testdata.get('day_after_tomorrow'))
            )
        else:
            # API-Client initialisieren
            api_client = WeatherAPIClient()
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_start = today_start + timedelta(days=1)
            day_after_start = tomorrow_start + timedelta(days=1)
            weather = StageWeather(
                today=hole_wetterdaten(api_client, etappe, today_start, tomorrow_start),
                tomorrow=hole_wetterdaten(api_client, etappe, tomorrow_start, day_after_start),
                day_after_tomorrow=hole_wetterdaten(api_client, etappe, day_after_start, day_after_start + timedelta(days=1))
            )
        # Aggregator und Report-Generator initialisieren
        aggregator = WeatherAggregator(config["schwellen"])
        report_generator = ReportGenerator(config["schwellen"])
        # Report generieren
        if mode == ReportMode.EVENING:
            report = aggregator.aggregate_evening_report(
                etappe["name"],
                datetime.now(),
                weather
            )
        elif mode == ReportMode.MORNING:
            report = aggregator.aggregate_morning_report(
                etappe["name"],
                datetime.now(),
                weather
            )
        else:  # ReportMode.DAY
            report = aggregator.aggregate_day_warning(
                etappe["name"],
                datetime.now(),
                weather
            )
            if not report:
                logger.info("Keine Tageswarnung nötig")
                return
        # Report-Text generieren
        if args.inreach:
            report.text = report_generator.generate_inreach(report)
        else:
            report.text = report_generator.generate_report(report)
        if args.dry_run:
            print("\n=== Wetterbericht (nur Ausgabe, keine E-Mail) ===\n")
            print(report.text)
            print("\n=== Ende Bericht ===\n")
        else:
            print("=== Wetterbericht ===")
            print(report.text)
            print("=====================")
            sende_email(
                text=report.text,
                smtp_config=config["smtp"]
            )
            logger.info("Wetterbericht erfolgreich gesendet")
    except Exception as e:
        logger.error(f"Fehler: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 