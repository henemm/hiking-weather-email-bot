import json
import random

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Etappen-Visualisierung</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <style>#map { height: 98vh; width: 100vw; }</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([42.5, 8.9], 10);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

{layers}

</script>
</body>
</html>
'''

def random_color():
    return f"#{random.randint(0, 0xFFFFFF):06x}"

def lade_etappen_json(pfad):
    with open(pfad, 'r', encoding='utf-8') as f:
        return json.load(f)

def erstelle_leaflet_layers(etappen):
    js = []
    for idx, etappe in enumerate(etappen, 1):
        punkte = etappe['punkte']
        coords = [[p['lat'], p['lon']] for p in punkte]
        color = random_color()
        # Linie für Etappe
        js.append(f"var poly{idx} = L.polyline({coords}, {{color: '{color}', weight: 5, opacity: 0.8}}).addTo(map);")
        js.append(f"poly{idx}.bindPopup('Etappe {idx}');")
        # Marker für Start
        js.append(f"L.marker({coords[0]}).addTo(map).bindPopup('Etappe {idx} Start');")
        # Marker für Zwischenmessstellen
        for i, c in enumerate(coords[1:-1], 1):
            js.append(f"L.marker({c}).addTo(map).bindPopup('Etappe {idx} Messpunkt {i}');")
        # Marker für Ziel
        js.append(f"L.marker({coords[-1]}).addTo(map).bindPopup('Etappe {idx} Ziel');")
    # Karte auf alle Etappen zoomen
    all_coords = [c for et in etappen for c in [[p['lat'], p['lon']] for p in et['punkte']]]
    js.append(f"map.fitBounds({all_coords});")
    return '\n'.join(js)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Visualisiere etappen.json als interaktive Leaflet-Karte.")
    parser.add_argument('--input', default='etappen.json', help='Pfad zu etappen.json')
    parser.add_argument('--output', default='etappen_karte.html', help='Ziel-HTML-Datei')
    args = parser.parse_args()
    etappen = lade_etappen_json(args.input)
    layers = erstelle_leaflet_layers(etappen)
    html = HTML_TEMPLATE.replace('{layers}', layers)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Karte erfolgreich geschrieben: {args.output}") 