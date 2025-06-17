# SPEZIFIKATION Wetterbericht-Output

## Allgemeines
- Alle Berichte enthalten konkrete Werte (keine Risikolevel).
- Zeitpunkte werden als HH oder HH:MM angegeben.
- Für Regen und Gewitter werden jeweils zwei Werte ausgegeben:
  - Der Wert, bei dem die Schwelle (aus config.yaml) erstmals überschritten wird (mit Zeitpunkt)
  - Das Tagesmaximum (mit Zeitpunkt)

## Langbericht (Abend/Morgen/Tag)
### Beispiel (Abend/Morgen/Tag)

```
Wetterbericht für Etappe 1 am 01.01.2023

Nachttemperatur:
  18°C

Risiken für morgen:
  Regenwahrscheinlichkeit: 25%@10:00 (60%@15:00)
  Niederschlagsmenge: 2mm@10:00 (5mm@15:00)
  Gewitterwahrscheinlichkeit: 40%@12:00 (70%@15:00)
  Wind: 20km/h
  Hitze: 32°C

Gewitterwahrscheinlichkeit für übermorgen:
  30%
```

- Für Morgen- und Tag-Modus entsprechend "Risiken für heute" bzw. "Signifikante Verschlechterung".

## Kurzbericht (InReach)
### Format
```
Etappenname | Gewitter 40% @12 (70% @15) | Regen 25% 2mm @10 (60% 5mm @15) | Wind 20km/h | Hitze 32°C | Nacht 18°C
```
- Im Tag-/Morgenmodus ohne "Nacht ..."
- Immer beide Werte (Schwelle, Maximum) mit Zeitpunkten und Einheiten.

## Felder
- **Regenwahrscheinlichkeit:** xx%@hh:mm (yy%@hh:mm)
- **Niederschlagsmenge:** xxmm@hh:mm (yymm@hh:mm)
- **Gewitterwahrscheinlichkeit:** xx%@hh:mm (yy%@hh:mm)
- **Wind:** xxkm/h
- **Hitze:** xx°C
- **Nacht:** xx°C (nur Abend)

## Beispiele
### Abendbericht (Lang)
```
Wetterbericht für Etappe 1 am 01.01.2023

Nachttemperatur:
  18°C

Risiken für morgen:
  Regenwahrscheinlichkeit: 25%@10:00 (60%@15:00)
  Niederschlagsmenge: 2mm@10:00 (5mm@15:00)
  Gewitterwahrscheinlichkeit: 40%@12:00 (70%@15:00)
  Wind: 20km/h
  Hitze: 32°C

Gewitterwahrscheinlichkeit für übermorgen:
  30%
```

### Abendbericht (Kurz/InReach)
```
Etappe 1 | Gewitter 40% @12 (70% @15) | Regen 25% 2mm @10 (60% 5mm @15) | Wind 20km/h | Hitze 32°C | Nacht 18°C
```

### Morgenbericht (Lang)
```
Wetterbericht für Etappe 1 am 01.01.2023

Risiken für heute:
  Regenwahrscheinlichkeit: 25%@10:00 (60%@15:00)
  Niederschlagsmenge: 2mm@10:00 (5mm@15:00)
  Gewitterwahrscheinlichkeit: 40%@12:00 (70%@15:00)
  Wind: 20km/h
  Hitze: 32°C

Gewitterwahrscheinlichkeit für morgen:
  30%
```

### Morgenbericht (Kurz/InReach)
```
Etappe 1 | Gewitter 40% @12 (70% @15) | Regen 25% 2mm @10 (60% 5mm @15) | Wind 20km/h | Hitze 32°C
```

### Tageswarnung (Lang)
```
Wetterbericht für Etappe 1 am 01.01.2023

⚠️ Wetterwarnung für Etappe 1 am 01.01.2023

Signifikante Verschlechterung:
  Regenwahrscheinlichkeit: 25%@10:00 (60%@15:00)
  Niederschlagsmenge: 2mm@10:00 (5mm@15:00)
  Gewitterwahrscheinlichkeit: 40%@12:00 (70%@15:00)
  Wind: 20km/h
  Hitze: 32°C
```

### Tageswarnung (Kurz/InReach)
```
Etappe 1 | Gewitter 40% @12 (70% @15) | Regen 25% 2mm @10 (60% 5mm @15) | Wind 20km/h | Hitze 32°C
```

## Zusätzliche Hinweise
- Wenn kein Schwellenwert überschritten wird, wird nur der Maximalwert mit Uhrzeit angezeigt: `[Max%@HH:MM]`
- Wenn keine Daten vorhanden sind, wird "unbekannt" ausgegeben.
- Alle Zeitangaben im Format HH:MM (z.B. 09:00, 15:00).

## Testfall für die Implementierung
**Input:**  
- Regen: 15% ab 10:00, Maximum 45% um 15:00  
- Gewitter: 20% ab 11:00, Maximum 50% um 16:00  
- Wind: 35km/h  
- Hitze: 32°C  
- Nachttemperatur: 13.7°C  
- Gewitter +1: 30% ab 12:00, Maximum 60% um 14:00

**Erwartete Ausgabe (Langtext Abendbericht):**
```
Wetterbericht für Etappe 1 am 20.03.2024

Nachttemperatur:
  13.7°C

Risiken für morgen:
  Regenwahrscheinlichkeit: 25%@10:00 (60%@15:00)
  Niederschlagsmenge: 2mm@10:00 (5mm@15:00)
  Gewitterwahrscheinlichkeit: 40%@12:00 (70%@15:00)
  Wind: 35km/h
  Hitze: 32°C

Gewitterwahrscheinlichkeit für übermorgen:
  30%
``` 