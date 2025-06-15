from wetter.fetch import hole_wetterdaten
from wetter.analyse import generiere_wetterbericht
from wetter.notify import sende_email
from etappen import ETAPPEN
import datetime

modus = "abend"  # hartkodiert für MVP
heute = datetime.date.today()
etappe = ETAPPEN[(heute - datetime.date(2025, 7, 1)).days % len(ETAPPEN)]

berichte = hole_wetterdaten(etappe["punkte"])
text = generiere_wetterbericht(etappe["name"], berichte)

print(text)
sende_email(text)
