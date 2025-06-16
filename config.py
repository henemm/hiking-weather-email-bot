import yaml
import os
import logging
import sys
from datetime import date, datetime
from typing import Dict, Any, Union, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Basis-Exception für Konfigurationsfehler"""
    pass

class ConfigValidationError(ConfigError):
    """Fehler bei der Validierung der Konfiguration"""
    pass

class ConfigFileError(ConfigError):
    """Fehler beim Lesen der Konfigurationsdatei"""
    pass

def sicherstelle_verzeichnis(pfad: str) -> None:
    """Stellt sicher, dass ein Verzeichnis existiert"""
    try:
        Path(pfad).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ConfigError(f"Konnte Verzeichnis {pfad} nicht erstellen: {str(e)}")

def validiere_schwellenwerte(schwellen: Dict[str, Any]) -> None:
    """
    Validiert die Schwellenwerte auf Plausibilität.
    
    Args:
        schwellen: Dictionary mit Schwellenwerten
        
    Raises:
        ConfigValidationError: Bei ungültigen Werten
    """
    if not isinstance(schwellen, dict):
        raise ConfigValidationError("Schwellenwerte müssen ein Dictionary sein")

    min_max_values = {
        "regen": (0, 100),
        "gewitter": (0, 100),
        "wind": (0, 200),
        "hitze": (-20, 50),
        "delta_prozent": (0, 100),
        "gewitter_ab_uhrzeit": (0, 23)
    }
    
    # Prüfe ob alle erforderlichen Schwellenwerte vorhanden sind
    fehlende_schwellen = set(min_max_values.keys()) - set(schwellen.keys())
    if fehlende_schwellen:
        raise ConfigValidationError(f"Fehlende Schwellenwerte: {', '.join(fehlende_schwellen)}")
    
    # Prüfe jeden Schwellenwert
    for key, (min_val, max_val) in min_max_values.items():
        value = schwellen.get(key)
        if not isinstance(value, (int, float)):
            raise ConfigValidationError(f"Schwellenwert für '{key}' muss eine Zahl sein")
        if not min_val <= value <= max_val:
            raise ConfigValidationError(
                f"Schwellenwert für '{key}' muss zwischen {min_val} und {max_val} liegen"
            )

def validiere_smtp_config(smtp: Dict[str, Any]) -> None:
    """
    Validiert die SMTP-Konfiguration.
    
    Args:
        smtp: Dictionary mit SMTP-Konfiguration
        
    Raises:
        ConfigValidationError: Bei ungültiger Konfiguration
    """
    if not isinstance(smtp, dict):
        raise ConfigValidationError("SMTP-Konfiguration muss ein Dictionary sein")

    required_fields = ["host", "user", "to"]
    for field in required_fields:
        if not smtp.get(field):
            raise ConfigValidationError(f"SMTP-Konfiguration unvollständig ({field} fehlt)")
        if not isinstance(smtp[field], str):
            raise ConfigValidationError(f"SMTP-Feld '{field}' muss ein String sein")

    # Port validieren
    port = smtp.get("port", 587)
    if not isinstance(port, int) or port not in [465, 587]:
        raise ConfigValidationError("SMTP-Port muss 465 (SSL) oder 587 (STARTTLS) sein")

def validiere_umgebungsvariablen() -> None:
    """
    Validiert die erforderlichen Umgebungsvariablen.
    
    Raises:
        ConfigError: Bei fehlenden oder ungültigen Umgebungsvariablen
    """
    required_vars = {
        "GMAIL_APP_PW": "E-Mail-Passwort",
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        raise ConfigError(
            f"Fehlende Umgebungsvariablen: {', '.join(missing_vars)}\n"
            "Bitte erstellen Sie eine .env Datei mit diesen Variablen."
        )

def lade_config(pfad: str = "config.yaml") -> Dict[str, Any]:
    """
    Lädt und validiert die Konfiguration.
    
    Args:
        pfad: Pfad zur Konfigurationsdatei
        
    Returns:
        Dictionary mit der validierten Konfiguration
        
    Raises:
        ConfigError: Bei Konfigurationsfehlern
    """
    # Lade .env-Datei
    load_dotenv()
    
    # Stelle sicher, dass das Log-Verzeichnis existiert
    sicherstelle_verzeichnis("logs")
    
    # Validiere Umgebungsvariablen
    validiere_umgebungsvariablen()
    
    # Lade Konfigurationsdatei
    try:
        with open(pfad, "r") as f:
            config = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigFileError(f"Fehler beim Lesen der Konfigurationsdatei: {str(e)}")

    if not isinstance(config, dict):
        raise ConfigValidationError("Konfiguration muss ein Dictionary sein")

    # Startdatum prüfen
    startdatum_raw = config.get("startdatum")
    if not isinstance(startdatum_raw, (str, date)):
        raise ConfigValidationError("Startdatum fehlt oder ist kein gültiges Datum")
    
    if isinstance(startdatum_raw, str):
        try:
            config["startdatum"] = date.fromisoformat(startdatum_raw)
        except ValueError:
            raise ConfigValidationError("Startdatum ist kein gültiges ISO-Datum (YYYY-MM-DD)")

    # SMTP-Konfiguration prüfen
    smtp = config.get("smtp", {})
    validiere_smtp_config(smtp)

    # Schwellwerte prüfen
    schwellen = config.get("schwellen", {})
    validiere_schwellenwerte(schwellen)
    
    logger.info("Konfiguration erfolgreich geladen und validiert")
    return config

def get_config() -> Dict[str, Any]:
    """
    Lädt die Konfiguration mit Fehlerbehandlung.
    
    Returns:
        Dictionary mit der Konfiguration
        
    Raises:
        SystemExit: Bei kritischen Fehlern
    """
    try:
        return lade_config()
    except ConfigError as e:
        logger.error(f"Konfigurationsfehler: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Laden der Konfiguration: {str(e)}")
        sys.exit(1)

# Globale Konfiguration
config = get_config()