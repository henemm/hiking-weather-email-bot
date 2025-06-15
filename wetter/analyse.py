def generiere_wetterbericht(etappenname, daten, schwellen, modus):
    lines = [f"🏔️ Etappe: {etappenname}"]

    if modus == "abend":
        if "nacht" in daten and "gefuehlt" in daten["nacht"]:
            lines.append(f"🌙 Gefühlte Nachttemperatur: {daten['nacht']['gefuehlt']} °C")

    if "regen" in daten:
        regen = daten["regen"]
        if regen.get("wert", 0) >= schwellen.get("regen", 50):
            zeile = f"🌧️ Regenrisiko: {regen['wert']} %"
            if "zeit" in regen:
                zeile += f" ab {regen['zeit']} Uhr"
            zeile += f" ({regen.get('menge', '?')} mm)"
            lines.append(zeile)

    if "gewitter" in daten:
        gewitter = daten["gewitter"]
        if gewitter.get("wert", 0) >= schwellen.get("gewitter", 30):
            zeile = f"🌩️ Gewitterrisiko: {gewitter['wert']} %"
            if "zeit" in gewitter:
                zeile += f" ab {gewitter['zeit']} Uhr"
            lines.append(zeile)

    if "hitze" in daten:
        hitze = daten["hitze"]
        if hitze.get("wert", 0) >= schwellen.get("hitze", 32):
            lines.append(f"🌡️ Gefühlte Tageshitze: {hitze['wert']} °C")

    if "wind" in daten:
        wind = daten["wind"]
        if wind.get("wert", 0) >= schwellen.get("wind", 40):
            lines.append(f"💨 Max. Windgeschwindigkeit: {wind['wert']} km/h")

    if not lines:
        return "Keine relevanten Wetterinformationen verfügbar."

    return "\n".join(lines)