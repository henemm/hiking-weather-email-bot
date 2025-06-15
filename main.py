import argparse
import datetime
from config import config
from wetter.fetch import hole_wetterdaten
from wetter.analyse import generiere_wetterbericht
from wetter.kurztext import generiere_kurznachricht
from sende.mail import sende_email
import json

parser = argparse.ArgumentParser()
parser.add_argument("--modus", choices=["abend", "morgen", "tag"], required=True)
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--input", help="Pfad zur Testdatei im JSON-Format")
parser.add_argument("--inreach", action="store_true")
args = parser.parse_args()

if args.input:
    with open(args.input) as f:
        daten = json.load(f)
        etappe = daten["etappe"]
        wetter = daten["wetter"]
else:
    from etappen import lade_heutige_etappe
    etappe = lade_heutige_etappe(config)
    wetter = hole_wetterdaten(etappe["punkte"], args.modus)

bericht = generiere_wetterbericht(etappe["name"], wetter, config["schwellen"], args.modus)

if args.inreach:
    bericht = generiere_kurznachricht(config, etappe["name"], wetter)

print(bericht)
if not args.dry_run:
    sende_email(bericht)
