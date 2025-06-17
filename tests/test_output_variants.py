import unittest
import json
import os
import argparse
from datetime import datetime, timedelta
from wetter.analyse import generiere_wetterbericht
from wetter.kurztext import generiere_kurznachricht
from main import lade_daten

class TestOutputVariants(unittest.TestCase):
    def setUp(self):
        # Load test data
        self.test_data_dir = os.path.dirname(__file__)
        self.etappen = [
            {
                "name": "Test Etappe",
                "punkte": [
                    {"lat": 47.0, "lon": 11.0},
                    {"lat": 47.1, "lon": 11.1}
                ]
            }
        ]
        
        # Standard configuration
        self.config = {
            "startdatum": "2024-03-20",
            "schwellen": {
                "regen": 20,
                "gewitter": 20,
                "delta_prozent": 5,
                "hitze": 25,
                "wind": 10
            }
        }

    def load_test_data(self, filename):
        """Helper to load test data from JSON files"""
        with open(os.path.join(self.test_data_dir, filename), 'r') as f:
            return json.load(f)

    def test_evening_mode_detailed(self):
        """Test evening mode with detailed output"""
        test_data = self.load_test_data("testdaten_abend.json")
        args = argparse.Namespace(
            modus="abend",
            input=os.path.join(self.test_data_dir, "testdaten_abend.json"),
            inreach=False,
            dry_run=True
        )
        
        daten = lade_daten(args, self.etappen[0], self.config)
        bericht = generiere_wetterbericht(
            nacht_temp=daten["wetter"].get("nacht_temp"),
            hitze=daten["wetter"].get("hitze"),
            regen=daten["wetter"].get("regen"),
            wind=daten["wetter"].get("wind_geschwindigkeit"),
            gewitter=daten["wetter"].get("gewitter"),
            regen_ab=daten["wetter"].get("regen_ab"),
            gewitter_ab=daten["wetter"].get("gewitter_ab"),
            regen_max_zeit=daten["wetter"].get("regen_max_zeit"),
            gewitter_max_zeit=daten["wetter"].get("gewitter_max_zeit"),
            etappenname=self.etappen[0]["name"]
        )
        
        # Verify exact output format
        self.assertIn("Nacht-Temperatur:", bericht)
        self.assertIn("Temperatur:", bericht)
        self.assertIn("Wind:", bericht)
        self.assertIn("Regen:", bericht)
        self.assertIn("Gewitter:", bericht)
        self.assertIn("Gewitter übermorgen:", bericht)  # Always shown in evening mode
        
        # Verify no "gering/mittel/hoch" words
        self.assertNotIn("gering", bericht.lower())
        self.assertNotIn("mittel", bericht.lower())
        self.assertNotIn("hoch", bericht.lower())

    def test_morning_mode_detailed(self):
        """Test morning mode with detailed output"""
        test_data = self.load_test_data("testdaten_morgen.json")
        args = argparse.Namespace(
            modus="morgen",
            input=os.path.join(self.test_data_dir, "testdaten_morgen.json"),
            inreach=False,
            dry_run=True
        )
        
        daten = lade_daten(args, self.etappen[0], self.config)
        bericht = generiere_wetterbericht(
            nacht_temp=daten["wetter"].get("nacht_temp"),
            hitze=daten["wetter"].get("hitze"),
            regen=daten["wetter"].get("regen"),
            wind=daten["wetter"].get("wind_geschwindigkeit"),
            gewitter=daten["wetter"].get("gewitter"),
            regen_ab=daten["wetter"].get("regen_ab"),
            gewitter_ab=daten["wetter"].get("gewitter_ab"),
            regen_max_zeit=daten["wetter"].get("regen_max_zeit"),
            gewitter_max_zeit=daten["wetter"].get("gewitter_max_zeit"),
            etappenname=self.etappen[0]["name"]
        )
        
        # Verify exact output format
        self.assertIn("Nacht-Temperatur:", bericht)
        self.assertIn("Temperatur:", bericht)
        self.assertIn("Wind:", bericht)
        self.assertIn("Regen:", bericht)
        self.assertIn("Gewitter:", bericht)
        self.assertNotIn("Gewitter übermorgen:", bericht)  # Not shown in morning mode

    def test_day_mode_detailed(self):
        """Test day mode with detailed output"""
        test_data = self.load_test_data("testdaten_tag_warnung.json")
        args = argparse.Namespace(
            modus="tag",
            input=os.path.join(self.test_data_dir, "testdaten_tag_warnung.json"),
            inreach=False,
            dry_run=True
        )
        
        daten = lade_daten(args, self.etappen[0], self.config)
        bericht = generiere_wetterbericht(
            nacht_temp=daten["wetter"].get("nacht_temp"),
            hitze=daten["wetter"].get("hitze"),
            regen=daten["wetter"].get("regen"),
            wind=daten["wetter"].get("wind_geschwindigkeit"),
            gewitter=daten["wetter"].get("gewitter"),
            regen_ab=daten["wetter"].get("regen_ab"),
            gewitter_ab=daten["wetter"].get("gewitter_ab"),
            regen_max_zeit=daten["wetter"].get("regen_max_zeit"),
            gewitter_max_zeit=daten["wetter"].get("gewitter_max_zeit"),
            etappenname=self.etappen[0]["name"]
        )
        
        # Verify exact output format
        self.assertIn("Temperatur:", bericht)
        self.assertIn("Wind:", bericht)
        self.assertIn("Regen:", bericht)
        self.assertIn("Gewitter:", bericht)
        self.assertNotIn("Nacht-Temperatur:", bericht)  # Not shown in day mode

    def test_inreach_output(self):
        """Test InReach compact output format"""
        test_data = self.load_test_data("testdaten_abend.json")
        args = argparse.Namespace(
            modus="abend",
            input=os.path.join(self.test_data_dir, "testdaten_abend.json"),
            inreach=True,
            dry_run=True
        )
        
        daten = lade_daten(args, self.etappen[0], self.config)
        nachricht = generiere_kurznachricht(
            wetterdaten=daten["wetter"],
            modus="abend",
            inreach=True,
            etappenname=self.etappen[0]["name"]
        )
        
        # Verify InReach format (single line, tabular)
        self.assertEqual(len(nachricht.split('\n')), 1)
        self.assertIn(' | ', nachricht)
        
        # Verify all required fields are present
        fields = nachricht.split(' | ')
        self.assertGreaterEqual(len(fields), 5)  # At least 5 fields (temp, wind, rain, thunder, thunder+1)
        
        # Verify no descriptive words
        self.assertNotIn("gering", nachricht.lower())
        self.assertNotIn("mittel", nachricht.lower())
        self.assertNotIn("hoch", nachricht.lower())

    def test_edge_cases(self):
        """Test various edge cases"""
        # Test missing values
        test_data = self.load_test_data("testdaten_fehlerhaft.json")
        args = argparse.Namespace(
            modus="abend",
            input=os.path.join(self.test_data_dir, "testdaten_fehlerhaft.json"),
            inreach=False,
            dry_run=True
        )
        
        daten = lade_daten(args, self.etappen[0], self.config)
        bericht = generiere_wetterbericht(
            nacht_temp=daten["wetter"].get("nacht_temp"),
            hitze=daten["wetter"].get("hitze"),
            regen=daten["wetter"].get("regen"),
            wind=daten["wetter"].get("wind_geschwindigkeit"),
            gewitter=daten["wetter"].get("gewitter"),
            regen_ab=daten["wetter"].get("regen_ab"),
            gewitter_ab=daten["wetter"].get("gewitter_ab"),
            regen_max_zeit=daten["wetter"].get("regen_max_zeit"),
            gewitter_max_zeit=daten["wetter"].get("gewitter_max_zeit"),
            etappenname=self.etappen[0]["name"]
        )
        
        # Verify handling of missing values
        self.assertIn("N/A", bericht)
        
        # Test maximum values
        test_data = self.load_test_data("testdaten_gewitter.json")
        args = argparse.Namespace(
            modus="abend",
            input=os.path.join(self.test_data_dir, "testdaten_gewitter.json"),
            inreach=False,
            dry_run=True
        )
        
        daten = lade_daten(args, self.etappen[0], self.config)
        bericht = generiere_wetterbericht(
            nacht_temp=daten["wetter"].get("nacht_temp"),
            hitze=daten["wetter"].get("hitze"),
            regen=daten["wetter"].get("regen"),
            wind=daten["wetter"].get("wind_geschwindigkeit"),
            gewitter=daten["wetter"].get("gewitter"),
            regen_ab=daten["wetter"].get("regen_ab"),
            gewitter_ab=daten["wetter"].get("gewitter_ab"),
            regen_max_zeit=daten["wetter"].get("regen_max_zeit"),
            gewitter_max_zeit=daten["wetter"].get("gewitter_max_zeit"),
            etappenname=self.etappen[0]["name"]
        )
        
        # Verify handling of maximum values
        self.assertIn("100%", bericht)

    def test_parameter_aggregation(self):
        """Test parameter aggregation logic for each mode"""
        # Test evening mode aggregation
        test_data = self.load_test_data("testdaten_abend.json")
        args = argparse.Namespace(
            modus="abend",
            input=os.path.join(self.test_data_dir, "testdaten_abend.json"),
            inreach=False,
            dry_run=True
        )
        
        daten = lade_daten(args, self.etappen[0], self.config)
        
        # Verify night temperature is from last point
        self.assertEqual(daten["wetter"]["nacht_temp"], test_data["punkte"][-1]["nacht_temp"])
        
        # Verify risks are maximum over all points
        self.assertEqual(daten["wetter"]["regen"], max(p["regen"] for p in test_data["punkte"]))
        self.assertEqual(daten["wetter"]["gewitter"], max(p["gewitter"] for p in test_data["punkte"]))

if __name__ == "__main__":
    unittest.main() 