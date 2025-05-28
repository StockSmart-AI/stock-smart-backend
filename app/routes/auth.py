from flask import Blueprint, request, jsonify, render_template_string
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from app.models import PasswordResetToken, User
from app.utils import generate_otp_secret, generate_otp_token,send_email, send_email, send_password_reset_email 
import pyotp  

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('signup', methods=['POST'])
def signup():
    data = request.get_json()
    print(f"Received data: {data}")  
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'employee')

    if not name or not email or not password:
        missing_fields = []
        if not name:
            missing_fields.append("name")
        if not email:
            missing_fields.append("email")
        if not password:
            missing_fields.append("password")

        print(f"Missing fields: {missing_fields}")  
        return jsonify({"error": "Missing required fields", "missing_fields": missing_fields}), 400

    existing_user = User.get_by_email(email)
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    new_user = User(name=name, email=email, password=password, role=role) 
    new_user.save()

    return jsonify(user=new_user.get_serialized()), 201


@auth_bp.route('login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    user = User.get_by_email(email)
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.email)
        refresh_token = create_refresh_token(identity=user.email)
        return jsonify(access_token=access_token, refresh_token=refresh_token, user=user.get_serialized()), 200

    return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    new_token = create_access_token(identity=identity)
    return jsonify(access_token=new_token), 200


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
        access_token = create_access_token(identity=user.email)
        refresh_token = create_refresh_token(identity=user.email)
        return jsonify(access_token=access_token, refresh_token=refresh_token, user=user.get_serialized()), 200

    return jsonify({"error": message}), 400


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.get_by_email(email)
    if not user:
        # Still return a success-like message to prevent email enumeration
        return jsonify({"message": "If an account with this email exists, a password reset link has been sent."}), 200

    reset_token_value = user.set_password_reset_token()
    # Update reset_link to point to our new Flask-served form
    # Assuming auth_bp is registered with '/auth' prefix, e.g., app.register_blueprint(auth_bp, url_prefix='/auth')
    # If no prefix, it would be '/reset-password-form/{reset_token_value}'
    # Make sure your backend URL is correct (e.g., http://127.0.0.1:5000)
    reset_link = f"http://127.0.0.1:5000/auth/reset-password-form/{reset_token_value}" 

    try:
        send_password_reset_email(user.email, reset_link)
    except Exception as e:
        # Log the error, but still return a generic message to the user
        print(f"Error sending password reset email: {e}")
        return jsonify({"message": "If an account with this email exists, a password reset link has been sent."}), 200
        
    return jsonify({"message": "If an account with this email exists, a password reset link has been sent."}), 200


@auth_bp.route('/reset-password-form/<token>', methods=['GET'])
def show_reset_password_form(token):
    # Simple HTML form. For production, use proper templates.
    html_form = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Password</title>
        <style>
            body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; margin-top: 50px; }}
            .container {{ width: 300px; padding: 20px; border: 1px solid #ccc; border-radius: 5px; }}
            label {{ display: block; margin-bottom: 5px; }}
            input[type="password"] {{ width: 95%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 3px; }}
            button {{ padding: 10px 15px; background-color: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }}
            button:hover {{ background-color: #0056b3; }}
            .message {{ margin-top: 15px; padding: 10px; border-radius: 3px; }}
            .success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .error {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Reset Your Password</h2>
            <form id="resetForm">
                <label for="password">New Password:</label>
                <input type="password" id="password" name="password" required minlength="6">
                <button type="submit">Reset Password</button>
            </form>
            <div id="messageArea" class="message" style="display:none;"></div>
        </div>
        <script>
            document.getElementById('resetForm').addEventListener('submit', async function(event) {{
                event.preventDefault();
                const password = document.getElementById('password').value;
                const messageArea = document.getElementById('messageArea');
                messageArea.style.display = 'none';
                messageArea.className = 'message'; // Reset classes

                const response = await fetch('/auth/reset-password/{token}', {{ // Make sure this path is correct
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ password: password }})
                }});

                const result = await response.json();
                messageArea.style.display = 'block';

                if (response.ok) {{
                    messageArea.textContent = result.message || 'Password reset successfully!';
                    messageArea.classList.add('success');
                    document.getElementById('resetForm').reset(); // Clear form
                }} else {{
                    messageArea.textContent = result.error || 'Failed to reset password.';
                    messageArea.classList.add('error');
                }}
            }});
        </script>
    </body>
    </html>
    """
    return render_template_string(html_form, token=token)


@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password_with_token(token):
    data = request.get_json()
    new_password = data.get('password')

    if not new_password:
        return jsonify({"error": "New password is required"}), 400
    
    if len(new_password) < 6: 
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    token_doc = PasswordResetToken.get_by_token(token)

    if not token_doc:
        return jsonify({"error": "Invalid or expired reset token"}), 400
    
    if token_doc.is_expired():
        token_doc.delete() 
        return jsonify({"error": "Invalid or expired reset token"}), 400 

    user = token_doc.user
    if not user:
        token_doc.delete() 
        return jsonify({"error": "User not found for this token"}), 404

    user.password_hash = "" 
    user_temp_for_hashing = User(password=new_password) 
    user.password_hash = user_temp_for_hashing.password_hash
    user.save()

    token_doc.delete()

    return jsonify({"message": "Password has been reset successfully."}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    response = jsonify({"message": "Successfully logged out"})
    unset_jwt_cookies(response)
    return response, 200
