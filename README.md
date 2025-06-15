# hiking-weather-email-bot

Tägliches Wetterskript für GR20 oder ähnliche Trekkingtouren.

## Setup

1. Python 3 venv
2. `pip install -r requirements.txt`
3. `.env` mit SMTP_PASS erstellen
4. `config.yaml` + `etappen.py` anpassen
5. `python main.py` starten

## Geplant
- `abend`, `morgen`, `delta`-Modi
- Vergleich mit Vortag
- Versand an Garmin-inReach via E-Mail
