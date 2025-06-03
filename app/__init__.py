from flask import Flask
from dotenv import load_dotenv 
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.shop import shop_bp
from app.routes.product import product_bp
from app.routes.upload import upload_bp
from app.routes.analytics import analytics_bp
from app.routes.notification import notification_bp
from app.db import me
import os
from flask_jwt_extended import JWTManager
from datetime import timedelta
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

load_dotenv()



def create_app():
    app = Flask(__name__)

     # Configuration       
    cloudinary.config( 
        cloud_name = "dmbuhyrta", 
        api_key = os.getenv("cloudinary_api_key"), 
        api_secret = os.getenv("cloudinary_secret_key"),
        secure=True
    )

    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["SECRET_KEY"] = os.getenv("secret_key")
    app.config["JWT_SECRET_KEY"] = os.getenv("secret_key") 
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    jwt = JWTManager(app)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is missing. Check your .env file!")

    try:
        print("Database connected successfully")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp)
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(shop_bp, url_prefix='/shops')
    app.register_blueprint(product_bp, url_prefix='/products')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(notification_bp, url_prefix='/api')
    return app
