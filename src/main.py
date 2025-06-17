import logging
import sys
import argparse
from datetime import datetime, timedelta
from typing import Optional

from src.config import get_config
from src.etappen import lade_heutige_etappe
from src.weather.api import WeatherAPIClient
from src.weather.aggregator import WeatherAggregator
from src.weather.models import StageWeather, WeatherData, ReportMode
from src.report.generator import ReportGenerator
from src.email import sende_email

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

def main():
    """Hauptfunktion"""
    # Kommandozeilenargumente parsen
    args = parse_args()
    
    # Modus in Enum konvertieren
    mode = ReportMode(args.modus)
    
    try:
        # Konfiguration laden
        config = get_config()
        logger.info(f"Starte im {mode.value}-Modus")
        
        # Etappe laden
        etappe = lade_heutige_etappe(config)
        logger.info(f"Lade Etappe: {etappe['name']}")
        
        # API-Client initialisieren
        api_client = WeatherAPIClient()
        
        # Zeiträume für Wetterdaten bestimmen
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        day_after_start = tomorrow_start + timedelta(days=1)
        
        # Wetterdaten holen
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
                now,
                weather
            )
        elif mode == ReportMode.MORNING:
            report = aggregator.aggregate_morning_report(
                etappe["name"],
                now,
                weather
            )
        else:  # ReportMode.DAY
            report = aggregator.aggregate_day_warning(
                etappe["name"],
                now,
                weather
            )
            if not report:  # Keine Warnung nötig
                logger.info("Keine Tageswarnung nötig")
                return
        
        # Report-Text generieren
        report.text = report_generator.generate_report(report)
        
        if args.dry_run:
            print("\n=== Wetterbericht (nur Ausgabe, keine E-Mail) ===\n")
            print(report.text)
            print("\n=== Ende Bericht ===\n")
        else:
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