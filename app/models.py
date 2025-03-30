from werkzeug.security import generate_password_hash, check_password_hash
import mongoengine as me
import time

"""
Base Model
"""
class BaseModel(me.Document):
    meta = {'abstract': True}

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
    phone = me.StringField(unique=True)
    password_hash = me.StringField(required=True)
    otp = me.StringField()
    otp_expiry = me.FloatField()
    role = me.StringField()
    shop = me.ReferenceField('Shop')
    
    meta = {'collection': 'users'}

    def __init__(self, *args, password=None, **kwargs):
        if password:
            kwargs['password_hash'] = generate_password_hash(password, method="scrypt")

        super().__init__(*args, **kwargs)


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
                return False, "OTP expired"
            if self.otp == otp_code:
                return True, "OTP verified"
        return False, "Invalid OTP"
    
    @classmethod
    def get_by_shop_id(cls, shop_id):
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

    meta = {'collection': 'products'}