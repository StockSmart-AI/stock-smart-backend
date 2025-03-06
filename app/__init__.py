from flask import Flask
from dotenv import load_dotenv 
from flask_login import LoginManager
from app.routes.auth import auth_bp
from app.db import db  
import os

load_dotenv()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Load SECRET_KEY
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")



    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is missing. Check your .env file!")

    try:
        print("Database connected successfully")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

    login_manager.init_app(app)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    return app
