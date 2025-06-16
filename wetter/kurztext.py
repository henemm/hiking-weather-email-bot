from datetime import datetime
from typing import Any, Dict, Optional, List
import logging
from .config import ConfigError

logger = logging.getLogger(__name__)

class TextGenerationError(Exception):
    """Basis-Exception für Fehler bei der Textgenerierung"""
    pass

class EtappeError(TextGenerationError):
    """Fehler bei der Etappenverarbeitung"""
    pass


def format_zeit(zeit: str) -> str:
    """
    Formatiert die Zeit im Format HH:MM zu HH.
    
    Args:
        zeit: Zeit im Format HH:MM
        
    Returns:
        Stunde ohne führende Null
        
    Raises:
        ValueError: Bei ungültigem Zeitformat
    """
    try:
        if not isinstance(zeit, str) or len(zeit) < 13:
            raise ValueError("Ungültiges Zeitformat")
        return zeit[11:13]
    except (IndexError, TypeError):
        raise ValueError("Ungültiges Zeitformat")


def formatiere_zeit(iso_zeit: Optional[str]) -> str:
    """
    Formatiert eine ISO-Zeit zu einer Stunde.
    
    Args:
        iso_zeit: Zeit im ISO-Format oder None
        
    Returns:
        Stunde als String oder leerer String bei None
    """
    if not iso_zeit:
        return ""
    try:
        zeit = datetime.fromisoformat(iso_zeit)
        return str(zeit.hour)
    except (ValueError, TypeError) as e:
        logger.warning(f"Fehler beim Formatieren der Zeit {iso_zeit}: {str(e)}")
        return ""


def get_current_etappe(start_date: str) -> Optional[int]:
    """
    Berechnet die aktuelle Etappe basierend auf dem Startdatum.
    
    Args:
        start_date: Startdatum im Format YYYY-MM-DD
        
    Returns:
        Etappennummer oder None bei Fehler
        
    Raises:
        EtappeError: Bei ungültigem Datumsformat oder zukünftigem Datum
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        today = datetime.now()
        days_diff = (today - start).days
        if days_diff < 0:
            raise EtappeError("Startdatum liegt in der Zukunft")
        return days_diff + 1  # +1 weil die erste Etappe am Starttag ist
    except ValueError as e:
        raise EtappeError(f"Ungültiges Datumsformat: {str(e)}")
    except Exception as e:
        logger.error(f"Fehler bei der Berechnung der aktuellen Etappe: {str(e)}")
        raise EtappeError(f"Fehler bei der Berechnung der aktuellen Etappe: {str(e)}")


def get_etappe_name(etappe_nummer: Optional[int], etappen_data: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """
    Holt den Namen der Etappe aus den Etappendaten.
    
    Args:
        etappe_nummer: Nummer der Etappe
        etappen_data: Liste der Etappendaten
        
    Returns:
        Name der Etappe oder None bei Fehler
    """
    try:
        if etappe_nummer is None or etappe_nummer <= 0:
            return None
        if not etappen_data:
            return f'Etappe {etappe_nummer}'
            
        # Etappen sind 0-basiert im Array, aber 1-basiert in der Nummerierung
        if etappe_nummer > len(etappen_data):
            logger.warning(f"Etappennummer {etappe_nummer} außerhalb des gültigen Bereichs")
            return f'Etappe {etappe_nummer}'
            
        etappe = etappen_data[etappe_nummer - 1]
        return etappe.get('name', f'Etappe {etappe_nummer}')
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Etappennamens: {str(e)}")
        return f'Etappe {etappe_nummer}'


def generiere_kurznachricht(
    wetterdaten: Dict[str, Any],
    modus: str = "abend",
    start_date: Optional[str] = None,
    etappen_data: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generiert eine kurze Wetternachricht basierend auf den Wetterdaten.
    
    Args:
        wetterdaten: Dictionary mit den Wetterdaten
        modus: Betriebsmodus ("morgen" oder "abend")
        start_date: Startdatum im Format YYYY-MM-DD
        etappen_data: Liste der Etappendaten
        config: Konfiguration
        
    Returns:
        Formatierte Wetternachricht
        
    Raises:
        TextGenerationError: Bei Fehlern bei der Textgenerierung
    """
    try:
        # Validiere die Eingabedaten
        if not wetterdaten:
            raise TextGenerationError("Keine Wetterdaten vorhanden")
        
        if modus not in ["morgen", "abend"]:
            raise TextGenerationError(f"Ungültiger Modus: {modus}")
        
        # Extrahiere die relevanten Daten
        temp = wetterdaten.get('temp')
        temp_gefuehlt = wetterdaten.get('temp_gefuehlt')
        wind_geschwindigkeit = wetterdaten.get('wind_geschwindigkeit')
        wind_richtung = wetterdaten.get('wind_richtung')
        regen = wetterdaten.get('regen')
        gewitter = wetterdaten.get('gewitter', False)
        regen_zeit = wetterdaten.get('regen_zeit')
        gewitter_zeit = wetterdaten.get('gewitter_zeit')
        
        # Validiere die erforderlichen Felder
        required_fields = ['temp', 'temp_gefuehlt', 'wind_geschwindigkeit', 'wind_richtung']
        for field in required_fields:
            if field not in wetterdaten:
                raise TextGenerationError(f"Fehlendes Pflichtfeld: {field}")
        
        # Bestimme die aktuelle Etappe und ihren Namen
        aktuelle_etappe = get_current_etappe(start_date) if start_date else None
        etappen_name = get_etappe_name(aktuelle_etappe, etappen_data) if etappen_data else None
        
        # Für den Morgenmodus
        if modus == "morgen":
            nacht_temp = wetterdaten.get('nacht_temp')
            nacht_temp_gefuehlt = wetterdaten.get('nacht_temp_gefuehlt')
            
            # Generiere die Morgennachricht
            nachricht = f"Wetterbericht Morgen:\n"
            
            # Temperaturinformationen
            if nacht_temp is not None and nacht_temp_gefuehlt is not None:
                nachricht += f"Temperatur: {nacht_temp}°C (gefühlt {nacht_temp_gefuehlt}°C)\n"
            else:
                nachricht += f"Aktuelle Temperatur: {temp}°C (gefühlt {temp_gefuehlt}°C)\n"
            
            # Windinformationen
            nachricht += f"Wind: {wind_geschwindigkeit} km/h aus {wind_richtung}\n"
            
            # Regeninformationen
            if regen is not None and regen > 0:
                nachricht += f"Regen: {regen} mm"
                if regen_zeit:
                    nachricht += f" ({formatiere_zeit(regen_zeit)})"
                nachricht += "\n"
            
            # Gewitterinformationen
            if gewitter:
                gewitter_text = "Gewitter"
                if etappen_name:
                    gewitter_text += f" für {etappen_name}"
                if gewitter_zeit:
                    gewitter_text += f" ({formatiere_zeit(gewitter_zeit)})"
                nachricht += f"{gewitter_text}\n"
            
            return nachricht
        
        # Für den Abendmodus (Standard)
        nachricht = f"Wetterbericht Abend:\n"
        nachricht += f"Temperatur: {temp}°C (gefühlt {temp_gefuehlt}°C)\n"
        nachricht += f"Wind: {wind_geschwindigkeit} km/h aus {wind_richtung}\n"
        
        if regen is not None and regen > 0:
            nachricht += f"Regen: {regen} mm"
            if regen_zeit:
                nachricht += f" ({formatiere_zeit(regen_zeit)})"
            nachricht += "\n"
        
        if gewitter:
            gewitter_text = "Gewitter"
            if etappen_name:
                gewitter_text += f" für {etappen_name}"
            if gewitter_zeit:
                gewitter_text += f" ({formatiere_zeit(gewitter_zeit)})"
            nachricht += f"{gewitter_text}\n"
        
        return nachricht
        
    except Exception as e:
        logger.error(f"Fehler beim Generieren der Kurznachricht: {str(e)}")
        raise TextGenerationError(f"Fehler bei der Textgenerierung: {str(e)}")
