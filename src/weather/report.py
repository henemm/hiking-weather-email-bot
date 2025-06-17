from datetime import datetime
from typing import Optional, Dict, Any
from .models import ReportMode, WeatherReport

def generiere_wetterbericht(
    nacht_temp: Optional[float],
    hitze: float,
    regen: float,
    wind: float,
    gewitter: float,
    regen_ab: Optional[str] = None,
    gewitter_ab: Optional[str] = None,
    regen_max_zeit: Optional[str] = None,
    gewitter_max_zeit: Optional[str] = None,
    stage_name: Optional[str] = None,
    modus: str = "abend"
) -> str:
    """
    Generiert einen Wetterbericht basierend auf den Wetterdaten.
    
    Args:
        nacht_temp: Nachttemperatur
        hitze: Maximale Temperatur
        regen: Niederschlagswahrscheinlichkeit
        wind: Windgeschwindigkeit
        gewitter: Gewitterwahrscheinlichkeit
        regen_ab: Zeitpunkt des Regenbeginns
        gewitter_ab: Zeitpunkt des Gewitterbeginns
        regen_max_zeit: Zeitpunkt des stärksten Regens
        gewitter_max_zeit: Zeitpunkt der höchsten Gewittergefahr
        stage_name: Name der Etappe
        modus: Berichtsmodus (abend/morgen/tag)
        
    Returns:
        Formatieter Wetterbericht
    """
    bericht = []
    
    if stage_name:
        bericht.append(f"🏔️ {stage_name}\n")
    
    # Nachttemperatur (nur im Abendmodus)
    if modus == "abend" and nacht_temp is not None:
        if nacht_temp < 5:
            bericht.append(f"❄️ Extreme Kälte: {nacht_temp:.1f}°C - Warme Kleidung für die Nacht!")
        else:
            bericht.append(f"🌙 Nacht: {nacht_temp:.1f}°C")
    
    # Temperatur
    if hitze > 30:
        bericht.append(f"🔥 Heiß: {hitze:.1f}°C")
    else:
        bericht.append(f"🌡️ Temperatur: {hitze:.1f}°C")
    
    # Regen
    if regen > 80:
        bericht.append(f"🌧️ Starker Regen ({regen:.1f}%)")
    elif regen > 50:
        bericht.append(f"🌧️ Regenrisiko: {regen:.1f}%")
    elif regen > 20:
        bericht.append(f"🌧️ Leichter Regen möglich ({regen:.1f}%)")
    
    if regen_ab:
        bericht.append(f"   • Regen ab: {regen_ab.split('T')[1][:5]}")
    if regen_max_zeit:
        bericht.append(f"   • Stärkster Regen: {regen_max_zeit.split('T')[1][:5]}")
    
    # Wind
    if wind > 75:
        bericht.append(f"💨 Orkan ({wind:.1f} km/h)")
    elif wind > 50:
        bericht.append(f"💨 Sturm ({wind:.1f} km/h)")
    elif wind > 30:
        bericht.append(f"💨 Starker Wind ({wind:.1f} km/h)")
    
    # Gewitter
    if gewitter > 50:
        bericht.append(f"⛈️ Gewitterwahrscheinlich ({gewitter:.1f}%)")
        if gewitter_ab:
            bericht.append(f"   • Gewitter ab: {gewitter_ab.split('T')[1][:5]}")
        if gewitter_max_zeit:
            bericht.append(f"   • Höchste Gewittergefahr: {gewitter_max_zeit.split('T')[1][:5]}")
    
    return "\n".join(bericht) 