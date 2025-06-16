import unittest
from datetime import date
from unittest.mock import MagicMock, patch

import requests

from wetter.fetch import (WeatherAPIConnectionError, WeatherAPIRateLimitError,
                          WeatherAPIResponseError, fetch_weather_data,
                          hole_wetterdaten)


class TestWeatherAPI(unittest.TestCase):
    def setUp(self):
        """Testdaten vorbereiten"""
        self.test_location = {"lat": 42.5105, "lon": 8.8562}
        self.test_date = date(2024, 3, 15)

        # Mock-API-Antwort
        self.mock_response = {
            "daily": {
                "temperature_2m_min": [15.0],
                "temperature_2m_max": [25.0],
                "apparent_temperature_max": [25.0],
                "precipitation_probability_max": [30],
                "wind_speed_10m_max": [20.0],
                "wind_gusts_10m_max": [30.0],
            },
            "hourly": {
                "temperature_2m": [18.0, 17.0],
                "apparent_temperature": [17.0, 16.0],
                "precipitation_probability": [20, 30],
                "wind_speed_10m": [15.0, 16.0],
                "wind_gusts_10m": [22.0, 23.0],
                "thunderstorm_probability": [5, 10],
            },
        }

    @patch("requests.get")
    def test_successful_api_call(self, mock_get):
        """Test erfolgreicher API-Aufruf"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_response
        mock_get.return_value = mock_response

        result = fetch_weather_data(
            self.test_location["lat"], self.test_location["lon"], self.test_date
        )

        self.assertEqual(result, self.mock_response)
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_rate_limit_handling(self, mock_get):
        """Test Rate Limit Behandlung"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with self.assertRaises(WeatherAPIRateLimitError):
            fetch_weather_data(
                self.test_location["lat"], self.test_location["lon"], self.test_date
            )

    @patch("requests.get")
    def test_invalid_response_format(self, mock_get):
        """Test ungültiges Antwortformat"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "format"}
        mock_get.return_value = mock_response

        with self.assertRaises(WeatherAPIResponseError):
            fetch_weather_data(
                self.test_location["lat"], self.test_location["lon"], self.test_date
            )

    @patch("requests.get")
    def test_connection_error(self, mock_get):
        """Test Verbindungsfehler"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with self.assertRaises(WeatherAPIConnectionError):
            fetch_weather_data(
                self.test_location["lat"], self.test_location["lon"], self.test_date
            )

    def test_hole_wetterdaten_aggregation(self):
        """Test Aggregation mehrerer Wetterpunkte"""
        test_points = [{"lat": 42.5105, "lon": 8.8562}, {"lat": 42.4958, "lon": 8.9216}]

        with patch("wetter.fetch.fetch_weather_data") as mock_fetch:
            mock_fetch.return_value = self.mock_response
            result = hole_wetterdaten(test_points, "abend")

            # Prüfe die erwarteten Felder
            expected_fields = [
                "nacht_temp",
                "hitze",
                "regen",
                "wind",
                "gewitter",
            ]
            for field in expected_fields:
                self.assertIn(field, result)


if __name__ == "__main__":
    unittest.main()
