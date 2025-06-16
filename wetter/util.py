import json
import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


def extrahiere_zeitpunkt_mit_schwelle(times, values, datum, schwelle):
    for t, v in zip(times, values):
        if not t.startswith(datum):
            continue
        if v >= schwelle:
            try:
                return datetime.fromisoformat(t).strftime("%H:%M")
            except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
                continue
    return None


def lade_heutige_etappe() -> Dict[str, Any]:
    """Lädt die heutige Etappe aus der JSON-Datei."""
    try:
        with open("etappen.json", "r", encoding="utf-8") as f:
            etappen = json.load(f)
        heute = datetime.now().date()
        for etappe in etappen:
            start = datetime.strptime(etappe["start"], "%Y-%m-%d").date()
            ende = datetime.strptime(etappe["ende"], "%Y-%m-%d").date()
            if start <= heute <= ende:
                return etappe
        raise ValueError("Keine Etappe für heute gefunden")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Fehler beim Laden der Etappendaten: {str(e)}")


def format_zeit(zeit: str) -> str:
    """
    Formatiert einen Zeitstempel in ein lesbares Format.

    Args:
        zeit: Zeitstempel im ISO-Format

    Returns:
        Formatierter Zeitstring
    """
    try:
        dt = datetime.fromisoformat(zeit.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return zeit


def lade_config() -> Dict[str, Any]:
    """Lädt die Konfiguration aus der JSON-Datei."""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ValueError(f"Fehler beim Laden der Konfiguration: {str(e)}")
