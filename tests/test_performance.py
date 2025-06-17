import unittest
import time
from unittest.mock import patch
import pytest
from wetter.wetterdaten import hole_wetterdaten
from wetter.analyse import generiere_wetterbericht
from wetter.kurztext import generiere_kurznachricht

class TestPerformance(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit Testdaten"""
        self.test_points = [
            {"lat": 42.5105, "lon": 8.8562},
            {"lat": 42.4958, "lon": 8.9216},
            {"lat": 42.4800, "lon": 8.9500}
        ]
        
        self.mock_weather_data = {
            'hourly': {
                'temperature_2m': [15.0, 20.0, 18.0],
                'apparent_temperature': [14.0, 19.0, 17.0],
                'windspeed_10m': [10.0, 15.0, 12.0],
                'winddirection_10m': [90, 180, 135],
                'precipitation': [2.5, 5.0, 3.0],
                'thunderstorm': [True, False, True],
                'time': ['2024-06-01T12:00:00', '2024-06-01T13:00:00', '2024-06-01T14:00:00']
            }
        }

    def test_weather_data_fetch_performance(self):
        """Test performance of weather data fetching"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = self.mock_weather_data
            
            # Measure time for single point
            start_time = time.time()
            hole_wetterdaten(42.5105, 8.8562, config={})
            single_point_time = time.time() - start_time
            
            # Measure time for multiple points
            start_time = time.time()
            hole_wetterdaten(self.test_points, "abend")
            multiple_points_time = time.time() - start_time
            
            # Assert reasonable performance
            self.assertLess(single_point_time, 1.0)  # Should take less than 1 second
            self.assertLess(multiple_points_time, 3.0)  # Should take less than 3 seconds for multiple points

    def test_report_generation_performance(self):
        """Test performance of report generation"""
        test_data = {
            "nacht_temp": 15.0,
            "hitze": 25.0,
            "regen": 20.0,
            "wind": 15.0,
            "gewitter": 5.0,
            "regen_ab": "14:00",
            "gewitter_ab": "15:00"
        }
        
        # Measure time for report generation
        start_time = time.time()
        for _ in range(100):  # Generate 100 reports
            generiere_wetterbericht(**test_data)
        total_time = time.time() - start_time
        
        # Assert reasonable performance
        self.assertLess(total_time, 1.0)  # Should generate 100 reports in less than 1 second

    def test_concurrent_requests(self):
        """Test performance under concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def worker():
            try:
                with patch('requests.get') as mock_get:
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = self.mock_weather_data
                    result = hole_wetterdaten(42.5105, 8.8562, config={})
                    results.put(result)
            except Exception as e:
                errors.put(e)
        
        # Create and start multiple threads
        threads = []
        for _ in range(10):  # 10 concurrent requests
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Check results
        self.assertEqual(results.qsize(), 10)  # All requests should succeed
        self.assertEqual(errors.qsize(), 0)  # No errors should occur

    def test_memory_usage(self):
        """Test memory usage during report generation"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate multiple reports
        test_data = {
            "nacht_temp": 15.0,
            "hitze": 25.0,
            "regen": 20.0,
            "wind": 15.0,
            "gewitter": 5.0
        }
        
        reports = []
        for _ in range(1000):
            reports.append(generiere_wetterbericht(**test_data))
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Assert reasonable memory usage
        self.assertLess(memory_increase, 50 * 1024 * 1024)  # Less than 50MB increase

    def test_api_rate_limiting(self):
        """Test handling of API rate limiting"""
        with patch('requests.get') as mock_get:
            # Simulate rate limiting
            mock_get.side_effect = [
                Exception("Rate limit exceeded"),
                Exception("Rate limit exceeded"),
                type('Response', (), {'status_code': 200, 'json': lambda: self.mock_weather_data})()
            ]
            
            start_time = time.time()
            result = hole_wetterdaten(42.5105, 8.8562, config={})
            total_time = time.time() - start_time
            
            # Assert retry mechanism works
            self.assertIsNotNone(result)
            self.assertLess(total_time, 5.0)  # Should handle rate limiting in reasonable time

if __name__ == '__main__':
    unittest.main() 