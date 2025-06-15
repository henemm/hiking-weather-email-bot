import sys
import argparse
import datetime
from wetter.fetch import hole_wetterdaten
from wetter.analyse import generiere_wetterbericht
from wetter.kurztext import generiere_kurznachricht
from wetter.notify import sende_email
from config import config
from etappen import ETAPPEN
import json

parser = argparse.ArgumentParser()
parser.add_argument("--modus", choices=["abend", "tag"], default="abend")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--input", help="Pfad zu Testdaten (JSON)")
parser.add_argument("--inreach", action="store_true")
args = parser.parse_args()

# Etappe bestimmen
heute = datetime.date.today()
startdatum_raw = config.get("startdatum")
if isinstance(startdatum_raw, str):
    startdatum = datetime.date.fromisoformat(startdatum_raw)
else:
    startdatum = startdatum_raw

etappen_index = (heute - startdatum).days
if etappen_index < 0 or etappen_index >= len(ETAPPEN):
    print("Kein gültiger Etappentag")
    sys.exit(1)

etappe = ETAPPEN[etappen_index]

# Wetterdaten laden
if args.input:
    with open(args.input) as f:
        daten = json.load(f)
else:
    daten = hole_wetterdaten(etappe["punkte"])

# Bericht erzeugen
bericht = generiere_wetterbericht(
    etappe["name"],
    daten,
    config.get("schwellen", {}),
    args.modus
)

# ggf. kürzen für inReach
if args.inreach:
    bericht = generiere_kurznachricht(config, etappe["name"], daten)

print(bericht)

if not args.dry_run:
    sende_email(bericht)