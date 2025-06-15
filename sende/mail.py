import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv(".env")
GMAIL_APP_PW = os.getenv("GMAIL_APP_PW")

def sende_email(text):
    msg = EmailMessage()
    msg.set_content(text)
    msg["Subject"] = "Wetterwarnung GR20"
    msg["From"] = os.getenv("GMAIL_USER")
    msg["To"] = os.getenv("GMAIL_TO")

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(msg["From"], GMAIL_APP_PW)
        smtp.send_message(msg)
