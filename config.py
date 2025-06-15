import yaml
import datetime

def lade_config(pfad="config.yaml"):
    with open(pfad, "r") as f:
        return yaml.safe_load(f)

config = lade_config()

if not isinstance(config.get("startdatum"), str):
    raise ValueError("Startdatum fehlt oder ist kein gültiges Datum.")

if "smtp" not in config or not config["smtp"].get("user"):
    raise ValueError("SMTP-Konfiguration unvollständig.")
