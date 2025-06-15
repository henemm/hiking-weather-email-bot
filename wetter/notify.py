import smtplib, ssl, os, yaml
from email.message import EmailMessage
from dotenv import load_dotenv

def sende_email(text):
    load_dotenv()
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    msg = EmailMessage()
    msg.set_content(text[:160])
    msg["Subject"] = "Wetterwarnung GR20"
    msg["From"] = config["smtp"]["user"]
    msg["To"] = config["smtp"]["to"]

    context = ssl.create_default_context()
    with smtplib.SMTP(config["smtp"]["host"], config["smtp"]["port"]) as server:
        server.starttls(context=context)
        server.login(config["smtp"]["user"], os.environ["SMTP_PASS"])
        server.send_message(msg)
