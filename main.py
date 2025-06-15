from wetter.fetch import hole_wetterdaten
from wetter.analyse import generiere_wetterbericht
from wetter.notify import sende_email
from etappen import ETAPPEN
import datetime
import sys
import os

modus = "abend"
dry_run = False

for arg in sys.argv[1:]:
    if arg.startswith("--modus="):
        modus = arg.split("=", 1)[1]
    elif arg == "--dry-run":
        dry_run = True

heute = datetime.date.today()
tag_index = (heute - datetime.date(2025, 7, 1)).days

if tag_index < 0 or tag_index >= len(ETAPPEN):
    print("Kein gültiger Etappentag")
    sys.exit(0)

etappe = ETAPPEN[tag_index]
bericht = ""

if modus == "abend":
    heute_daten = hole_wetterdaten(etappe["punkte"], tag="heute")
    morgen_daten = hole_wetterdaten(ETAPPEN[tag_index + 1]["punkte"], tag="morgen") if tag_index + 1 < len(ETAPPEN) else None

    if morgen_daten:
        bericht += generiere_wetterbericht(ETAPPEN[tag_index + 1]["name"], morgen_daten) + "\n\n"
    bericht += generiere_wetterbericht(etappe["name"] + " (Nacht)", heute_daten)

elif modus == "tag":
    heute_daten_alt = hole_wetterdaten(etappe["punkte"], tag="morgen")  # was morgens bekannt war
    aktuell_daten = hole_wetterdaten(etappe["punkte"], tag="heute")

    delta_gewitter = aktuell_daten["gewitter"] - heute_daten_alt["gewitter"]
    delta_regen = aktuell_daten["regen"] - heute_daten_alt["regen"]

    delta_prozent = max(
        abs(delta_gewitter),
        abs(delta_regen)
    )

    if delta_prozent >= config["schwellen"]["delta_prozent"]:
        bericht = generiere_wetterbericht(etappe["name"], aktuell_daten)
    else:
        print("Keine signifikante Änderung. Keine Mail gesendet.")
        sys.exit(0)
else:
    print("Unbekannter Modus. Verwende --modus=abend oder --modus=tag")
    sys.exit(1)

print(bericht)
if not dry_run:
    sende_email(bericht)