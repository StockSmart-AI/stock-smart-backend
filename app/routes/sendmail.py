from utils import generate_totp_secret, generate_totp_token, send_email

#On a view that you want to trigger message. You can do this:
otp_secret = generate_otp_secret()
otp_token = generate_otp_token(otp_secret)
send_email(
             to_email="add the email to be sent the message",
             subject="add a subject",
             body="here you can ensure to add {otp_token} so that you send the token"
            )