from typing import Dict, Any
import yaml
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Basis-Exception für Konfigurationsfehler"""
    pass

class ConfigValidationError(ConfigError):
    """Fehler bei der Konfigurationsvalidierung"""
    pass

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validiert die Konfiguration.
    
    Args:
        config: Die zu validierende Konfiguration
        
    Raises:
        ConfigValidationError: Bei ungültiger Konfiguration
    """
    # Pflichtfelder
    required_fields = ['startdatum', 'smtp', 'schwellen']
    for field in required_fields:
        if field not in config:
            raise ConfigValidationError(f"Fehlendes Pflichtfeld: {field}")
    
    # Validierung des Startdatums
    if not isinstance(config['startdatum'], str):
        raise ConfigValidationError("Ungültiger Typ für startdatum (muss String sein)")
    try:
        datetime.strptime(config['startdatum'], '%Y-%m-%d')
    except ValueError:
        raise ConfigValidationError("Ungültiges Startdatum-Format (erwartet: YYYY-MM-DD)")
    
    # Validierung der SMTP-Konfiguration
    smtp_fields = ['host', 'port', 'user', 'to']
    for field in smtp_fields:
        if field not in config['smtp']:
            raise ConfigValidationError(f"Fehlendes SMTP-Feld: {field}")
    
    # Validierung des SMTP-Ports
    if not isinstance(config['smtp']['port'], int) or not (0 < config['smtp']['port'] < 65536):
        raise ConfigValidationError("Ungültiger SMTP-Port (muss zwischen 1 und 65535 liegen)")
    
    # Validierung der Schwellenwerte
    schwellen_fields = ['regen', 'gewitter', 'delta_prozent', 'hitze', 'wind']
    for field in schwellen_fields:
        if field not in config['schwellen']:
            raise ConfigValidationError(f"Fehlender Schwellenwert: {field}")
    
    # Validierung der Schwellenwerte-Typen
    for field in schwellen_fields:
        if not isinstance(config['schwellen'][field], (int, float)) or config['schwellen'][field] < 0:
            raise ConfigValidationError(f"Ungültiger Schwellenwert für {field} (muss >= 0 sein)")

def lade_konfiguration(config_path: str) -> Dict[str, Any]:
    """
    Lädt und validiert die Konfiguration aus einer YAML-Datei.
    
    Args:
        config_path: Pfad zur Konfigurationsdatei
        
    Returns:
        Die validierte Konfiguration
        
    Raises:
        ConfigError: Bei Fehlern beim Laden oder Validieren der Konfiguration
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(f"Konfigurationsdatei nicht gefunden: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Ungültiges YAML-Format: {str(e)}")
    except Exception as e:
        raise ConfigError(f"Unerwarteter Fehler beim Laden der Konfiguration: {str(e)}")
    
    try:
        validate_config(config)
    except ConfigValidationError as e:
        raise ConfigError(f"Konfigurationsvalidierung fehlgeschlagen: {str(e)}")
    
    return config

# Globale Konfiguration
# try:
#     config = lade_konfiguration('config.yaml')
# except ConfigError as e:
#     logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
#     raise 

def validiere_konfiguration(config: Dict[str, Any]) -> None:
    """Validiert die Konfiguration und wirft ConfigError bei Problemen."""
    # Prüfe erforderliche Felder
    erforderliche_felder = [
        "schwellenwerte",
        "start_datum",
        "smtp",
        "modus",
        "etappen"
    ]
    
    for feld in erforderliche_felder:
        if feld not in config:
            raise ConfigError(f"Fehlendes Konfigurationsfeld: {feld}")
    
    # Validiere Schwellenwerte
    schwellenwerte = config["schwellenwerte"]
    erforderliche_schwellenwerte = [
        "temp_min",
        "temp_max",
        "regen_min",
        "wind_min",
        "gewitter_min"
    ]
    
    for schwellenwert in erforderliche_schwellenwerte:
        if schwellenwert not in schwellenwerte:
            raise ConfigError(f"Fehlende Schwellenwerte: {schwellenwert}")
    
    # Validiere SMTP-Konfiguration
    smtp = config["smtp"]
    erforderliche_smtp_felder = [
        "server",
        "port",
        "username",
        "password",
        "absender",
        "empfaenger"
    ]
    
    for feld in erforderliche_smtp_felder:
        if feld not in smtp:
            raise ConfigError(f"Fehlende SMTP-Konfiguration: {feld}")
    
    # Validiere Modus
    if config["modus"] not in ["tag", "etappe"]:
        raise ConfigError("Ungültiger Modus. Muss 'tag' oder 'etappe' sein.")
    
    # Validiere Etappen
    if not isinstance(config["etappen"], list):
        raise ConfigError("Etappen müssen als Liste definiert sein.")
    
    for etappe in config["etappen"]:
        if not isinstance(etappe, dict):
            raise ConfigError("Etappen müssen als Dictionaries definiert sein.")
        
        erforderliche_etappen_felder = ["name", "datum", "start", "ziel"]
        for feld in erforderliche_etappen_felder:
            if feld not in etappe:
                raise ConfigError(f"Fehlende Etappenfelder: {feld}") 