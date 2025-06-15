def generiere_kurznachricht(config, etappenname, daten):
    subject = config.get("smtp", {}).get("subject", "Wetterwarnung")
    text = f"🏔️ {etappenname}"
    if daten.get("nachttemperatur") is not None:
        text += f" 🌙 {daten['nachttemperatur']:.1f}°C"
    if daten.get("hitze") is not None:
        text += f" 🌡️ {daten['hitze']:.1f}°C"
    if daten.get("regen") is not None:
        text += f" 🌧️ {daten['regen']}%"
    if daten.get("gewitter") is not None:
        text += f" ⛈️ {daten['gewitter']}%"
    if daten.get("wind") is not None:
        text += f" 💨 {daten['wind']} km/h"
    result = f"{subject}: {text}"
    return result[:157] + "..." if len(result) > 160 else result
