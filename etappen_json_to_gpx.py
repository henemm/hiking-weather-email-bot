import json
import gpxpy
import gpxpy.gpx


def lade_etappen_json(pfad):
    with open(pfad, 'r', encoding='utf-8') as f:
        return json.load(f)

def erstelle_gpx(etappen, gpx_pfad):
    gpx = gpxpy.gpx.GPX()
    alle_trackpunkte = []
    for idx, etappe in enumerate(etappen, 1):
        punkte = etappe['punkte']
        # Startpunkt
        start = punkte[0]
        wpt_start = gpxpy.gpx.GPXWaypoint(
            latitude=start['lat'], longitude=start['lon'],
            name=f"Etappe {idx} Start"
        )
        gpx.waypoints.append(wpt_start)
        # Zielpunkt
        ziel = punkte[-1]
        wpt_ziel = gpxpy.gpx.GPXWaypoint(
            latitude=ziel['lat'], longitude=ziel['lon'],
            name=f"Etappe {idx} Ziel"
        )
        gpx.waypoints.append(wpt_ziel)
        # Für Track: alle Punkte in Reihenfolge
        for p in punkte:
            alle_trackpunkte.append((p['lat'], p['lon']))
    # Optional: durchgehender Track
    if alle_trackpunkte:
        trk = gpxpy.gpx.GPXTrack(name="Alle Etappen")
        trkseg = gpxpy.gpx.GPXTrackSegment()
        for lat, lon in alle_trackpunkte:
            trkseg.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
        trk.segments.append(trkseg)
        gpx.tracks.append(trk)
    # Schreibe GPX-Datei
    with open(gpx_pfad, 'w', encoding='utf-8') as f:
        f.write(gpx.to_xml())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Konvertiert etappen.json zu einer GPX mit Wegpunkten und Track.")
    parser.add_argument('--input', default='etappen.json', help='Pfad zu etappen.json')
    parser.add_argument('--output', default='etappen.gpx', help='Ziel-GPX-Datei')
    args = parser.parse_args()
    etappen = lade_etappen_json(args.input)
    erstelle_gpx(etappen, args.output)
    print(f"GPX-Datei erfolgreich geschrieben: {args.output}") 