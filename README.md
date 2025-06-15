# hiking-weather-email-bot

Ein leichtgewichtiges Python-Skript, das tägliche Wetterwarnungen für Trekking-Etappen generiert (z. B. GR20) und sie per E-Mail versendet – z. B. an ein Garmin inReach.

## ✅ Features

- Abfrage mehrerer Koordinaten pro Etappe via Open-Meteo
- Bewertung auf Basis von Schwellenwerten (Regen, Gewitter)
- Versand per SMTP an E-Mail-Empfänger
- Modularer Aufbau (fetch, analyse, notify)
- Konfigurierbar über YAML & .env-Datei
- Vorbereitbar für automatische Ausführung via cron oder systemd

## 🚀 Setup

### 1. Klonen & installieren

```bash
git clone https://github.com/henemm/hiking-weather-email-bot.git
cd hiking-weather-email-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt