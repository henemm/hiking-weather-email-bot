from datetime import datetime
from typing import Any, Dict


def format_zeit(zeit: str) -> str:
    """Formatiert einen Zeitstempel in ein lesbares Format."""
    try:
        dt = datetime.fromisoformat(zeit.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return zeit


def generiere_kurznachricht(daten: Dict[str, Any]) -> str:
    """
    Generiert eine kurze Wetternachricht für den InReach Messenger.

    Args:
        daten: Dictionary mit Wetterdaten

    Returns:
        String mit der kurzen Nachricht (max. 160 Zeichen)
    """
    nachricht = []

    # Nachttemperatur
    if daten["nachttemperatur"] is not None:
        nachricht.append(f"Nacht: {daten['nachttemperatur']}°C")

    # Hitze
    if daten["hitze"] is not None:
        nachricht.append(f"Tag: {daten['hitze']}°C")

    # Regen
    if daten["regen"] is not None:
        regen_text = f"Regen: {daten['regen']}%"
        if daten["regen_ab"] is not None:
            regen_text += f" ab {format_zeit(daten['regen_ab'])}"
        nachricht.append(regen_text)

    # Wind
    if daten["wind"] is not None:
        nachricht.append(f"Wind: {daten['wind']} km/h")

    # Gewitter
    if daten["gewitter"] is not None:
        gewitter_text = f"Gewitter: {daten['gewitter']}%"
        if daten["gewitter_ab"] is not None:
            gewitter_text += f" ab {format_zeit(daten['gewitter_ab'])}"
        nachricht.append(gewitter_text)

    # Zusammenfügen und auf 160 Zeichen kürzen
    text = " | ".join(nachricht)
    return text[:160]
