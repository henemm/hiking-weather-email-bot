import smtplib
import os
import logging
import time
from email.message import EmailMessage
from email.utils import formatdate
from typing import Optional, List

logger = logging.getLogger(__name__)

class EmailError(Exception):
    """Basis-Exception für E-Mail-bezogene Fehler"""
    pass

class EmailConfigError(EmailError):
    """Fehler in der E-Mail-Konfiguration"""
    pass

class EmailSendError(EmailError):
    """Fehler beim Senden der E-Mail"""
    pass

def validiere_email_adresse(email: str) -> bool:
    """
    Validiert eine E-Mail-Adresse.
    
    Args:
        email: Die zu validierende E-Mail-Adresse
        
    Returns:
        True wenn die E-Mail-Adresse gültig ist
    """
    if not isinstance(email, str):
        return False
    
    # Einfache Validierung
    if '@' not in email or '.' not in email:
        return False
    
    # Prüfe auf verbotene Zeichen
    verbotene_zeichen = [' ', '<', '>', '(', ')', '[', ']', '\\', ',', ';', ':', '"']
    return not any(zeichen in email for zeichen in verbotene_zeichen)

def erstelle_email_message(
    text: str,
    subject: str,
    from_addr: str,
    to_addr: str
) -> EmailMessage:
    """
    Erstellt eine E-Mail-Nachricht.
    
    Args:
        text: Der E-Mail-Text
        subject: Der Betreff
        from_addr: Absender-Adresse
        to_addr: Empfänger-Adresse
        
    Returns:
        EmailMessage-Objekt
        
    Raises:
        EmailConfigError: Bei ungültigen E-Mail-Adressen
    """
    if not validiere_email_adresse(from_addr):
        raise EmailConfigError(f"Ungültige Absender-E-Mail-Adresse: {from_addr}")
    if not validiere_email_adresse(to_addr):
        raise EmailConfigError(f"Ungültige Empfänger-E-Mail-Adresse: {to_addr}")
    
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(text)
    
    return msg

def sende_email(
    text: str,
    smtp_config: dict,
    max_retries: int = 3,
    retry_delay: float = 5.0,
    timeout: int = 30
) -> None:
    """
    Sendet eine E-Mail mit Wetterwarnung.
    
    Args:
        text: Der zu sendende Text
        smtp_config: SMTP-Konfiguration als Dictionary
        max_retries: Maximale Anzahl von Versuchen bei Fehlern
        retry_delay: Wartezeit zwischen Versuchen in Sekunden
        timeout: Timeout für SMTP-Operationen in Sekunden
        
    Raises:
        EmailError: Bei Problemen mit dem E-Mail-Versand
    """
    # SMTP-Konfiguration verwenden
    host = smtp_config["host"]
    port = smtp_config.get("port", 587)
    user = smtp_config["user"]
    to_addr = smtp_config["to"]
    subject = smtp_config.get("subject", "Wetterwarnung")
    
    # Überprüfe Umgebungsvariablen
    password = os.getenv("GMAIL_APP_PW")
    if not password:
        raise EmailError("E-Mail-Passwort nicht in Umgebungsvariablen gefunden (GMAIL_APP_PW)")
    
    # Erstelle E-Mail-Nachricht
    msg = EmailMessage()
    msg.set_content(text)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)
    
    use_ssl = port == 465
    errors: List[str] = []
    for attempt in range(max_retries):
        try:
            if use_ssl:
                with smtplib.SMTP_SSL(host, port, timeout=timeout) as smtp:
                    smtp.login(user, password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=timeout) as smtp:
                    smtp.starttls()
                    smtp.login(user, password)
                    smtp.send_message(msg)
            logger.info(f"E-Mail erfolgreich an {to_addr} gesendet.")
            return
        except Exception as e:
            logger.error(f"Fehler beim Senden der E-Mail (Versuch {attempt+1}): {str(e)}")
            errors.append(str(e))
            time.sleep(retry_delay)
    raise EmailError(f"E-Mail konnte nach {max_retries} Versuchen nicht gesendet werden: {'; '.join(errors)}")