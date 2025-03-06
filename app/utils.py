import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_otp_secret():
    # Generates a new TOTP secret key
    return pyotp.random_base32()

def generate_otp_token(secret, interval=200):
    # Generates a TOTP token based on the given secret and interval
    totp = pyotp.TOTP(secret, interval=interval)
    return totp.now()

def send_email(to_email, subject, body):
    """Sends an email with the provided subject and body."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_email = "chapaeresso1@gmail.com"  
    from_password = "mwbx uspp wbvu rqbi"  # Replace with your app-specific password

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False