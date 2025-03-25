from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from app.db import db
import time



class User(UserMixin):
    def __init__(self, id=None, name=None, email=None, password=None, phone=None, password_hash=None, otp=None, otp_expiry=None, role="owner"):
        self.id = str(id) if id else None 
        self.name = name
        self.email = email
        self.phone = phone
        self.otp = otp  
        self.otp_expiry = otp_expiry  
        self.role = role  

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
                id=str(user_data["_id"]),  
                name=user_data["name"],
                email=user_data["email"],
                phone=user_data["phone"],
                password_hash=user_data["password_hash"],
                otp=user_data.get("otp"),
                otp_expiry=user_data.get("otp_expiry"),
                role=user_data.get("role", "employee"),  
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
            "role": self.role,  
        }

        if self.id and ObjectId.is_valid(self.id):  
            db.users.update_one({"_id": ObjectId(self.id)}, {"$set": user_data}, upsert=True)
        else:  
            result = db.users.insert_one(user_data)
            self.id = str(result.inserted_id)  

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




class Product:
    def __init__(self, name, shop_id, price, quantity, threshold, description="", category="", barcode=None, identifier=None, id=None):
        self.id = str(id) if id else None  
        self.name = name
        self.shop_id = shop_id
        self.price = float(price)
        self.quantity = float(quantity)
        self.threshold = int(threshold)
        self.description = description
        self.category = category
        self.barcode = barcode  # New barcode field
        self.identifier = identifier if identifier else {}

    @staticmethod
    def get_by_barcode(barcode):
        product_data = db.products.find_one({"barcode": barcode})
        if product_data:
            return Product(
                id=str(product_data["_id"]),
                name=product_data["name"],
                shop_id=product_data["shop_id"],
                price=product_data["price"],
                quantity=product_data["quantity"],
                threshold=product_data["threshold"],
                description=product_data.get("description", ""),
                category=product_data.get("category", ""),
                barcode=product_data.get("barcode")
            )
        return None
  

    def save_to_db(self):
        product_data = {
            "name": self.name,
            "shop_id": self.shop_id,
            "price": self.price,
            "quantity": self.quantity,
            "threshold": self.threshold,
            "description": self.description,
            "category": self.category,
            "identifier": self.identifier,
            "barcode": self.barcode  # Ensure barcode is saved
        }

        if self.id and ObjectId.is_valid(self.id):  
            db.products.update_one({"_id": ObjectId(self.id)}, {"$set": product_data}, upsert=True)
        else:  
            result = db.products.insert_one(product_data)
            self.id = str(result.inserted_id)  

    @staticmethod
    def get_by_id(product_id):
        product_data = db.products.find_one({"_id": ObjectId(product_id)})
        if product_data:
            return Product(
                id=str(product_data["_id"]),
                name=product_data["name"],
                shop_id=product_data["shop_id"],
                price=product_data["price"],
                quantity=product_data["quantity"],
                threshold=product_data["threshold"],
                description=product_data.get("description", ""),
                category=product_data.get("category", ""),
                identifier=product_data.get("identifier", {}),
                barcode=product_data.get("barcode")  
            )
        return None

    def delete_from_db(self):
        if self.id and ObjectId.is_valid(self.id):
            db.products.delete_one({"_id": ObjectId(self.id)})

    def update_stock(self, amount):
        """Update the quantity of the product in stock"""
        new_quantity = self.quantity + amount
        db.products.update_one({"_id": ObjectId(self.id)}, {"$set": {"quantity": new_quantity}})
        self.quantity = new_quantity  

    def apply_discount(self, percentage):
        """Apply a discount to the product's price"""
        new_price = self.price - (self.price * (percentage / 100))
        db.products.update_one({"_id": ObjectId(self.id)}, {"$set": {"price": new_price}})
        self.price = new_price  


class Restock:
    def __init__(self, shop_id, product_id, user_id, quantity, id=None):
        self.id = str(id) if id else None  
        self.shop_id = shop_id
        self.product_id = ObjectId(product_id)
        self.user_id = user_id
        self.quantity = float(quantity)

    def save_to_db(self):
        restock_data = {
            "shop_id": self.shop_id,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "quantity": self.quantity
        }

        if self.id and ObjectId.is_valid(self.id):  
            db.restocks.update_one({"_id": ObjectId(self.id)}, {"$set": restock_data}, upsert=True)
        else:  
            result = db.restocks.insert_one(restock_data)
            self.id = str(result.inserted_id)  

    @staticmethod
    def get_by_product_id(product_id):
        """Retrieve all restocks related to a specific product"""
        restocks = db.restocks.find({"product_id": ObjectId(product_id)})
        return [Restock(
            id=str(r["_id"]),
            shop_id=r["shop_id"],
            product_id=str(r["product_id"]),
            user_id=r["user_id"],
            quantity=r["quantity"]
        ) for r in restocks]
