import yaml

def generiere_wetterbericht(etappenname, berichte):
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    regen_schwelle = config["schwellen"]["regen"]
    max_risiko = max(b["regen"] for b in berichte)
    max_menge = max(b["menge"] for b in berichte)

    text = f"{etappenname}\nRegenrisiko: {max_risiko}% – {max_menge:.1f} mm"
    if max_risiko >= regen_schwelle:
        text += "\n⚠️ Regenwarnung empfohlen"
    return text