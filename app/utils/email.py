import smtplib
from email.mime.text import MIMEText

EMAIL = "sajan.borle@atishay.com"
PASSWORD = "ndmn yvsk lgcb aixr"

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to, msg.as_string())