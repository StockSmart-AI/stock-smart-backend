from flask import Blueprint, request, jsonify
from app.models import User, Invitation, Shop  # Ensure Invitation is imported
from flask_jwt_extended import get_jwt_identity, jwt_required
import uuid
import mongoengine as me  # Add this import to resolve the NameError

user_bp = Blueprint('users', __name__)


@user_bp.route('/user/<email>', methods=['GET'])
@jwt_required()
def get_user_by_email(email):
    user = User.get_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.get_serialized()), 200

@user_bp.route('/users/<shop_id>', methods=['GET'])
@jwt_required()
def get_user_by_shop(shop_id):
    users = User.get_employees_by_shop_id(shop_id)
    if not users:
        return jsonify({"error": "User not found"}), 404

    shop = Shop.get_by_id(shop_id)

    user_list = [shop.owner.get_serialized()] if shop and shop.owner else []
    for user in users:
        user_list.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        })

    return jsonify(user_list), 200

@user_bp.route('/user', methods=['DELETE'])
@jwt_required()
def delete_user():
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.delete()
    return jsonify({"message": "User deleted successfully"}), 200


@user_bp.route('/users/invite', methods=['POST'])
@jwt_required()
def invite_employee():
    data = request.get_json()
    shop_id = data.get("shop_id")
    employee_email = data.get("email")

    if not shop_id or not employee_email:
        return jsonify({"error": "shop_id and email are required"}), 400

    owner_email = get_jwt_identity()
    owner = User.get_by_email(owner_email)
    employee = User.get_by_email(employee_email)
    if  not employee:
        return jsonify({"error": "Employee does not exist"}), 404
    if not owner or owner.role != "owner":
        return jsonify({"error": "Only shop owners can send invitations"}), 403

    # Generate a unique token for the invitation
    invitation_token = str(uuid.uuid4())
    invitation_link = f"https://stock-smart-backend-ny1z.onrender.com/users/join?token={invitation_token}"

    # Save the invitation to the database
    new_invitation = Invitation(token=invitation_token, shop_id=shop_id, email=employee_email)
    new_invitation.save()

    # Construct the invitation email
    subject = "You're Invited to Join a Shop on StockSmart"
    body = f"""
    Hi,

    You have been invited by {owner.name} to join their shop on StockSmart.
    Please use the following link to register and join the shop:

    {invitation_link}

    Shop ID: {shop_id}

    Best regards,
    StockSmart Team
    """

    # Send the email
    from app.utils import send_email
    if send_email(employee_email, subject, body):
        return jsonify({"message": "Invitation email sent successfully"}), 200
    else:
        return jsonify({"error": "Failed to send invitation email"}), 500


@user_bp.route('/users/join', methods=['GET'])
def join_shop():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Invalid or missing token"}), 400

    # Validate the token
    invitation = Invitation.get_by_token(token)
    if not invitation:
        return jsonify({"error": "Invalid or expired invitation"}), 404

    user = User.get_by_email(invitation.email)
    if user and user.role != "employee":
        user.shop_id = invitation.shop_id
        user.save()

    # Delete the invitation after use
    invitation.delete()

    return jsonify({"message": "User successfully joined the shop"}), 201