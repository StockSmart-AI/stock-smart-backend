from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from app.db import db
import time

class User(UserMixin):
    def __init__(self, id=None, name=None, email=None, password=None, phone=None, password_hash=None, otp=None, otp_expiry=None):
        self.id = str(id) if id else None  # Ensure self.id is None for new users
        self.name = name
        self.email = email
        self.phone = phone
        self.otp = otp  
        self.otp_expiry = otp_expiry  

        if password:
            self.password_hash = generate_password_hash(str(password), method="scrypt")
        else:
            self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_email(email):
        user_data = db.users.find_one({"email": email})
        if user_data:
            return User(
                id=str(user_data["_id"]),  # Ensure ObjectId is stored as a string
                name=user_data["name"],
                email=user_data["email"],
                phone=user_data["phone"],
                password_hash=user_data["password_hash"],
                otp=user_data.get("otp"),
                otp_expiry=user_data.get("otp_expiry"),
            )
        return None

    def save_to_db(self):
        user_data = {
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "phone": self.phone,
            "otp": self.otp,
            "otp_expiry": self.otp_expiry,
        }

        if self.id and ObjectId.is_valid(self.id):  # Check if self.id is a valid ObjectId
            db.users.update_one({"_id": ObjectId(self.id)}, {"$set": user_data}, upsert=True)
        else:  # If new user, insert into DB and set the generated ID
            result = db.users.insert_one(user_data)
            self.id = str(result.inserted_id)  # Convert ObjectId to string

    def set_otp(self, otp_code, expiry_seconds=300):
        """Store OTP and expiration in DB (5 min default)"""
        self.otp = otp_code
        self.otp_expiry = time.time() + expiry_seconds
        self.save_to_db()

    def verify_otp(self, otp_code):
        """Check if OTP is valid and not expired"""
        if self.otp and self.otp_expiry:
            if time.time() > self.otp_expiry:
                return False, "OTP expired"
            if self.otp == otp_code:
                return True, "OTP verified"
        return False, "Invalid OTP"
