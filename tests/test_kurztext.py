import unittest
from datetime import datetime
from wetter.kurztext import (
    format_zeit,
    formatiere_zeit,
    get_current_etappe,
    get_etappe_name,
    generiere_kurznachricht,
    TextGenerationError,
    EtappeError
)

class TestKurztext(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit Testdaten"""
        self.test_wetterdaten = {
            'temp': 20.5,
            'temp_gefuehlt': 19.8,
            'wind_geschwindigkeit': 15.2,
            'wind_richtung': 'NO',
            'regen': 2.5,
            'regen_zeit': '2024-03-10T14:00:00',
            'gewitter': True,
            'gewitter_zeit': '2024-03-10T15:00:00'
        }
        
        self.test_etappen = [
            {'name': 'München - Garmisch'},
            {'name': 'Garmisch - Mittenwald'},
            {'name': 'Mittenwald - Innsbruck'}
        ]

    def test_format_zeit(self):
        """Test Zeitformatierung"""
        # Test gültige Zeit
        self.assertEqual(format_zeit('2024-03-10T14:00:00'), '14')
        
        # Test ungültige Zeit
        with self.assertRaises(ValueError):
            format_zeit('invalid')

    def test_formatiere_zeit(self):
        """Test ISO-Zeitformatierung"""
        # Test gültige ISO-Zeit
        self.assertEqual(formatiere_zeit('2024-03-10T14:00:00'), '14')
        
        # Test None
        self.assertEqual(formatiere_zeit(None), '')
        
        # Test ungültige Zeit
        self.assertEqual(formatiere_zeit('invalid'), '')

    def test_get_current_etappe(self):
        """Test Etappenberechnung"""
        # Test gültiges Datum
        today = datetime.now()
        start_date = today.strftime('%Y-%m-%d')
        self.assertEqual(get_current_etappe(start_date), 1)
        
        # Test zukünftiges Datum
        future_date = (today.replace(year=today.year + 1)).strftime('%Y-%m-%d')
        with self.assertRaises(EtappeError):
            get_current_etappe(future_date)
        
        # Test ungültiges Datum
        with self.assertRaises(EtappeError):
            get_current_etappe('invalid-date')

    def test_get_etappe_name(self):
        """Test Etappennamen-Abruf"""
        # Test gültige Etappe
        self.assertEqual(get_etappe_name(1, self.test_etappen), 'München - Garmisch')
        
        # Test ungültige Etappennummer
        self.assertEqual(get_etappe_name(0, self.test_etappen), None)
        self.assertEqual(get_etappe_name(4, self.test_etappen), 'Etappe 4')
        
        # Test ohne Etappendaten
        self.assertEqual(get_etappe_name(1, None), 'Etappe 1')

    def test_generiere_kurznachricht_abend(self):
        """Test Abend-Wetterbericht"""
        nachricht = generiere_kurznachricht(
            self.test_wetterdaten,
            modus="abend"
        )
        
        # Überprüfe die Nachricht
        self.assertIn("Wetterbericht Abend", nachricht)
        self.assertIn("20.5°C", nachricht)
        self.assertIn("19.8°C", nachricht)
        self.assertIn("15.2 km/h", nachricht)
        self.assertIn("NO", nachricht)
        self.assertIn("2.5 mm", nachricht)
        self.assertIn("Gewitter", nachricht)

    def test_generiere_kurznachricht_morgen(self):
        """Test Morgen-Wetterbericht"""
        wetterdaten = self.test_wetterdaten.copy()
        wetterdaten.update({
            'nacht_temp': 15.5,
            'nacht_temp_gefuehlt': 14.8
        })
        nachricht = generiere_kurznachricht(
            wetterdaten,
            modus="morgen",
            etappenname=None
        )
        # Überprüfe die Nachricht
        self.assertIn("Wetterbericht Morgen", nachricht)
        self.assertIn("15.5°C", nachricht)
        self.assertIn("14.8°C", nachricht)

    def test_generiere_kurznachricht_invalid_data(self):
        """Test ungültige Wetterdaten"""
        # Test mit leeren Wetterdaten
        with self.assertRaises(TextGenerationError):
            generiere_kurznachricht({})

    def test_format_time_invalid(self):
        """Test ungültiges Zeitformat"""
        with self.assertRaises(ValueError):
            format_zeit("invalid-time")
            
    def test_format_time_none(self):
        """Test None als Zeitwert"""
        with self.assertRaises(ValueError):
            format_zeit(None)

if __name__ == '__main__':
    unittest.main() 