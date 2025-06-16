import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from wetter.wetterdaten import hole_wetterdaten, windrichtung_zu_text, WeatherDataError, APIError, DataProcessingError

class TestWetterdaten(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit Mock-Daten"""
        self.mock_response = {
            "list": [
                {
                    "dt": 1710000000,
                    "main": {
                        "temp": 15.5,
                        "feels_like": 14.2
                    },
                    "wind": {
                        "speed": 5.2,
                        "deg": 180
                    },
                    "rain": {"3h": 2.5},
                    "weather": [
                        {
                            "id": 200,
                            "main": "Thunderstorm",
                            "description": "thunderstorm with light rain"
                        }
                    ]
                }
            ]
        }

    @patch('requests.get')
    def test_hole_wetterdaten_success(self, mock_get):
        """Test erfolgreicher Wetterdaten-Abruf"""
        # Mock-Antwort im neuen Format
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'hourly': {
                'temperature_2m': 15.0,
                'apparent_temperature': 14.0,
                'windspeed_10m': 10.0,
                'winddirection_10m': 90,
                'precipitation': 2.5,
                'thunderstorm': True,
                'precipitation_time': '2024-06-01T12:00:00',
                'thunderstorm_time': '2024-06-01T15:00:00',
                'time': ['2024-06-01T12:00:00']
            }
        }
        result = hole_wetterdaten(48.137154, 11.576124, config={})
        self.assertEqual(result['temp'], 15.0)
        self.assertEqual(result['temp_gefuehlt'], 14.0)
        self.assertEqual(result['wind_geschwindigkeit'], 10.0)
        self.assertEqual(result['wind_richtung'], 'O')
        self.assertEqual(result['regen'], 2.5)
        self.assertTrue(result['gewitter'])
        self.assertEqual(result['regen_zeit'], '2024-06-01T12:00:00')
        self.assertEqual(result['gewitter_zeit'], '2024-06-01T15:00:00')

    @patch('requests.get')
    def test_hole_wetterdaten_api_error(self, mock_get):
        """Test API-Fehler"""
        mock_get.side_effect = Exception("API Error")
        with self.assertRaises(WeatherDataError):
            hole_wetterdaten(48.137154, 11.576124, config={})

    @patch('requests.get')
    def test_hole_wetterdaten_invalid_response(self, mock_get):
        """Test ungültige API-Antwort"""
        # Mock-Antwort ohne 'hourly'
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        with self.assertRaises(DataProcessingError):
            hole_wetterdaten(48.137154, 11.576124, config={})

    def test_windrichtung_zu_text(self):
        """Test Windrichtungs-Konvertierung"""
        # Test verschiedene Windrichtungen
        test_cases = [
            (0, 'N'),
            (45, 'NO'),
            (90, 'O'),
            (135, 'SO'),
            (180, 'S'),
            (225, 'SW'),
            (270, 'W'),
            (315, 'NW'),
            (360, 'N')
        ]
        
        for degrees, expected in test_cases:
            with self.subTest(degrees=degrees):
                self.assertEqual(windrichtung_zu_text(degrees), expected)

    def test_windrichtung_zu_text_invalid(self):
        """Test ungültige Windrichtung"""
        # Überprüfe, ob der richtige Fehler geworfen wird
        with self.assertRaises(ValueError):
            windrichtung_zu_text(-1)
        
        with self.assertRaises(ValueError):
            windrichtung_zu_text(361)

if __name__ == '__main__':
    unittest.main() 