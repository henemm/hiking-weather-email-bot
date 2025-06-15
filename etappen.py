import datetime
from config import config
from etappenliste import ETAPPEN

def lade_heutige_etappe(config):
    heute = datetime.date.today()
    startdatum = datetime.date.fromisoformat(config["startdatum"])
    delta = (heute - startdatum).days
    if 0 <= delta < len(ETAPPEN):
        return ETAPPEN[delta]
    raise ValueError("Kein gültiger Etappentag")
