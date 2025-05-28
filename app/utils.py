import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import cloudinary.uploader

def upload_image_to_cloudinary(image_file):
    result = cloudinary.uploader.upload(image_file)
    return result["secure_url"]  # or result["url"] if you want non-secure

def generate_otp_secret():
    
    return pyotp.random_base32()

def generate_otp_token(secret, interval=200):
    
    totp = pyotp.TOTP(secret, interval=interval)
    return totp.now()

def send_email(to_email, subject, body):
    """Sends an email with the provided subject and body."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_email = "stocksmartteam@gmail.com"  
    from_password = "vivc swji pyyi fkpe" 

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


def send_password_reset_email(recipient_email, reset_link):
    subject = "Password Reset Request for StockSmart"
    body = f"Please click the following link to reset your password:\n{reset_link}\n\nIf you did not request this, please ignore this email.\nThis link will expire in 1 hour."
    
    if send_email(recipient_email, subject, body):
        print(f"Password reset email sent to {recipient_email}")
    else:
        print(f"Failed to send password reset email to {recipient_email}")
