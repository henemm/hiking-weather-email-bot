# Hiking Weather Email Bot

Ein Bot, der tägliche Wetterberichte für eine Wanderung per E-Mail versendet.

## Logik

### Berichtsmodi

Der Bot arbeitet in drei Modi, die durch die Tageszeit bestimmt werden:

- **Abendbericht** (18:00-23:59):
  - Nachttemperatur: Temperatur am letzten Punkt der heutigen Etappe
  - Alle anderen Risiken: Maximum über alle Punkte der morgigen Etappe
  - Gewitter +1: Maximum über alle Punkte der übermorgigen Etappe

- **Morgenbericht** (06:00-11:59):
  - Alle Risiken: Maximum über alle Punkte der heutigen Etappe
  - Gewitter +1: Maximum über alle Punkte der morgigen Etappe
  - Keine Nachttemperatur

- **Tageswarnung** (00:00-05:59, 12:00-17:59):
  - Nur bei signifikanter Verschlechterung
  - Alle Risiken: Maximum über alle Punkte der heutigen Etappe
  - Keine Vorhersage für morgen

### Risikobewertung

Die Risiken werden basierend auf Schwellenwerten bewertet:

```yaml
schwellen:
  regen: 5.0      # mm
  gewitter: 30.0  # %
  hitze: 30.0     # °C
  wind: 30.0      # km/h
```

Die Risikostufen werden wie folgt bestimmt:
- **Niedrig**: Wert unter Schwellenwert
- **Mittel**: Wert über Schwellenwert
- **Hoch**: Wert über 1.5 × Schwellenwert

Beispiele:
- Regen: 3mm → niedrig (unter 5mm)
- Regen: 6mm → mittel (über 5mm)
- Regen: 8mm → hoch (über 7.5mm)

### Datenaggregation

1. **Nachttemperatur:**
   - Wird nur im Abendbericht angezeigt
   - Stammt vom letzten Punkt der heutigen Etappe
   - Keine Aggregation (Minimum/Maximum) über alle Punkte
   - Beispiel: Wenn die Etappe 5 Punkte hat, wird nur die Temperatur des 5. Punktes verwendet

2. **Risiken (Regen, Gewitter, Wind, Hitze):**
   - Maximum über alle Punkte der relevanten Etappe
   - Gewitterwahrscheinlichkeit kann `None` sein
   - Gefühlte Temperatur für Hitze-Bewertung
   - Beispiel: Wenn die Etappe 5 Punkte hat mit Regenwerten [2mm, 5mm, 3mm, 7mm, 4mm], wird 7mm verwendet

3. **Gewitter +1:**
   - Im Abendbericht: Maximum über alle Punkte der übermorgigen Etappe
   - Im Morgenbericht: Maximum über alle Punkte der morgigen Etappe
   - In Tageswarnung: Nicht relevant
   - Beispiel: Wenn morgen 3 Punkte mit Gewitterwahrscheinlichkeiten [20%, 35%, 25%], wird 35% verwendet

### Berichtsformat

1. **Abendbericht:**
```
Wetterbericht für [Etappe] am [Datum]

Nachttemperatur:
  [Temperatur]°C

Risiken für morgen:
  Regen: [Risiko] ([Wert]mm)
  Gewitter: [Risiko] ([Wert]%)
  Wind: [Risiko] ([Wert]km/h)
  Hitze: [Risiko] ([Wert]°C)

Gewitterwahrscheinlichkeit für übermorgen:
  [Wert]%
```

Beispiel:
```
Wetterbericht für Etappe 1 am 20.03.2024

Nachttemperatur:
  12.5°C

Risiken für morgen:
  Regen: mittel (6.2mm)
  Gewitter: hoch (45%)
  Wind: niedrig (25km/h)
  Hitze: mittel (32°C)

Gewitterwahrscheinlichkeit für übermorgen:
  30%
```

2. **Morgenbericht:**
```
Wetterbericht für [Etappe] am [Datum]

Risiken für heute:
  Regen: [Risiko] ([Wert]mm)
  Gewitter: [Risiko] ([Wert]%)
  Wind: [Risiko] ([Wert]km/h)
  Hitze: [Risiko] ([Wert]°C)

Gewitterwahrscheinlichkeit für morgen:
  [Wert]%
```

Beispiel:
```
Wetterbericht für Etappe 1 am 20.03.2024

Risiken für heute:
  Regen: niedrig (3.5mm)
  Gewitter: mittel (35%)
  Wind: hoch (48km/h)
  Hitze: niedrig (28°C)

Gewitterwahrscheinlichkeit für morgen:
  20%
```

3. **Tageswarnung:**
```
⚠️ Wetterwarnung für [Etappe] am [Datum]

Signifikante Verschlechterung:
  [Betroffene Risiken mit Werten]
```

Beispiel:
```
⚠️ Wetterwarnung für Etappe 1 am 20.03.2024

Signifikante Verschlechterung:
  Regen: 8.5mm
  Gewitter: 45%
  Wind: 35km/h
```

## Technische Details

### Datenmodelle

- `WeatherPoint`: Einzelner Wettermesspunkt
  ```python
  @dataclass
  class WeatherPoint:
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
  ```

- `WeatherData`: Wetterdaten für einen Zeitraum
  ```python
  @dataclass
  class WeatherData:
      points: List[WeatherPoint]
  ```

- `StageWeather`: Wetterdaten für eine Etappe
  ```python
  @dataclass
  class StageWeather:
      today: WeatherData
      tomorrow: Optional[WeatherData]
      day_after_tomorrow: Optional[WeatherData]
  ```

- `WeatherReport`: Generierter Wetterbericht
  ```python
  @dataclass
  class WeatherReport:
      mode: ReportMode
      stage_name: str
      date: datetime
      night_temperature: Optional[float]
      max_temperature: float
      max_feels_like: float
      max_precipitation: float
      max_thunderstorm_probability: Optional[float]
      max_wind_speed: float
      max_cloud_cover: float
      next_day_thunderstorm: Optional[float]
      text: str
  ```

### API-Integration

- Verwendet die Open-Meteo API
- Holt stündliche Wetterdaten
- Berücksichtigt Höhenlage der Etappenpunkte
- API-Endpunkt: `https://api.open-meteo.com/v1/forecast`
- Parameter:
  - `latitude`, `longitude`, `elevation`
  - `hourly`: temperature_2m, apparent_temperature, precipitation, thunderstorm_probability, windspeed_10m, winddirection_10m, cloudcover
  - `timezone`: auto
  - `start_date`, `end_date`: YYYY-MM-DD

### Fehlerbehandlung

- Robuste Fehlerbehandlung für API-Aufrufe
  - `WeatherAPIError`: Basis-Exception
  - `WeatherAPIRequestError`: Fehler bei der API-Anfrage
  - `WeatherAPIParseError`: Fehler beim Parsen der Antwort
- Logging für Debugging
  - Datei: `logs/hiking-weather-bot.log`
  - Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Klare Fehlermeldungen
- Keine stillen Fehler

## Konfiguration

Die Konfiguration erfolgt über `config.yaml`:

```yaml
startdatum: "2024-03-20"  # YYYY-MM-DD

schwellen:
  regen: 5.0
  gewitter: 30.0
  hitze: 30.0
  wind: 30.0

smtp:
  host: "smtp.gmail.com"
  port: 587
  user: "your-email@gmail.com"
  to: "recipient@example.com"
  subject: "Wetterbericht"
```

## Installation

1. Repository klonen
2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
4. `.env` Datei erstellen:
   ```
   GMAIL_APP_PW=your-app-password
   ```

## Verwendung

```bash
python -m src.main
```

Der Bot wird automatisch den passenden Modus basierend auf der Tageszeit wählen.

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
GMAIL_USER=name@example.com
GMAIL_TO=target@example.com
GMAIL_APP_PW=<your app password>
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

# Wetterbericht-Modi Übersicht

Diese Datei beschreibt, welche Wetterdaten im jeweiligen Modus verwendet werden und von welchen Etappenpunkten sie berechnet werden.

---

## 🕖 1. Abendmodus (`--modus abend`)

| Faktor                     | Quelle                                          | Beschreibung                                                                 |
|---------------------------|--------------------------------------------------|------------------------------------------------------------------------------|
| 🌙 Gefühlte Nachttemperatur | Letzter Punkt der **heutigen** Etappe           | Wie kalt es nachts am Schlafplatz wird                                      |
| 🌡️ Gefühlte Tageshitze     | Alle Punkte der **morgigen** Etappe             | Max. gefühlte Temperatur am nächsten Tag                                    |
| 🌧️ Regenrisiko             | Alle Punkte der **morgigen** Etappe             | Regenrisiko mit Zeitpunkt (z. B. `15%@10(45%@15)`)                           |
| 💨 Wind                    | Alle Punkte der **morgigen** Etappe             | Höchster Windwert                                                            |
| ⚡ Gewitterrisiko morgen   | Alle Punkte der **morgigen** Etappe             | Gewitterrisiko mit Zeitpunkt (z. B. `20%@11(50%@16)`)                        |
| ➤⚡ Gewitterrisiko übermorgen | Alle Punkte der **übernächsten** Etappe      | Früher Zeitpunkt & Max-Wert mit Uhrzeit                                     |

---

## 🌅 2. Morgenmodus (`--modus morgen`)

| Faktor                     | Quelle                                          | Beschreibung                                                                 |
|---------------------------|--------------------------------------------------|------------------------------------------------------------------------------|
| 🌡️ Gefühlte Tageshitze     | Alle Punkte der **heutigen** Etappe             | Max. gefühlte Temperatur des Tages                                           |
| 🌧️ Regenrisiko             | Alle Punkte der **heutigen** Etappe             | Regenrisiko mit Zeitpunkt                                                    |
| 💨 Wind                    | Alle Punkte der **heutigen** Etappe             | Höchster Windwert                                                            |
| ⚡ Gewitterrisiko heute    | Alle Punkte der **heutigen** Etappe             | Gewitterrisiko mit Uhrzeit                                                   |
| ➤⚡ Gewitterrisiko morgen  | Alle Punkte der **morgigen** Etappe             | Gewitterrisiko mit Uhrzeit                                                   |

> **Hinweis:** Keine Nachttemperatur, da vergangen.

---

## 🌩 3. Tageswarnung (`--modus tag`)

| Faktor                     | Quelle                                          | Beschreibung                                                                 |
|---------------------------|--------------------------------------------------|------------------------------------------------------------------------------|
| 🌡️ Gefühlte Tageshitze     | Alle Punkte der **heutigen** Etappe             | Wenn aktueller Wert über Schwelle gestiegen                                 |
| 🌧️ Regenrisiko             | Alle Punkte der **heutigen** Etappe             | Wenn aktueller Wert höher als morgens, inkl. Zeitpunkt                       |
| 💨 Wind                    | Alle Punkte der **heutigen** Etappe             | Wenn aktueller Wert höher als morgens                                        |
| ⚡ Gewitterrisiko          | Alle Punkte der **heutigen** Etappe             | Wenn Schwellwert überschritten oder stärker als morgens                      |

> Diese Warnung wird **nur bei signifikanter Verschlechterung** gesendet.

---

## 🔍 Beispiele

### Abendmodus – Langtext

```
Etappe: Haut Asco → Ballone  
🌙 Gefühlte Nachttemperatur: 13.7 °C  
🌡️ Gefühlte Tageshitze morgen: 32.5 °C  
🌧️ Regenrisiko: 15%@10(45%@15)  
💨 Wind: 35 km/h  
⚡ Gewitterrisiko morgen: 20%@11(50%@16)  
➤⚡ Gewitterrisiko übermorgen: 30%@12(60%@14)
```

### Abendmodus – InReach kompakt

```
Asco→Ballone | Nacht 13.7°C | Tag 32.5°C | Regen 15%@10(45%@15) | Wind 35km/h | Gewitter 20%@11(50%@16) ➤ 30%@12(60%@14)
```

---

### Morgenmodus – Langtext

```
Etappe: Ballone → Manganu  
🌡️ Gefühlte Tageshitze: 28.9 °C  
🌧️ Regenrisiko: 10%@13(55%@17)  
💨 Wind: 28 km/h  
⚡ Gewitterrisiko heute: 15%@14(60%@16)  
➤⚡ Gewitterrisiko morgen: 20%@10(35%@15)
```

### Morgenmodus – InReach kompakt

```
Ballone→Manganu | Tag 28.9°C | Regen 10%@13(55%@17) | Wind 28km/h | Gewitter 15%@14(60%@16) ➤ 20%@10(35%@15)
```

---

### Tageswarnung – Langtext

```
⚠️ Wetterwarnung – Etappe: Manganu → Petra Piana  
🌡️ Neue Tageshitze: 34.1 °C  
🌧️ Regen gestiegen: 20%@11(50%@15)  
💨 Wind gestiegen: 42 km/h  
⚡ Gewitterrisiko gestiegen: 30%@13(65%@16)
```

### Tageswarnung – InReach kompakt

```
Manganu→Petra Piana | Tag 34.1°C | Regen 20%@11(50%@15) | Wind 42km/h | Gewitter 30%@13(65%@16)
```

> **Hinweis zu Schwellenwerten:** Für Zeitangaben (z.B. ab wann Regen oder Gewitter) wird **immer der Schwellwert aus der Konfiguration (`config.yaml`, Bereich `Schwellen`) verwendet**. Es wird der erste Zeitpunkt ausgegeben, an dem dieser Schwellwert überschritten wird, sowie der Zeitpunkt mit dem Maximalwert.

---

## 🌤️ Referenztabelle: Wetterfaktoren & Open-Meteo-API-Felder

| Projektbegriff                | Open-Meteo-API Feld (daily/hourly)         | Aggregation/Logik im Projekt                        | Bemerkung                                  |
|-------------------------------|--------------------------------------------|-----------------------------------------------------|---------------------------------------------|
| **Gefühlte Nachttemperatur** | `apparent_temperature_min` (daily)         | Minimum über die ganze Nacht am letzten Punkt der Etappe (Schlafplatz), Element `[0]` (heute) | Nur im Abendbericht relevant |
| **Gefühlte Tageshitze**      | `apparent_temperature_max` (daily)         | Maximum über alle Punkte der Etappe, Element `[1]` (morgen) im Abendbericht, `[0]` (heute) in anderen Modi | |
| **Regenrisiko**              | `precipitation_probability_max` (daily)    | Maximum über alle Punkte der Etappe, Element `[1]` (morgen) im Abendbericht, `[0]` (heute) in anderen Modi | |
| **Windrisiko**               | `wind_speed_10m_max` (daily)              | Maximum über alle Punkte der Etappe, Element `[1]` (morgen) im Abendbericht, `[0]` (heute) in anderen Modi | |
| **Gewitterrisiko**           | `thunderstorm_probability_max` (daily)     | Maximum über alle Punkte der Etappe, Element `[1]` (morgen) im Abendbericht, `[0]` (heute) in anderen Modi | |
| **Gewitter +1**              | `thunderstorm_probability_max` (daily)     | Maximum über alle Punkte der Etappe, Element `[2]` (übermorgen) im Abendbericht, `[1]` (morgen) in anderen Modi | |
| **Zeitpunkt Regen/Gewitter**  | `precipitation_probability`/`thunderstorm_probability` (hourly) | Zeitpunkt, an dem der Wert den **Schwellwert** aus der Konfiguration überschreitet; zusätzlich Zeitpunkt des Maximums | Schwellenwert aus `config.yaml`             |

> **Wichtig:** Die Nachttemperatur im Abendreport ist **die minimale Temperatur über die ganze Nacht am letzten Punkt der heutigen Etappe (Schlafplatz)**. Es wird also nicht über mehrere Punkte aggregiert, sondern gezielt der Schlafplatz betrachtet.
