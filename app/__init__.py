from flask import Flask
from dotenv import load_dotenv 
from app.routes.auth import auth_bp
from app.routes.product import product_bp
from app.db import db  
import os
from flask_jwt_extended import JWTManager
from datetime import timedelta

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["SECRET_KEY"] = os.getenv("secret_key")
    app.config["JWT_SECRET_KEY"] = os.getenv("secret_key")  # Ensure JWT_SECRET_KEY is set correctly
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

    jwt = JWTManager(app)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is missing. Check your .env file!")

    try:
        print("Database connected successfully")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(product_bp, url_prefix='/products')
    return app
