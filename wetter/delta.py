def berechne_delta(alt, neu):
    """
    Vergleicht die Regenwahrscheinlichkeit pro Punkt.
    """
    return [b.get("regen", 0) - a.get("regen", 0) for a, b in zip(alt, neu)]

def delta_warnung(alt, neu, schwelle, etappenname):
    """
    Gibt Warntext zurück, wenn Differenz über Schwelle liegt.
    """
    deltas = berechne_delta(alt, neu)
    max_diff = max(deltas)

    if max_diff >= schwelle:
        warnung = (
            f"⚠️ Wetteränderung Etappe {etappenname}\n"
            f"Regenrisiko stark gestiegen: +{max_diff:.0f}%\n"
        )
        return warnung, True
    return "", False