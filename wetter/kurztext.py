def generiere_kurznachricht(config, etappenname, daten):
    subject = config.get("smtp", {}).get("subject", "Wetterwarnung")

    nacht = daten.get("nacht", {})
    tag = daten.get("tag", {})

    teile = [f"🏔️ {etappenname}"]

    if nacht.get("gefuehlt") is not None:
        teile.append(f"🌙 {nacht['gefuehlt']} °C")

    if tag.get("regen_prozent") and tag["regen_prozent"] >= config["schwellen"].get("regen", 0):
        zeit = tag.get("regen_ab")
        emoji = "🌧️"
        teile.append(f"{emoji} {tag['regen_prozent']} %{f' ab {zeit}h' if zeit else ''}")

    if tag.get("gewitter_prozent") and tag["gewitter_prozent"] >= config["schwellen"].get("gewitter", 0):
        zeit = tag.get("gewitter_ab")
        emoji = "⛈️"
        teile.append(f"{emoji} {tag['gewitter_prozent']} %{f' ab {zeit}h' if zeit else ''}")

    if tag.get("gefuehlt_max") and tag["gefuehlt_max"] >= config["schwellen"].get("hitze", 32):
        teile.append(f"🌡️ {tag['gefuehlt_max']} °C")

    if tag.get("wind_max") and tag["wind_max"] >= config["schwellen"].get("wind", 40):
        teile.append(f"💨 {tag['wind_max']} km/h")

    nachricht = f"{subject}: " + " ".join(teile)

    if len(nachricht) > 160:
        nachricht = nachricht[:157] + "..."

    return nachricht