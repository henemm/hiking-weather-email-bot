import requests
import datetime

def hole_wetterdaten(punkte, modus):
    ziel_datum = datetime.date.today() if modus != "abend" else datetime.date.today() + datetime.timedelta(days=1)
    daten = {"nachttemperatur": None, "hitze": None, "regen": None, "wind": None, "gewitter": None}
    for punkt in punkte:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={punkt['lat']}&longitude={punkt['lon']}"
            f"&daily=apparent_temperature_max,apparent_temperature_min,precipitation_probability_max,"
            f"wind_speed_10m_max,thunderstorm_probability&timezone=auto"
        )
        r = requests.get(url).json()
        try:
            i = r["daily"]["time"].index(ziel_datum.isoformat())
            daten["hitze"] = max(daten["hitze"] or 0, r["daily"]["apparent_temperature_max"][i])
            daten["regen"] = max(daten["regen"] or 0, r["daily"]["precipitation_probability_max"][i])
            daten["wind"] = max(daten["wind"] or 0, r["daily"]["wind_speed_10m_max"][i])
            daten["gewitter"] = max(daten["gewitter"] or 0, r["daily"]["thunderstorm_probability"][i])
            if modus == "abend":
                daten["nachttemperatur"] = r["daily"]["apparent_temperature_min"][i]
        except:
            continue
    return daten
