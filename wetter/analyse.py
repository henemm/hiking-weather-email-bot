def generiere_wetterbericht(etappenname, daten, schwellen, modus):
    text = f"🏔️ Etappe: {etappenname}"
    if modus == "abend" and daten.get("nachttemperatur") is not None:
        text += f"\n🌙 Gefühlte Nachttemperatur: {daten['nachttemperatur']:.1f} °C"
    if "hitze" in daten:
        text += f"\n🌡️ Gefühlte Tageshitze: {daten['hitze']:.1f} °C"
    if "regen" in daten and daten["regen"] >= schwellen["regen"]:
        text += f"\n🌧️ Regenrisiko: {daten['regen']}%"
    if "wind" in daten and daten["wind"] >= schwellen["wind"]:
        text += f"\n💨 Wind: {daten['wind']} km/h"
    if "gewitter" in daten and daten["gewitter"] >= schwellen["gewitter"]:
        text += f"\n⛈️ Gewitterrisiko: {daten['gewitter']}%"
    return text
