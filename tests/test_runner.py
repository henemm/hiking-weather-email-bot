from wetter.analyse import generiere_wetterbericht
import pytest
from unittest.mock import patch, MagicMock
import argparse
import sys


def test_generate_weather_report():
    """Test der Wetterbericht-Generierung."""
    # Testdaten
    test_data = {
        "nacht_temp": 5.0,
        "hitze": 25.0,
        "regen": 30.0,
        "wind": 15.0,
        "gewitter": 10.0,
    }
    # Generiere Bericht
    report = generiere_wetterbericht(**test_data)
    # Prüfe Ergebnis
    assert isinstance(report, str)
    assert len(report) > 0
    assert "Nachttemperatur" in report or "Tagestemperatur" in report

# --- Integrationstest für den Produktivablauf ---
abend_mock = {
    'nacht_temp': 15.0,
    'hitze': 25.0,
    'regen': 10.0,
    'wind': 12.0,
    'gewitter': 0.0,
    'gewitter_plus1': 0.0
}

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_normalfall(mock_send_email, mock_hole_wetterdaten):
    mock_hole_wetterdaten.return_value = abend_mock
    mock_send_email.return_value = True
    from main import main
    with patch.object(sys, 'argv', ['main.py', '--modus', 'abend']):
        main()
    mock_send_email.assert_called_once()

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_api_error(mock_send_email, mock_hole_wetterdaten):
    mock_hole_wetterdaten.side_effect = Exception("API down")
    mock_send_email.return_value = True
    from main import main
    with patch.object(sys, 'argv', ['main.py', '--modus', 'abend']):
        with pytest.raises(Exception):
            main()

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_extremwetter(mock_send_email, mock_hole_wetterdaten):
    mock_hole_wetterdaten.return_value = {
        'nacht_temp': 30.0,
        'hitze': 45.0,
        'regen': 100.0,
        'wind': 100.0,
        'gewitter': 100.0,
        'gewitter_plus1': 100.0
    }
    mock_send_email.return_value = True
    from main import main
    with patch.object(sys, 'argv', ['main.py', '--modus', 'abend']):
        main()
    mock_send_email.assert_called_once()

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_leere_daten(mock_send_email, mock_hole_wetterdaten):
    mock_hole_wetterdaten.return_value = {
        'nacht_temp': None,
        'hitze': None,
        'regen': None,
        'wind': None,
        'gewitter': None,
        'gewitter_plus1': None
    }
    mock_send_email.return_value = True
    from main import main
    with patch.object(sys, 'argv', ['main.py', '--modus', 'abend']):
        with pytest.raises(Exception):
            main()

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_retry_mechanism(mock_send_email, mock_hole_wetterdaten):
    """Test retry mechanism for transient API failures"""
    # Simulate two failures then success
    mock_hole_wetterdaten.side_effect = [
        Exception("Temporary API Error"),
        Exception("Temporary API Error"),
        abend_mock
    ]
    mock_send_email.return_value = True
    from main import main
    with patch.object(sys, 'argv', ['main.py', '--modus', 'abend']):
        main()
    # Should have retried 3 times
    assert mock_hole_wetterdaten.call_count == 3
    mock_send_email.assert_called_once()

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_partial_data(mock_send_email, mock_hole_wetterdaten):
    """Test handling of partial weather data"""
    partial_data = {
        'nacht_temp': 15.0,
        'hitze': None,  # Missing data
        'regen': 10.0,
        'wind': 12.0,
        'gewitter': 0.0,
        'gewitter_plus1': 0.0
    }
    mock_hole_wetterdaten.return_value = partial_data
    mock_send_email.return_value = True
    from main import main
    with patch.object(sys, 'argv', ['main.py', '--modus', 'abend']):
        main()
    mock_send_email.assert_called_once()

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_multiple_stages(mock_send_email, mock_hole_wetterdaten):
    """Test processing multiple stages in sequence"""
    stages = [
        {'name': 'Stage 1', 'punkte': [{'lat': 47.0, 'lon': 11.0}]},
        {'name': 'Stage 2', 'punkte': [{'lat': 47.1, 'lon': 11.1}]}
    ]
    mock_hole_wetterdaten.side_effect = [abend_mock, abend_mock]
    mock_send_email.return_value = True
    from main import main
    with patch.object(sys, 'argv', ['main.py', '--modus', 'abend']):
        main()
    assert mock_hole_wetterdaten.call_count == 2
    assert mock_send_email.call_count == 2

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_config_validation(mock_send_email, mock_hole_wetterdaten):
    """Test configuration validation during runtime"""
    mock_hole_wetterdaten.return_value = abend_mock
    mock_send_email.return_value = True
    from main import main
    # Test with invalid configuration
    with patch.object(sys, 'argv', ['main.py', '--modus', 'invalid_mode']):
        with pytest.raises(ValueError):
            main()
    # Test with missing configuration
    with patch.object(sys, 'argv', ['main.py']):
        with pytest.raises(ValueError):
            main()

@patch('wetter.fetch.hole_wetterdaten')
@patch('emailversand.sende_email')
def test_end_to_end_logging(mock_send_email, mock_hole_wetterdaten):
    """Test logging functionality during execution"""
    import logging
    from io import StringIO
    log_stream = StringIO()
    logging.basicConfig(stream=log_stream, level=logging.INFO)
    
    mock_hole_wetterdaten.return_value = abend_mock
    mock_send_email.return_value = True
    from main import main
    with patch.object(sys, 'argv', ['main.py', '--modus', 'abend']):
        main()
    
    log_output = log_stream.getvalue()
    assert "Starting weather report generation" in log_output
    assert "Weather data fetched successfully" in log_output
    assert "Email sent successfully" in log_output
