from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User
from app.utils import generate_otp_secret, generate_otp_token, send_email  # Import utility functions
import pyotp  

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('signup', methods=['POST'])
def signup():
    data = request.get_json()
    print(f"Received data: {data}")  
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')  
    role = data.get('role', 'employee')

    if not name or not email or not password or not phone:
        missing_fields = []
        if not name:
            missing_fields.append("name")
        if not email:
            missing_fields.append("email")
        if not password:
            missing_fields.append("password")
        if not phone:
            missing_fields.append("phone")
        print(f"Missing fields: {missing_fields}")  
        return jsonify({"error": "Missing required fields", "missing_fields": missing_fields}), 400

    existing_user = User.get_by_email(email)
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    new_user = User(None, name, email, password, phone, role=role) 
    new_user.save_to_db()

    return jsonify({"message": "User created successfully"}), 201

@auth_bp.route('login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    print(f"Received data: {data}")  

    if not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    user = User.get_by_email(email)
    if user and user.check_password(password):
        access_token = create_access_token(identity={"email": user.email, "role": user.role})
        return jsonify(access_token=access_token, role=user.role), 200

    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route("send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")
    
    if not email:
        return jsonify({"error": "Missing email field"}), 400

    user = User.get_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404


    otp_code = pyotp.TOTP(pyotp.random_base32()).now()
    user.set_otp(otp_code)  

    
    subject = "Your OTP Code"
    body = f"Your OTP code is {otp_code}. It expires in 5 minutes."

    if send_email(to_email=email, subject=subject, body=body):
        return jsonify({"message": "OTP sent successfully"}), 200
    else:
        return jsonify({"error": "Failed to send OTP"}), 500


@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp_code = data.get("otp")

    if not email or not otp_code:
        return jsonify({"error": "Missing email or OTP"}), 400

    user = User.get_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    is_valid, message = user.verify_otp(otp_code)
    if is_valid:
        access_token = create_access_token(identity={"email": user.email, "role": user.role})
        return jsonify({"message": "Login successful!", "role": user.role, "access_token": access_token}), 200

    return jsonify({"error": message}), 400
