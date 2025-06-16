import unittest
from datetime import datetime, timedelta
from wetter.analyse import generiere_wetterbericht
from wetter.kurztext import generiere_kurznachricht
import json
import argparse
from main import lade_daten

class TestAppOutputs(unittest.TestCase):
    def setUp(self):
        # Beispiel-Etappen
        self.etappen = [
            {"name": "Tal - Gipfel", "punkte": [{"lat": 42.5, "lon": 8.9}]}
        ]
        # Standard-Konfiguration
        self.config = {
            "startdatum": "2025-06-15",
            "schwellen": {
                "regen": 20,
                "gewitter": 20,
                "delta_prozent": 5,
                "hitze": 25,
                "wind": 10
            },
            "smtp": {
                "host": "smtp.example.com",
                "port": 587,
                "user": "test@example.com",
                "empfaenger": "empfaenger@example.com",
                "betreff": "Testbericht"
            }
        }
        # Beispiel-Wetterdaten
        self.wetterdaten = {
            "nacht_temp": 2.0,
            "hitze": 35.0,
            "temp": 20.0,
            "temp_gefuehlt": 18.0,
            "wind": 60.0,
            "wind_geschwindigkeit": 15.0,
            "wind_richtung": "NO",
            "regen": 90.0,
            "regen_ab": "14:00",
            "regen_max_zeit": "16:00",
            "gewitter": 80.0,
            "gewitter_ab": "15:00",
            "gewitter_max_zeit": "17:00"
        }

    def test_wetterbericht_standard(self):
        bericht = generiere_wetterbericht(
            nacht_temp=self.wetterdaten["nacht_temp"],
            hitze=self.wetterdaten["hitze"],
            regen=self.wetterdaten["regen"],
            wind=self.wetterdaten["wind"],
            gewitter=self.wetterdaten["gewitter"],
            regen_ab=self.wetterdaten["regen_ab"],
            gewitter_ab=self.wetterdaten["gewitter_ab"],
            regen_max_zeit=self.wetterdaten["regen_max_zeit"],
            gewitter_max_zeit=self.wetterdaten["gewitter_max_zeit"]
        )
        print("\n--- Wetterbericht (Standard) ---\n", bericht)
        self.assertIn("Kalt", bericht)
        self.assertIn("Heiß", bericht)
        self.assertIn("Starker Regen", bericht)
        self.assertIn("Sturm", bericht)
        self.assertIn("Gewitterwahrscheinlich", bericht)
        self.assertIn("Regen ab: 14:00", bericht)
        self.assertIn("Gewitter ab: 15:00", bericht)

    def test_kurznachricht_abend(self):
        nachricht = generiere_kurznachricht(
            wetterdaten=self.wetterdaten,
            modus="abend",
            start_date=self.config["startdatum"],
            etappen_data=self.etappen,
            config=self.config
        )
        print("\n--- Kurznachricht (Abend) ---\n", nachricht)
        self.assertIn("Temperatur", nachricht)
        self.assertIn("Wind", nachricht)
        self.assertIn("Regen", nachricht)
        self.assertIn("Gewitter", nachricht)

    def test_kurznachricht_morgen(self):
        wetterdaten_morgen = self.wetterdaten.copy()
        wetterdaten_morgen["nacht_temp"] = 10.0
        nachricht = generiere_kurznachricht(
            wetterdaten=wetterdaten_morgen,
            modus="morgen",
            start_date=self.config["startdatum"],
            etappen_data=self.etappen,
            config=self.config
        )
        print("\n--- Kurznachricht (Morgen) ---\n", nachricht)
        self.assertIn("Temperatur", nachricht)
        self.assertIn("Wind", nachricht)
        self.assertIn("Regen", nachricht)
        self.assertIn("Gewitter", nachricht)

    def test_kurznachricht_extremwerte(self):
        config_extrem = self.config.copy()
        config_extrem["schwellenwerte"] = {"regen": 0, "gewitter": 0, "wind": 0, "kalt": -10, "heiss": 10}
        nachricht = generiere_kurznachricht(
            wetterdaten=self.wetterdaten,
            modus="abend",
            start_date=self.config["startdatum"],
            etappen_data=self.etappen,
            config=config_extrem
        )
        print("\n--- Kurznachricht (Extremwerte) ---\n", nachricht)
        self.assertIn("Regen", nachricht)
        self.assertIn("Gewitter", nachricht)

    def test_delta_warnungen(self):
        """Test für Delta-Warnungen im Tag-Modus"""
        # Lade Testdaten mit Delta-Änderungen
        with open("tests/testdaten_tag_delta.json", "r") as f:
            testdaten = json.load(f)
        
        # Simuliere Tag-Modus mit Delta-Vergleich
        args = argparse.Namespace(modus="tag", input="tests/testdaten_tag_delta.json")
        daten = lade_daten(args, self.etappen[0], self.config)
        
        # Überprüfe die generierten Warnungen
        self.assertIn("wetter", daten)
        wetter = daten["wetter"]
        
        # Prüfe die erwarteten Änderungen
        self.assertEqual(wetter["hitze"], 28.0)  # Hitze gestiegen
        self.assertEqual(wetter["regen"], 35)    # Regen gestiegen
        self.assertEqual(wetter["wind"], 8)      # Wind gesunken
        self.assertEqual(wetter["gewitter"], 25) # Gewitter gestiegen
        self.assertEqual(wetter["gewitter_ab"], "16:30")  # Gewitterzeit verzögert

if __name__ == "__main__":
    unittest.main() 