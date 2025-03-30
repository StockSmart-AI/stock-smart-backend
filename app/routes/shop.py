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


    shops = Shop.get_by_owner_id(owner.id)
    for shop in shops:
        if shop.name == shop_name:
            return jsonify({"error": "Name is already in use"}), 400

    new_shop = Shop(name=shop_name, address=address, owner=owner)
    new_shop.save()
    return jsonify({"message": "Shop created successfully"}), 201


@shop_bp.route("/shops", methods=["GET"])
@jwt_required()
def get_shops_by_owner():
    email = get_jwt_identity()
    owner = User.get_by_email(email)
    shops = Shop.get_by_owner_id(owner.id)

    if not shops:
        return jsonify({"error": "No shops found for this owner"}), 404
    
    shop_list = []
    for shop in shops:
        shop_list.append({
            "id": str(shop.id),
            "name": shop.name,
            "address": shop.address,
            "owner_id": str(shop.owner.id)
        })

    return jsonify(shop_list), 200