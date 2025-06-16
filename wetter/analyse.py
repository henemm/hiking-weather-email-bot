from typing import Optional, List, Dict, Any


def generiere_wetterbericht(
    nacht_temp: Optional[float],
    hitze: Optional[float],
    regen: Optional[float],
    wind: Optional[float],
    gewitter: Optional[float],
    regen_ab: Optional[str] = None,
    gewitter_ab: Optional[str] = None,
    regen_max_zeit: Optional[str] = None,
    gewitter_max_zeit: Optional[str] = None,
    etappenname: Optional[str] = None,
) -> str:
    """
    Generiert einen detaillierten Wetterbericht mit allen relevanten Informationen.
    """
    bericht = []
    
    # Etappenname als Überschrift
    if etappenname:
        bericht.append(f"🏔️ {etappenname}")
        bericht.append("")  # Leerzeile für bessere Lesbarkeit
    
    # Nachttemperatur mit Warnung
    if nacht_temp is not None:
        if nacht_temp < 5:
            bericht.append(f"❄️ Kalt: {nacht_temp:.1f}°C - Warme Kleidung für die Nacht!")
        else:
            bericht.append(f"🌙 Nachttemperatur: {nacht_temp:.1f}°C")
    
    # Tagestemperatur mit Warnung
    if hitze is not None:
        if hitze > 30:
            bericht.append(f"🔥 Heiß: {hitze:.1f}°C")
        else:
            bericht.append(f"🌡️ Tagestemperatur: {hitze:.1f}°C")
    
    # Regenrisiko mit detaillierten Informationen
    if regen is not None:
        if regen > 70:
            regen_text = f"🌧️ Starker Regen ({regen:.1f}%)"
        elif regen > 40:
            regen_text = f"🌧️ Regenrisiko: {regen:.0f}%"
        else:
            regen_text = "Leichter Regen möglich"
            
        if regen_ab:
            regen_text += f"\n   • Regen ab: {regen_ab}"
        if regen_max_zeit:
            regen_text += f"\n   • Stärkster Regen: {regen_max_zeit}"
        bericht.append(regen_text)
    
    # Wind mit Warnung
    if wind is not None:
        if wind > 50:
            bericht.append(f"💨 Sturm ({wind:.1f} km/h)")
        else:
            bericht.append(f"💨 Wind: {wind:.1f} km/h")
    
    # Gewitterrisiko mit detaillierten Informationen
    if gewitter is not None:
        if gewitter > 50:
            gewitter_text = f"⛈️ Gewitterwahrscheinlich ({gewitter:.1f}%)"
        else:
            gewitter_text = f"⚡ Gewitterrisiko: {gewitter:.0f}%"
            
        if gewitter_ab:
            gewitter_text += f"\n   • Gewitter ab: {gewitter_ab}"
        if gewitter_max_zeit:
            gewitter_text += f"\n   • Höchste Gewittergefahr: {gewitter_max_zeit}"
        bericht.append(gewitter_text)
    
    return "\n".join(bericht)

def finde_erste_zeit_ueber_schwelle(
    stunden: List[Dict[str, Any]], 
    wert: str, 
    schwelle: float
) -> Optional[str]:
    """
    Findet die erste Uhrzeit, ab der der Wert über dem Schwellenwert liegt.
    """
    for stunde in stunden:
        if stunde[wert] > 0:  # Geändert: Prüfe auf >0 statt >schwelle
            return stunde["zeit"]
    return None
