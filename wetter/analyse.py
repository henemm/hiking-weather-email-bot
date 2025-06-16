from typing import Optional


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
    Gibt alle Wetterwerte als nackte Zahlen mit Emoji aus.
    """
    bericht = []
    if etappenname:
        bericht.append(etappenname)
    if nacht_temp is not None:
        bericht.append(f"🌙 Nacht: {nacht_temp:.1f}°C")
    if hitze is not None:
        bericht.append(f"🌡️ Tag: {hitze:.1f}°C")
    if regen is not None:
        zeile = f"🌧️ Regen: {regen:.0f}%"
        if regen_ab:
            zeile += f" ab {regen_ab[11:16]}"
        bericht.append(zeile)
    if wind is not None:
        bericht.append(f"💨 Wind: {wind:.1f} km/h")
    if gewitter is not None:
        zeile = f"⚡ Gewitter: {gewitter:.0f}%"
        if gewitter_ab:
            zeile += f" ab {gewitter_ab[11:16]}"
        bericht.append(zeile)
    return "\n".join(bericht)
