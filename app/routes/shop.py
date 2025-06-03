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