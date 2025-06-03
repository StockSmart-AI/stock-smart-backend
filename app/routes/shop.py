from flask import Blueprint, request, jsonify
from app.models import Shop
from app.models import User
from bson import ObjectId
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

shop_bp = Blueprint('shops', __name__)

@shop_bp.route('/shop', methods=['POST'])
@jwt_required()
def create_shop():
    data = request.get_json()
    print(f"recieved data: {data}")
    shop_name = data.get('name')
    address = data.get('address')
    email = get_jwt_identity()
    owner = User.get_by_email(email)

    if not owner:
        return jsonify({"error": "Owner not found"}), 404
    
    if owner.shops:
        for shop_ref in owner.shops:
            shop = Shop.get_by_id(id=shop_ref.id)
            if shop and shop.name == shop_name:
                return jsonify({"error": "Name is already in use"}), 400
            
    

    new_shop = Shop(name=shop_name, address=address, owner=owner)
    new_shop.save()
    owner.shops.append(new_shop)
    owner.save()
    return jsonify(shop=new_shop.get_serialized()), 201


@shop_bp.route("/shops", methods=["GET"])
@jwt_required()
def get_shops_by_user():
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role == "owner":
        shops = Shop.get_by_owner_id(user.id)
        if not shops:
            return jsonify({"error": "No shops found for this owner"}), 404
        
        shop_list = []
        for shop in shops:
            shop_list.append(shop.get_serialized())
        return jsonify(shop_list), 200
    
    elif user.role == "employee":
        if not user.shop:
            return jsonify({"error": "No shop associated with this employee"}), 404
        return jsonify([user.shop.get_serialized()]), 200
    
    return jsonify({"error": "Invalid user role"}), 400

@shop_bp.route("/shop/<shop_id>", methods=["GET"])
@jwt_required()
def get_shop_by_id(shop_id):
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    shop = Shop.get_by_id(shop_id)
    if not shop:
        return jsonify({"error": "Shop not found"}), 404
    
    # Check if user has access to this shop
    if user.role == "owner":
        if str(shop.owner.id) != str(user.id):
            return jsonify({"error": "Unauthorized access to shop"}), 403
    elif user.role == "employee":
        if not user.shop or str(user.shop.id) != str(shop.id):
            return jsonify({"error": "Unauthorized access to shop"}), 403
    
    return jsonify(shop.get_serialized()), 200

@shop_bp.route("/shop/<shop_id>", methods=["PUT"])
@jwt_required()
def update_shop(shop_id):
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if user.role != "owner":
        return jsonify({"error": "Only shop owners can update shop details"}), 403
    
    shop = Shop.get_by_id(shop_id)
    if not shop:
        return jsonify({"error": "Shop not found"}), 404
    
    if str(shop.owner.id) != str(user.id):
        return jsonify({"error": "Unauthorized to update this shop"}), 403
    
    data = request.get_json()
    name = data.get('name')
    address = data.get('address')
    
    if not name or not address:
        return jsonify({"error": "Name and address are required"}), 400
    
    # Check if new name conflicts with existing shop names
    if name != shop.name:
        for existing_shop in user.shops:
            if existing_shop.name == name and str(existing_shop.id) != str(shop.id):
                return jsonify({"error": "Name is already in use"}), 400
    
    shop.name = name
    shop.address = address
    shop.save()
    
    return jsonify(shop.get_serialized()), 200

@shop_bp.route("/shop/<shop_id>", methods=["DELETE"])
@jwt_required()
def delete_shop(shop_id):
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if user.role != "owner":
        return jsonify({"error": "Only shop owners can delete shops"}), 403
    
    shop = Shop.get_by_id(shop_id)
    if not shop:
        return jsonify({"error": "Shop not found"}), 404
    
    if str(shop.owner.id) != str(user.id):
        return jsonify({"error": "Unauthorized to delete this shop"}), 403
    
    # Remove shop from owner's shops list
    user.shops = [s for s in user.shops if str(s.id) != str(shop.id)]
    user.save()
    
    # Delete the shop
    shop.delete()
    
    return jsonify({"message": "Shop deleted successfully"}), 200