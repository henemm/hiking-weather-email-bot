import datetime
import json


def lade_etappen(pfad="etappen.json"):
    with open(pfad, "r") as f:
        return json.load(f)


def lade_heutige_etappe(config):
    etappen = lade_etappen()
    startdatum = config["startdatum"]
    heute = datetime.date.today()
    differenz = (heute - startdatum).days

    if differenz < 0 or differenz >= len(etappen):
        raise ValueError("Kein gültiger Etappentag – liegt außerhalb des definierten Zeitraums.")

    return etappen[differenz]