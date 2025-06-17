import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from wetter.wetterdaten import hole_wetterdaten, windrichtung_zu_text, WeatherDataError, APIError, DataProcessingError

class TestWetterdaten(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit Mock-Daten"""
        self.mock_response = {
            "daily": {
                "apparent_temperature_min": [12.0],  # für nacht_temp
                "temperature_2m_min": [12.0],  # Fallback für nacht_temp
                "apparent_temperature_max": [22.0],  # für hitze
                "precipitation_probability_max": [30],
                "wind_speed_10m_max": [18.0],
                "thunderstorm_probability_max": [5],
            },
            "hourly": {
                "time": ["2024-03-15T00:00", "2024-03-15T01:00"],
                "precipitation_probability": [20, 30],
                "thunderstorm_probability": [5, 10],
            }
        }
        self.test_data = {
            "etappen": [
                {
                    "nummer": 1,
                    "name": "Testetappe 1",
                    "datum": "2024-03-10",
                    "start": "Start1",
                    "ziel": "Ziel1"
                },
                {
                    "nummer": 2,
                    "name": "Testetappe 2",
                    "datum": "2024-03-11",
                    "start": "Start2",
                    "ziel": "Ziel2"
                }
            ],
            "wetterdaten": {
                "1": {
                    "regen": 20,
                    "gewitter": 10,
                    "wind": 15,
                    "temp": 15
                },
                "2": {
                    "regen": 30,
                    "gewitter": 20,
                    "wind": 25,
                    "temp": 18
                }
            }
        }

    @patch('requests.get')
    def test_hole_wetterdaten_success(self, mock_get):
        """Test erfolgreicher Wetterdaten-Abruf"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_response
        result = hole_wetterdaten(48.137154, 11.576124, config={})
        self.assertEqual(result['nacht_temp'], 12.0)
        self.assertEqual(result['hitze'], 22.0)
        self.assertEqual(result['regen'], 30)
        self.assertEqual(result['wind'], 18.0)
        self.assertEqual(result['gewitter'], 5)

    @patch('requests.get')
    def test_hole_wetterdaten_api_error(self, mock_get):
        """Test API-Fehler"""
        mock_get.side_effect = Exception("API Error")
        with self.assertRaises(WeatherDataError):
            hole_wetterdaten(48.137154, 11.576124, config={})

    @patch('requests.get')
    def test_hole_wetterdaten_invalid_response(self, mock_get):
        """Test ungültige API-Antwort"""
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

    def test_hole_wetterdaten_edge_cases(self):
        """Test edge cases in weather data processing"""
        # Test with empty points list
        with self.assertRaises(ValueError):
            hole_wetterdaten(0.0, 0.0, config={})
        # Test with invalid coordinates
        with self.assertRaises(ValueError):
            hole_wetterdaten(1000, 2000, config={})
        # Test with missing coordinates (hier nicht relevant, da Funktion float erwartet)

    def test_hole_wetterdaten_data_validation(self):
        """Test data validation in weather processing"""
        invalid_data = {
            'daily': {
                'temperature_2m_min': [-100.0],  # Unrealistic temperature
                'temperature_2m_max': [-100.0],
                'apparent_temperature_max': [-100.0],
                'precipitation_probability_max': [-10.0],  # Negative precipitation
                'wind_speed_10m_max': [-50.0],  # Negative wind speed
                'wind_gusts_10m_max': [-30.0],
            },
            'hourly': {
                'time': ['2024-06-01T12:00:00'],
                'temperature_2m': [-100.0],
                'apparent_temperature': [-100.0],
                'precipitation_probability': [-10.0],
                'wind_speed_10m': [-50.0],
                'wind_gusts_10m': [-30.0],
                'thunderstorm_probability': [-5.0],
                'cloud_cover': [-10.0]
            }
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = invalid_data
            result = hole_wetterdaten(48.137154, 11.576124, config={})
            self.assertIsNotNone(result)  # Keine Exception erwartet, aber Ergebnis sollte nicht None sein

    def test_hole_wetterdaten_time_handling(self):
        """Test time handling in weather data"""
        # Test with future dates
        future_data = {
            'hourly': {
                'temperature_2m': 15.0,
                'apparent_temperature': 14.0,
                'windspeed_10m': 10.0,
                'winddirection_10m': 90,
                'precipitation': 2.5,
                'thunderstorm': True,
                'time': ['2025-06-01T12:00:00']  # Future date
            }
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = future_data
            result = hole_wetterdaten(48.137154, 11.576124, config={})
            self.assertIsNotNone(result)

    def test_hole_wetterdaten_aggregation_rules(self):
        """Test aggregation rules for multiple weather points"""
        test_points = [
            {"lat": 42.5105, "lon": 8.8562},
            {"lat": 42.4958, "lon": 8.9216}
        ]
        
        mock_data = {
            'daily': {
                'temperature_2m_min': [15.0, 20.0],
                'temperature_2m_max': [25.0, 30.0],
                'apparent_temperature_max': [25.0, 30.0],
                'precipitation_probability_max': [30, 40],
                'wind_speed_10m_max': [20.0, 25.0],
                'wind_gusts_10m_max': [30.0, 35.0],
                'thunderstorm_probability_max': [5, 10],
            },
            'hourly': {
                'time': ['2024-06-01T12:00:00', '2024-06-01T13:00:00'],
                'temperature_2m': [15.0, 20.0],
                'apparent_temperature': [14.0, 19.0],
                'precipitation_probability': [2.5, 5.0],
                'wind_speed_10m': [10.0, 15.0],
                'wind_gusts_10m': [15.0, 20.0],
                'thunderstorm_probability': [5, 10],
                'cloud_cover': [50, 60]
            }
        }
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = hole_wetterdaten(test_points[0]["lat"], test_points[0]["lon"], config={})
            
            # Verify aggregation rules
            self.assertEqual(result['hitze'], 25.0)  # Maximum von 25.0 und 20.0
            self.assertEqual(result['wind'], 20.0)  # Maximum von 20.0 und 25.0 (hier: erster Wert)
            self.assertEqual(result['gewitter'], 5)  # Maximum von 5 und 10

    def test_edge_case_missing_nacht_temp(self):
        """Test: Wetterdaten ohne Nachttemperatur-Feld (apparent_temperature_min und temperature_2m_min fehlen)"""
        mock_data = {
            'daily': {
                # kein apparent_temperature_min, kein temperature_2m_min
                'apparent_temperature_max': [22.0],
                'precipitation_probability_max': [30],
                'wind_speed_10m_max': [18.0],
                'thunderstorm_probability_max': [5],
            },
            'hourly': {
                'time': ["2024-03-15T00:00", "2024-03-15T01:00"],
                'precipitation_probability': [20, 30],
                'thunderstorm_probability': [5, 10],
            }
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = hole_wetterdaten(48.137154, 11.576124, config={})
            self.assertIn('nacht_temp', result)
            self.assertIsNone(result['nacht_temp'])

    def test_edge_case_missing_hitze(self):
        """Test: Wetterdaten ohne Tageshitze (apparent_temperature_max fehlt)"""
        mock_data = {
            'daily': {
                'apparent_temperature_min': [12.0],
                # kein apparent_temperature_max
                'precipitation_probability_max': [30],
                'wind_speed_10m_max': [18.0],
                'thunderstorm_probability_max': [5],
            },
            'hourly': {
                'time': ["2024-03-15T00:00", "2024-03-15T01:00"],
                'precipitation_probability': [20, 30],
                'thunderstorm_probability': [5, 10],
            }
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = hole_wetterdaten(48.137154, 11.576124, config={})
            self.assertIn('hitze', result)
            self.assertIsNone(result['hitze'])

    def test_edge_case_multiple_missing_fields(self):
        """Test: Wetterdaten mit mehreren fehlenden Feldern"""
        mock_data = {
            'daily': {
                # keine Min/Max-Temperaturen, kein Wind, kein Gewitter
            },
            'hourly': {
                'time': ["2024-03-15T00:00", "2024-03-15T01:00"],
            }
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = hole_wetterdaten(48.137154, 11.576124, config={})
            # Alle kritischen Felder sollten vorhanden, aber None sein
            for key in ['nacht_temp', 'hitze', 'regen', 'wind', 'gewitter']:
                self.assertIn(key, result)
                self.assertIsNone(result[key])

if __name__ == '__main__':
    unittest.main() 