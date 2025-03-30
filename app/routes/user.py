from flask import Blueprint, request, jsonify
from app.models import User
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

user_bp = Blueprint('users', __name__)


@user_bp.route('/users/<shop_id>', methods=['GET'])
@jwt_required()
def get_user_by_shop(shop_id):
    users = User.get_by_shop_id(shop_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_list = []
    for user in user:
        user_list.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
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