import unittest
from datetime import datetime
from src.weather.models import WeatherPoint, WeatherData, ReportMode, WeatherReport
from src.report.generator import ReportGenerator, generate_report

class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        # Beispiel-Wetterdaten für Tests mit unterschiedlichen Schwellen- und Maximalwerten
        self.weather_data = WeatherData(
            points=[
                WeatherPoint(
                    latitude=47.3769,
                    longitude=8.5417,
                    elevation=400,
                    time=datetime(2023, 1, 1, 10, 0),
                    temperature=18,
                    feels_like=16,
                    precipitation=2,
                    rain_probability=25,
                    thunderstorm_probability=25,
                    wind_speed=10,
                    wind_direction=180,
                    cloud_cover=50
                ),
                WeatherPoint(
                    latitude=47.3769,
                    longitude=8.5417,
                    elevation=400,
                    time=datetime(2023, 1, 1, 15, 0),
                    temperature=22,
                    feels_like=20,
                    precipitation=5,
                    rain_probability=60,
                    thunderstorm_probability=60,
                    wind_speed=15,
                    wind_direction=200,
                    cloud_cover=70
                )
            ],
            rain_time_threshold="10:00",
            rain_time_max="15:00",
            thunder_time_threshold="12:00",
            thunder_time_max="15:00"
        )

    def test_evening_report(self):
        report = generate_report(
            mode=ReportMode.EVENING,
            stage_name="Etappe 1",
            date=datetime(2023, 1, 1),
            weather_data=self.weather_data
        )
        print("\nEVENING REPORT OUTPUT:\n" + report.text)
        self.assertIn("Regenwahrscheinlichkeit: 25%@10:00 (60%@15:00)", report.text)
        self.assertIn("Niederschlagsmenge: 2mm@10:00 (5mm@15:00)", report.text)
        self.assertIn("Gewitterwahrscheinlichkeit: 25%@10:00 (60%@15:00)", report.text)

    def test_morning_report_with_time_values(self):
        """Test that morning report shows time values for rain probability and amount"""
        report = generate_report(
            mode=ReportMode.MORNING,
            stage_name="Etappe 1",
            date=datetime(2023, 1, 1),
            weather_data=self.weather_data,
            next_day_thunderstorm=30
        )
        
        # Verify that the report contains time values
        self.assertIn("Regenwahrscheinlichkeit:", report.text)
        self.assertIn("Niederschlagsmenge:", report.text)
        self.assertIn("Gewitterwahrscheinlichkeit:", report.text)
        
        # Check that time values are present (should contain @ symbol)
        self.assertIn("@", report.text)
        
        print("\nMORNING REPORT OUTPUT:\n" + report.text)

    def test_morning_report(self):
        report = generate_report(
            mode=ReportMode.MORNING,
            stage_name="Etappe 1",
            date=datetime(2023, 1, 1),
            weather_data=self.weather_data,
            next_day_thunderstorm=30
        )
        print("\nMORNING REPORT OUTPUT:\n" + report.text)
        self.assertIn("Regenwahrscheinlichkeit: 25%@10:00 (60%@15:00)", report.text)
        self.assertIn("Niederschlagsmenge: 2mm@10:00 (5mm@15:00)", report.text)
        self.assertIn("Gewitterwahrscheinlichkeit: 25%@10:00 (60%@15:00)", report.text)
        self.assertIn("Gewitterwahrscheinlichkeit für morgen:", report.text)
        self.assertIn("30%", report.text)

    def test_day_warning(self):
        report = generate_report(
            mode=ReportMode.DAY,
            stage_name="Etappe 1",
            date=datetime(2023, 1, 1),
            weather_data=self.weather_data,
            thunderstorm_plus1=70
        )
        print("\nDAY WARNING REPORT OUTPUT:\n" + report.text)
        self.assertIn("Regenwahrscheinlichkeit: 25%@10:00 (60%@15:00)", report.text)
        self.assertIn("Niederschlagsmenge: 2mm@10:00 (5mm@15:00)", report.text)
        self.assertIn("Gewitterwahrscheinlichkeit: 25%@10:00 (60%@15:00)", report.text)

    def test_inreach_morning_report(self):
        """Test that InReach morning report shows rain warnings with time values"""
        report = generate_report(
            mode=ReportMode.MORNING,
            stage_name="E6 Manganu",
            date=datetime(2025, 6, 20),
            weather_data=self.weather_data,
            next_day_thunderstorm=30
        )
        
        # Create ReportGenerator and test InReach format
        from src.config import get_config
        config = get_config()
        report_generator = ReportGenerator(config["schwellen"])
        
        inreach_text = report_generator.generate_inreach(report)
        
        print("\nINREACH MORNING REPORT OUTPUT:\n" + inreach_text)
        
        # Verify that the InReach report contains rain information
        self.assertIn("Regen", inreach_text)
        self.assertIn("Gewitter", inreach_text)
        self.assertIn("Wind", inreach_text)
        self.assertIn("Hitze", inreach_text)
        
        # Check that time values are present (should contain @ symbol)
        self.assertIn("@", inreach_text)

    def test_inreach_evening_report(self):
        """Test that InReach evening report shows rain warnings with time values"""
        report = generate_report(
            mode=ReportMode.EVENING,
            stage_name="E6 Manganu",
            date=datetime(2025, 6, 20),
            weather_data=self.weather_data
        )
        
        # Create ReportGenerator and test InReach format
        from src.config import get_config
        config = get_config()
        report_generator = ReportGenerator(config["schwellen"])
        
        inreach_text = report_generator.generate_inreach(report)
        
        print("\nINREACH EVENING REPORT OUTPUT:\n" + inreach_text)
        
        # Verify that the InReach report contains rain information
        self.assertIn("Regen", inreach_text)
        self.assertIn("Gewitter", inreach_text)
        self.assertIn("Wind", inreach_text)
        self.assertIn("Hitze", inreach_text)
        self.assertIn("Nacht", inreach_text)
        
        # Check that time values are present (should contain @ symbol)
        self.assertIn("@", inreach_text)

if __name__ == '__main__':
    unittest.main() 