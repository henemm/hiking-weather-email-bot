# Hiking Weather Email Bot

Automated system for daily weather warnings via email or as a shortened InReach message – ideal for multi-day treks such as the GR20.

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
