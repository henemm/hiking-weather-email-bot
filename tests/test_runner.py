from wetter.analyse import generiere_wetterbericht


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
    assert "Kühl" in report or "Kalt" in report or "Warm" in report
