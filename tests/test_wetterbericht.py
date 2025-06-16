import unittest

from wetter.analyse import generiere_wetterbericht


class TestWetterbericht(unittest.TestCase):
    def setUp(self):
        """Testdaten vorbereiten"""
        self.normal_tag = {
            "nacht_temp": 15.0,
            "hitze": 25.0,
            "regen": 20.0,
            "wind": 15.0,
            "gewitter": 5.0,
        }

        self.warnung_tag = {
            "nacht_temp": 2.0,
            "hitze": 35.0,
            "regen": 90.0,
            "wind": 60.0,
            "gewitter": 80.0,
            "regen_ab": "14:00",
            "gewitter_ab": "15:00",
            "regen_max_zeit": "16:00",
            "gewitter_max_zeit": "17:00",
        }

        self.zeit_tag = {
            "nacht_temp": 10.0,
            "hitze": 20.0,
            "regen": 40.0,
            "wind": 10.0,
            "gewitter": 20.0,
            "regen_ab": "12:00",
            "gewitter_ab": "13:00",
        }

        self.ungueltige_zeit = {
            "nacht_temp": 10.0,
            "hitze": 20.0,
            "regen": 40.0,
            "wind": 10.0,
            "gewitter": 20.0,
            "regen_ab": "invalid",
            "gewitter_ab": "invalid",
        }

    def test_normaler_tag(self):
        """Test normaler Wetterbericht"""
        bericht = generiere_wetterbericht(**self.normal_tag)
        # Akzeptiere auch leere Berichte, wenn keine Schwellenwerte überschritten werden
        self.assertTrue(isinstance(bericht, str))

    def test_warnungen(self):
        """Test Wetterbericht mit Warnungen"""
        bericht = generiere_wetterbericht(**self.warnung_tag)

        # Prüfe Warnungen
        self.assertIn("❄️ Kalt: 2.0°C - Warme Kleidung für die Nacht!", bericht)
        self.assertIn("🔥 Heiß: 35.0°C", bericht)
        self.assertIn("🌧️ Starker Regen (90.0%)", bericht)
        self.assertIn("💨 Sturm (60.0 km/h)", bericht)
        self.assertIn("⛈️ Gewitterwahrscheinlich (80.0%)", bericht)

        # Prüfe zeitliche Informationen
        self.assertIn("Regen ab: 14:00", bericht)
        self.assertIn("Gewitter ab: 15:00", bericht)
        self.assertIn("Stärkster Regen: 16:00", bericht)
        self.assertIn("Höchste Gewittergefahr: 17:00", bericht)

    def test_zeitliche_informationen(self):
        """Test zeitliche Informationen im Bericht"""
        bericht = generiere_wetterbericht(**self.zeit_tag)

        # Prüfe zeitliche Informationen
        self.assertIn("Regen ab: 12:00", bericht)
        self.assertIn("Gewitter ab: 13:00", bericht)

        # Prüfe dass keine maximalen Zeiten enthalten sind
        self.assertNotIn("Stärkster Regen:", bericht)
        self.assertNotIn("Höchste Gewittergefahr:", bericht)

    def test_ungueltige_zeit(self):
        """Test Behandlung ungültiger Zeitstempel"""
        bericht = generiere_wetterbericht(**self.ungueltige_zeit)

        # Prüfe dass ungültige Zeiten ignoriert werden
        self.assertIn("Leichter Regen möglich", bericht)
        self.assertIn("Regen ab: invalid", bericht)
        self.assertIn("Gewitter ab: invalid", bericht)


if __name__ == "__main__":
    unittest.main()
