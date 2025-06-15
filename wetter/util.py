from datetime import datetime

def extrahiere_zeitpunkt_mit_schwelle(times, values, datum, schwelle):
    for t, v in zip(times, values):
        if not t.startswith(datum):
            continue
        if v >= schwelle:
            try:
                return datetime.fromisoformat(t).strftime("%H:%M")
            except:
                continue
    return None