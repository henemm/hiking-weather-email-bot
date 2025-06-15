import requests

def hole_wetterdaten(punkte):
    ergebnisse = []
    for punkt in punkte:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={punkt['lat']}&longitude={punkt['lon']}&daily=precipitation_probability_max,showers_sum&timezone=Europe%2FParis"
        data = requests.get(url).json()
        tag = data["daily"]
        ergebnisse.append({
            "regen": tag["precipitation_probability_max"][0],
            "menge": tag["showers_sum"][0]
        })
    return ergebnisse
