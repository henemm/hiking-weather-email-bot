#!/usr/bin/env python3
import argparse
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re

import gpxpy
from geopy.distance import geodesic

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def lade_gpx_punkte(pfad):
    with open(pfad, 'r', encoding='utf-8') as f:
        gpx = gpxpy.parse(f)
    punkte = []
    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                punkte.append((p.latitude, p.longitude, p.elevation or 0.0))
    return punkte

def extrahiere_trackpunkte(gpx: gpxpy.gpx.GPX) -> List[gpxpy.gpx.GPXTrackPoint]:
    """Extrahiert alle Trackpunkte aus dem GPX-Objekt."""
    trackpunkte = []
    for track in gpx.tracks:
        for segment in track.segments:
            trackpunkte.extend(segment.points)
    return trackpunkte

def berechne_distanz(p1, p2):
    # Erwartet Tupel (lat, lon, ele)
    return geodesic((p1[0], p1[1]), (p2[0], p2[1])).kilometers

def finde_hochpunkte_und_zwischenpunkte(punkte, min_abstand_start=1.0, min_abstand_ziel=1.0, min_abstand_punkte=5.0, max_luecke=8.0):
    if len(punkte) < 2:
        return punkte
    start = punkte[0]
    ziel = punkte[-1]
    result = [start]
    # Hochpunkte: nach Höhe sortiert, mind. 1km nach Start und vor Ziel
    zwischenkandidaten = [p for p in punkte[1:-1]
                         if berechne_distanz(start, p) >= min_abstand_start and berechne_distanz(p, ziel) >= min_abstand_ziel]
    hochpunkte = sorted(zwischenkandidaten, key=lambda p: p[2], reverse=True)
    # Füge Hochpunkte ein, wenn sie mind. min_abstand_punkte voneinander entfernt sind
    ausgewaehlt = []
    for hp in hochpunkte:
        if all(berechne_distanz(hp, p) >= min_abstand_punkte for p in ausgewaehlt):
            ausgewaehlt.append(hp)
    # Sortiere nach Reihenfolge auf der Route
    ausgewaehlt = sorted(ausgewaehlt, key=lambda p: punkte.index(p))
    result.extend(ausgewaehlt)
    # Prüfe auf große Lücken (>max_luecke km) und füge ggf. Mittelpunkt ein
    alle_punkte = result + [ziel]
    final = [alle_punkte[0]]
    for i in range(1, len(alle_punkte)):
        dist = berechne_distanz(alle_punkte[i-1], alle_punkte[i])
        if dist > max_luecke:
            # Füge Mittelpunkt ein
            mid_lat = (alle_punkte[i-1][0] + alle_punkte[i][0]) / 2
            mid_lon = (alle_punkte[i-1][1] + alle_punkte[i][1]) / 2
            mid_ele = (alle_punkte[i-1][2] + alle_punkte[i][2]) / 2
            final.append((mid_lat, mid_lon, mid_ele))
        final.append(alle_punkte[i])
    # Entferne doppelte Punkte (nach Koordinaten)
    unique = []
    seen = set()
    for p in final:
        key = (round(p[0], 6), round(p[1], 6))
        if key not in seen:
            unique.append(p)
            seen.add(key)
    return unique

def konvertiere_gpx_zu_json(input_dir, output_file):
    gpx_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.gpx')]
    gpx_files.sort(key=extrahiere_etappennummer)
    etappen = []
    for fname in gpx_files:
        pfad = os.path.join(input_dir, fname)
        punkte = lade_gpx_punkte(pfad)
        punkte_auswahl = finde_hochpunkte_und_zwischenpunkte(punkte)
        etappen.append({
            "name": fname,
            "punkte": [{"lat": p[0], "lon": p[1]} for p in punkte_auswahl]
        })
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(etappen, f, indent=2, ensure_ascii=False)
    print(f"Etappen erfolgreich gespeichert in {output_file}")

def get_gpx_startzeit(gpx: gpxpy.gpx.GPX) -> str:
    """Extrahiert die Startzeit aus einer GPX-Datei."""
    for track in gpx.tracks:
        for segment in track.segments:
            if segment.points:
                return segment.points[0].time.isoformat()
    return "0000-00-00T00:00:00"  # Fallback

def extrahiere_etappennummer(dateiname: str) -> int:
    """Extrahiert die Etappennummer aus dem Dateinamen."""
    match = re.search(r'Etappe\s+(\d+)', dateiname)
    if match:
        return int(match.group(1))
    return 999  # Fallback für Dateien ohne Etappennummer

def main():
    parser = argparse.ArgumentParser(description="Konvertiert GPX-Etappen zu etappen.json mit Start, Hochpunkten/Zwischenpunkten und Ziel.")
    parser.add_argument('--input-dir', required=True, help='Verzeichnis mit GPX-Dateien')
    parser.add_argument('--output', default='etappen.json', help='Ziel-Datei')
    args = parser.parse_args()
    konvertiere_gpx_zu_json(args.input_dir, args.output)

if __name__ == "__main__":
    main() 