import yaml
from datetime import datetime

with open("config.yaml") as f:
    config = yaml.safe_load(f)

SCHWELLEN = config["schwellen"]


def generiere_wetterbericht(name, daten):
    teile = [f"🏔️ Etappe: {name}"]

    if daten.get("nacht") is not None:
        teile.append(f"🌙 Gefühlte Nachttemperatur: {daten['nacht']} °C")

    teile.append(f"🌧️ Regenrisiko: {daten['regen']} % ({daten['menge']} mm)")
    teile.append(f"🌡️ Gefühlte Tageshitze: {daten['hitze']} °C")
    teile.append(f"💨 Max. Windgeschwindigkeit: {daten['wind']} km/h")

    if daten["gewitter"] >= SCHWELLEN["gewitter"]:
        uhrzeit = daten.get("gewitter_ab")
        zeitinfo = f" ab {uhrzeit}" if uhrzeit else ""
        teile.append(f"⛈️ Gewitterrisiko: {daten['gewitter']} %{zeitinfo}")

    warnungen = []
    if daten["regen"] >= SCHWELLEN["regen"]:
        warnungen.append("Regenwarnung")
    if daten["hitze"] >= SCHWELLEN["hitze"]:
        warnungen.append("Hitzewarnung")
    if daten["wind"] >= SCHWELLEN["wind"]:
        warnungen.append("Sturmwarnung")
    if daten["gewitter"] >= SCHWELLEN["gewitter"]:
        warnungen.append("Gewitterwarnung")

    if warnungen:
        teile.append("⚠️ WARNUNG: " + ", ".join(warnungen))

    return "\n".join(teile)