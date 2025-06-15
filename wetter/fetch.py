import requests
import datetime
from wetter.util import extrahiere_zeitpunkt_mit_schwelle
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

SCHWELLEN = config["schwellen"]

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

FELDER_DAILY = [
    "precipitation_probability_max",
    "showers_sum",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "windspeed_10m_max",
    "thunderstorm_probability",
]
FELDER_HOURLY = ["thunderstorm_probability"]


# Gibt Datumsliste für heute und morgen zurück
def datumsliste():
    heute = datetime.date.today()
    morgen = heute + datetime.timedelta(days=1)
    return heute.isoformat(), morgen.isoformat()


def hole_wetterdaten(punkte, tag="heute"):
    heute, morgen = datumsliste()
    ziel_datum = heute if tag == "heute" else morgen

    forecasts = []
    for lat, lon in punkte:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(FELDER_DAILY),
            "hourly": ",".join(FELDER_HOURLY),
            "timezone": "Europe/Paris",
        }
        r = requests.get(OPEN_METEO_URL, params=params)
        data = r.json()

        if "daily" not in data or "hourly" not in data:
            raise ValueError(f"Ungültige API-Antwort für Punkt {lat}, {lon}: {data}")

        if ziel_datum not in data["daily"]["time"]:
            raise ValueError(f"Datum {ziel_datum} nicht in daily-Zeitraum enthalten: {data['daily']['time']}")

        i = data["daily"]["time"].index(ziel_datum)

        forecast = {
            "regen": data["daily"]["precipitation_probability_max"][i],
            "menge": data["daily"]["showers_sum"][i],
            "hitze": data["daily"]["apparent_temperature_max"][i],
            "nacht": data["daily"]["apparent_temperature_min"][i],
            "wind": data["daily"]["windspeed_10m_max"][i],
            "gewitter": data["daily"].get("thunderstorm_probability", [0])[i],
            "gewitter_ab": extrahiere_zeitpunkt_mit_schwelle(
                data["hourly"]["time"],
                data["hourly"]["thunderstorm_probability"],
                ziel_datum,
                SCHWELLEN["gewitter"]
            )
        }
        forecasts.append(forecast)

    # Aggregation (Worst Case)
    return {
        "regen": max(f["regen"] for f in forecasts),
        "menge": max(f["menge"] for f in forecasts),
        "hitze": max(f["hitze"] for f in forecasts),
        "nacht": forecasts[-1]["nacht"],  # nur letzter Punkt relevant
        "wind": max(f["wind"] for f in forecasts),
        "gewitter": max(f["gewitter"] for f in forecasts),
        "gewitter_ab": min(f["gewitter_ab"] for f in forecasts if f["gewitter_ab"] is not None) if any(f["gewitter_ab"] for f in forecasts) else None
    }