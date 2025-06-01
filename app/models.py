from werkzeug.security import generate_password_hash, check_password_hash
import mongoengine as me
from datetime import datetime
import time
import pyotp

"""
Base Model
"""
class BaseModel(me.Document):
    meta = {'abstract': True}

    def get_serialized(self):
        data = self.to_mongo().to_dict()
        data["id"] = str(data.pop("_id"))
        return data

    @classmethod
    def get_by_id(cls, id):
        return cls.objects(id=id).first()
    
    @classmethod
    def get_all(cls):
        return cls.objects.all()


"""
User Model
"""
class User(BaseModel):
    name = me.StringField(required=True)
    email = me.EmailField(required=True, unique=True)
    password_hash = me.StringField(required=True)
    otp = me.StringField()
    otp_expiry = me.FloatField()
    role = me.StringField()
    shop = me.ReferenceField('Shop') 
    shops = me.ListField(me.ReferenceField('Shop')) 
    isVerified = me.BooleanField(required=True, default=False)
    canRestock = me.BooleanField(default=False)
    fcm_token = me.StringField(null=True, blank=True) 
    
    meta = {'collection': 'users'}

    def __init__(self, *args, password=None, **kwargs):
        if password:
            kwargs['password_hash'] = generate_password_hash(password, method="scrypt")

        super().__init__(*args, **kwargs)


    def get_serialized(self):
        data = self.to_mongo().to_dict()
        data["id"] = str(data.pop("_id"))
        data.pop('password_hash')
        data.pop('otp', None)
        data.pop('otp_expiry', None)
        if data['role'] == "owner":
            try:
                data['shops'] = [str(shop.id) for shop in self.shops]
                data.pop('shop')
            except KeyError:
                pass
        else:
            try:
                data['shop'] = str(self.shop.id) if self.shop else None
                data.pop('shops')
            except KeyError:
                pass
            
        return data
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_email(email):
        return User.objects(email=email).first()


    def set_otp(self, otp_code, expiry_seconds=300):
        """Store OTP and expiration in DB (5 min default)"""
        self.otp = otp_code
        self.otp_expiry = time.time() + expiry_seconds
        self.save()

    def verify_otp(self, otp_code):
        """Check if OTP is valid and not expired"""
        if self.otp and self.otp_expiry:
            if time.time() > self.otp_expiry:
                # Clear expired OTP
                self.otp = None
                self.otp_expiry = None
                self.save()
                return False, "OTP expired"
            if self.otp == otp_code:
                self.isVerified = True
                # Clear OTP after successful verification
                self.otp = None
                self.otp_expiry = None
                self.save()
                return True, "OTP verified"
        return False, "Invalid OTP"
    
    def set_password_reset_token(self):
        """Generate and store a password reset token"""
        # Invalidate any existing tokens for this user
        PasswordResetToken.objects(user=self).delete()
        
        token = pyotp.random_base32() # Using pyotp for a random string, could be uuid
        expiry_time = time.time() + 3600  # Token expires in 1 hour
        reset_token_doc = PasswordResetToken(user=self, token=token, expiry=expiry_time)
        reset_token_doc.save()
        return token

    @classmethod
    def get_employees_by_shop_id(cls, shop_id):
        return cls.objects(shop=shop_id)
    


"""
Shop Model
"""
class Shop(BaseModel):
    name = me.StringField(required=True)
    address = me.StringField(required=True)
    owner = me.ReferenceField('User', required=True, reverse_delete_rule=me.CASCADE)
    inventory_value = me.FloatField(default=0)

    meta = {'collection': 'shops'}

    def get_serialized(self):
        data = super().get_serialized()
        if 'owner' in data and data['owner'] is not None:
            data['owner'] = str(self.owner.id)
        return data
    
    @classmethod
    def get_by_owner_id(cls, owner_id):
        return cls.objects(owner=owner_id)
    

"""
Product Model
"""
class Product(BaseModel):
    name = me.StringField(required=True)
    shop = me.ReferenceField(Shop, required=True)
    price = me.FloatField(required=True)
    quantity = me.IntField(required=True, default=0)
    threshold = me.IntField(default=0)
    isSerialized = me.BooleanField(required=True)
    description = me.StringField(defaults="")
    category = me.StringField(defaults="")
    image_url = me.StringField(default="")

    meta = {'collection': 'products'}

    def get_serialized(self):
        data = self.to_mongo().to_dict()
        data["id"] = str(data.pop("_id"))
        data["shop_id"] = str(data.pop("shop"))
        return data


    @classmethod
    def get_product_by_id(cls, id):
        return cls.objects(id=id).first()


"""
Item Model
"""
class Item(BaseModel):
    product = me.ReferenceField(Product, required=True, reverse_delete_rule=me.CASCADE)
    barcode = me.StringField(unique=True)
    meta = {'collection': 'items'}

    def save(self, *args, **kwargs):
        if self.product:
            Product.objects(id=self.product.id).update_one(inc__quantity=1)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.product:
            Product.objects(id=self.product.id).update_one(dec__quantity=1) 

        super().delete(*args, **kwargs)

    @classmethod
    def get_by_barcode(cls, barcode):
        return cls.objects(barcode=barcode)



"""
Payload embeded document definition
"""
class SaleItemPayload(me.EmbeddedDocument):
    product_id = me.StringField(required=True)
    name = me.StringField(required=True)
    category = me.StringField(required=True)
    quantity = me.IntField(required=True)
    price = me.FloatField(required=True)
    isSerialized = me.BooleanField(default=False)
    barcodes = me.ListField(me.StringField())


"""
RestockItemPayload
"""
class RestockItemPayload(me.EmbeddedDocument):
    product_id = me.StringField(required=True)
    cost_price = me.FloatField(required=True) 
    isSerialized = me.BooleanField(required=True)
    quantity = me.IntField()
    barcodes = me.ListField(me.StringField()) 

    def clean(self):
        if self.isSerialized:
            if not self.barcodes:
                raise me.ValidationError("Barcodes are required for serialized restock items.")
            # Automatically set quantity for serialized items based on barcodes length
            self.quantity = len(self.barcodes)
        else: # Not serialized
            if self.quantity is None or self.quantity <= 0:
                raise me.ValidationError("A positive quantity is required for non-serialized restock items.")
            if self.barcodes:
                raise me.ValidationError("Barcodes should not be provided for non-serialized restock items.")


"""
Transaction Model
"""
class Transaction(BaseModel):
    date = me.DateTimeField(default=datetime.utcnow)
    shop = me.ReferenceField(Shop, required=True)
    user = me.ReferenceField(User, required=True)
    transaction_type = me.StringField(choices=["sale", "restock"], required=True)
    payload = me.ListField(me.GenericEmbeddedDocumentField(), required=True)
    total = me.FloatField(required=True)

    def clean(self):
        """Validates payload based on transaction_type."""
        if not self.payload:
            raise me.ValidationError("Payload cannot be empty.")

        if self.transaction_type == "sale":
            for item in self.payload:
                if not isinstance(item, SaleItemPayload):
                    raise me.ValidationError(
                        "Invalid item type in payload for 'sale' transaction. Expected SaleItemPayload."
                    )
        elif self.transaction_type == "restock":
            if len(self.payload) != 1:
                raise me.ValidationError("Restock transaction payload must contain exactly one item.")
            item = self.payload[0]
            if not isinstance(item, RestockItemPayload):
                raise me.ValidationError(
                    "Invalid item type in payload for 'restock' transaction. Expected RestockItemPayload."
                )

    def save(self, *args, **kwargs):
        self.clean()

        current_total = 0.0
        if self.payload:
            if self.transaction_type == "sale":
                for item in self.payload:
                    if isinstance(item, SaleItemPayload):
                        current_total += item.price * item.quantity
                    # else: already handled by clean()
            elif self.transaction_type == "restock":
                # Restock payload is expected to have one item after clean()
                item = self.payload[0]
                if isinstance(item, RestockItemPayload):
                    qty_to_consider = item.quantity # quantity is now correctly set in RestockItemPayload.clean()
                    current_total += item.cost_price * qty_to_consider
                # else: already handled by clean()
        
        self.total = current_total
        super().save(*args, **kwargs)

    meta = {'collection': 'transactions'}


class Invitation(BaseModel):
    token = me.StringField(required=True, unique=True)
    shop_id = me.ReferenceField('Shop', required=True, reverse_delete_rule=me.CASCADE)
    canRestock = me.BooleanField(default=False)
    email = me.EmailField(required=True)

    meta = {'collection': 'invitations'}

    @staticmethod
    def get_by_token(token):
        return Invitation.objects(token=token).first()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def generate_invitation_link(self):
        """Generate the invitation link using the backend URL."""
        return f"https://stock-smart-backend-ny1z.onrender.com/users/join?token={self.token}"


"""
Password Reset Token Model
"""
class PasswordResetToken(me.Document):
    user = me.ReferenceField('User', required=True, reverse_delete_rule=me.CASCADE)
    token = me.StringField(required=True, unique=True)
    expiry = me.FloatField(required=True) # Store as timestamp

    meta = {'collection': 'password_reset_tokens'}

    @classmethod
    def get_by_token(cls, token):
        return cls.objects(token=token).first()

    def is_expired(self):
        return time.time() > self.expiry
