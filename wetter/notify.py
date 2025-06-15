import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import yaml

# .env mit sensiblen Zugangsdaten laden
load_dotenv(".credentials.env")

# SMTP-Kennwort aus .env
GMAIL_APP_PW = os.getenv("GMAIL_APP_PW")

# Konfiguration aus YAML
with open("config.yaml") as f:
    config = yaml.safe_load(f)

SMTP_HOST = config["smtp"]["host"]
SMTP_PORT = config["smtp"]["port"]
SMTP_USER = config["smtp"]["user"]
EMAIL_TO = config["smtp"]["to"]
EMAIL_SUBJECT = config["smtp"].get("subject", "Wetterwarnung")


def sende_email(text):
    msg = EmailMessage()
    msg.set_content(text)
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, GMAIL_APP_PW)
        smtp.send_message(msg)
