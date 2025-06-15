import argparse
import datetime
import json
import logging
from pathlib import Path
import yaml

from wetter.fetch import hole_wetterdaten
from wetter.analyse import generiere_wetterbericht
from wetter.notify import sende_email
from wetter.delta import delta_warnung
from etappen import ETAPPEN

# ------------------------ Logging Setup ------------------------
logfile = Path("logs/wetter.log")
logfile.parent.mkdir(exist_ok=True)

logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ------------------------ Argumente parsen ------------------------
parser = argparse.ArgumentParser(description="Wetterbenachrichtigung GR20")
parser.add_argument("--modus", choices=["abend", "morgen", "test"], default="abend")
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

# ------------------------ Setup ------------------------
modus = args.modus
heute = datetime.date.today()
etappe = ETAPPEN[(heute - datetime.date(2025, 7, 1)).days % len(ETAPPEN)]
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
dateiname = data_dir / f"{heute}_{modus}.json"

# ------------------------ Config laden ------------------------
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# ------------------------ Wetterdaten abrufen ------------------------
berichte = hole_wetterdaten(etappe["punkte"])

# ------------------------ Modus: ABEND ------------------------
if modus == "abend":
    with open(dateiname, "w") as f:
        json.dump(berichte, f)

    text = generiere_wetterbericht(etappe["name"], berichte)
    if args.dry_run:
        print(text)
    else:
        sende_email(text)
        logging.info("Abendbericht gesendet.")

# ------------------------ Modus: MORGEN ------------------------
elif modus == "morgen":
    abend_datei = data_dir / f"{heute}_abend.json"
    if not abend_datei.exists():
        logging.warning("Keine Abendprognose vorhanden – kein Delta möglich.")
    else:
        with open(abend_datei) as f:
            abenddaten = json.load(f)

        warntext, kritisch = delta_warnung(abenddaten, berichte, config["schwellen"]["delta_prozent"], etappe["name"])

        if kritisch:
            if args.dry_run:
                print(warntext)
            else:
                sende_email(warntext)
                logging.info("Delta-Warnung gesendet.")
        else:
            logging.info("Keine signifikante Wetteränderung.")

# ------------------------ Modus: TEST ------------------------
else:
    text = generiere_wetterbericht(etappe["name"], berichte)
    print(text)