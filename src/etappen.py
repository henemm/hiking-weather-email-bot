import datetime
import json
from typing import Dict, Any, Optional


def lade_etappen(pfad: str = "etappen.json") -> Dict[str, Any]:
    """Lädt die Etappendaten aus der JSON-Datei."""
    with open(pfad, "r") as f:
        return json.load(f)


def lade_heutige_etappe(config: Dict[str, Any]) -> Dict[str, Any]:
    """Lädt die aktuelle Etappe basierend auf dem Startdatum."""
    etappen = lade_etappen()
    # Konvertiere das Startdatum von String zu datetime.date
    startdatum_str = config["startdatum"]
    if isinstance(startdatum_str, datetime.date):
        startdatum = startdatum_str
    else:
        try:
            startdatum = datetime.datetime.strptime(startdatum_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Ungültiges Startdatum-Format: {startdatum_str}. Erwartet wird YYYY-MM-DD.")
        
    heute = datetime.date.today()
    differenz = (heute - startdatum).days

    if differenz < 0 or differenz >= len(etappen):
        raise ValueError("Kein gültiger Etappentag – liegt außerhalb des definierten Zeitraums.")

    return etappen[differenz]