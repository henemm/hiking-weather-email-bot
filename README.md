# Hiking Weather Email Bot

Ein Python-Bot, der Wetterwarnungen für Wanderungen per E-Mail versendet. Version 1.0

## Features

- **Wetterberichte** für verschiedene Modi:
  - Abend: Tageszusammenfassung mit Warnungen
  - Morgen: Vorhersage für den kommenden Tag
  - Tag: Delta-Warnungen bei Wetteränderungen

- **Delta-Warnungen** bei signifikanten Änderungen:
  - Regenrisiko
  - Gewitterwahrscheinlichkeit
  - Windgeschwindigkeit
  - Temperatur
  - Zeitverschiebungen bei Gewitterwarnungen

- **Konfigurierbare Schwellenwerte** für:
  - Regen (in %)
  - Gewitter (in %)
  - Wind (in km/h)
  - Hitze (in °C)
  - Delta-Prozent für Änderungswarnungen

## Installation

1. Repository klonen:
```bash
git clone https://github.com/henemm/hiking-weather-email-bot.git
cd hiking-weather-email-bot
```

2. Python-Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

3. Konfiguration anpassen:
   - `config.yaml` mit SMTP-Daten und Schwellenwerten
   - `.env` mit API-Keys und Passwörtern

## Konfiguration

### config.yaml
```yaml
startdatum: "2025-06-15"
smtp:
  host: smtp.gmail.com
  port: 587
  user: your.email@gmail.com
  to: recipient@example.com
  subject: Wetterwarnung GR20
schwellen:
  regen: 50
  gewitter: 30
  delta_prozent: 20
  hitze: 32
  wind: 40
```

### .env
```
GMAIL_APP_PW=your_app_password
WEATHER_API_KEY=your_api_key
```

## Verwendung

### Kommandozeilenargumente

```bash
python main.py --modus [abend|morgen|tag] [--inreach] [--dry-run]
```

- `--modus`: Art der Wettermeldung
  - `abend`: Tageszusammenfassung
  - `morgen`: Vorhersage für morgen
  - `tag`: Delta-Warnungen bei Änderungen
- `--inreach`: Kürzere Nachricht für InReach-Geräte
- `--dry-run`: Nur Ausgabe, kein E-Mail-Versand

### Testdaten

Für Tests können JSON-Dateien mit Wetterdaten verwendet werden:
```bash
python main.py --modus tag --input tests/testdaten_tag_delta.json
```

## Tests

Alle Tests ausführen:
```bash
python -m unittest discover tests
```

Spezifische Tests:
```bash
python -m unittest tests/test_app_outputs.py
python -m unittest tests/test_wetterdaten.py
python -m unittest tests/test_config.py
```

## Version 1.0

Die erste stabile Version enthält:
- Vollständige Testabdeckung
- Delta-Warnungen für Wetteränderungen
- Zeitverschiebungs-Warnungen für Gewitter
- Verbesserte Fehlerbehandlung
- Stabile Konfiguration

## Lizenz

MIT License

## Autor

Henning Emmrich

---

## ✅ Features

- **Modes**:
  - `abend` (evening): Forecast for the next day + perceived night temperature
  - `morgen` (morning): Forecast for the current day (no night temp)
  - `tag` (day): Compares morning and current forecast → sends alert if significant change
- **InReach mode**: Message shortened to 160 characters
- **Thresholds**: Fully configurable via `config.yaml`
- **Test data support** for development and simulation

---

## 📦 Installation

```bash
git clone <REPO-URL>
cd hiking-weather-email-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### `config.yaml`

```yaml
startdatum: "2025-07-01"
smtp:
  host: smtp.gmail.com
  port: 587
  user: name@example.com
  to: target@example.com
  subject: GR20 Weather Alert
schwellen:
  regen: 50
  gewitter: 30
  delta_prozent: 20
  hitze: 32
  wind: 40
  gewitter_ab_uhrzeit: 12
```

### `.env`

```env
GMAIL_USER=name@example.com
GMAIL_TO=target@example.com
GMAIL_APP_PW=<your app password>
```

---

## 🚀 Usage

```bash
python main.py --modus abend --dry-run
python main.py --modus morgen --dry-run
python main.py --modus tag --dry-run
python main.py --modus abend --inreach --dry-run
```

> Without `--dry-run`, a real email will be sent.

---

## 🧪 Testing

```bash
python tests/test_runner.py
```

Test files are located in `tests/testdaten_*.json`.

---

## 📆 Automation Example (Cron)

```cron
0 6 * * * /bin/bash -c 'cd /opt/hiking-weather-email-bot && source venv/bin/activate && python main.py --modus abend'
```

---

## 🔒 Notes

- Gmail requires an [App Password](https://support.google.com/accounts/answer/185833)
- Ensure your system has internet access for API use
- Works offline with pre-generated test data

---

## 📁 Structure Overview

```
hiking-weather-email-bot/
├── main.py
├── config.py
├── config.yaml
├── wetter/
│   ├── analyse.py
│   ├── fetch.py
│   └── kurztext.py
├── sende/
│   └── mail.py
├── etappen.py
├── etappenliste.py
├── tests/
│   ├── test_runner.py
│   ├── testdaten_abend.json
│   └── ...
```

---

## 👣 Created for long-distance trekking on the GR20 (Corsica) – works worldwide 🌍
