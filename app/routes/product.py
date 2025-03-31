from flask import Blueprint, request, jsonify
from app.models import Product, Item
from flask_jwt_extended import jwt_required
from bson import ObjectId

product_bp = Blueprint('products', __name__)

@product_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_products():
    products = Product.get_all()
    product_list = [
        {
            "id": str(product.id),
            "name": product.name,
            "shop_id": str(product.shop.id),
            "price": product.price,
            "quantity": product.quantity,
            "threshold": product.threshold,
            "description": product.description,
            "category": product.category,
        }
        for product in products
    ]
    return jsonify(product_list), 200

@product_bp.route('/<product_id>', methods=['GET'])
@jwt_required()
def get_product_by_id(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "id": str(product.id),
        "name": product.name,
        "shop_id": str(product.shop.id),
        "price": product.price,
        "quantity": product.quantity,
        "threshold": product.threshold,
        "description": product.description,
        "category": product.category,
    }), 200

@product_bp.route('/barcode/<barcode>', methods=['GET'])
@jwt_required()
def get_product_by_barcode(barcode):
    item = Item.get_by_barcode(barcode)
    if not item:
        return jsonify({"error": "Product not found"}), 404

    product = item.product
    return jsonify({
        "id": str(product.id),
        "name": product.name,
        "shop_id": str(product.shop.id),
        "price": product.price,
        "quantity": product.quantity,
        "threshold": product.threshold,
        "description": product.description,
        "category": product.category,
        "barcode": item.barcode,
    }), 200

@product_bp.route('/add', methods=['POST'])
@jwt_required()
def add_product():
    data = request.get_json()
    name = data.get('name')
    shop_id = data.get('shop_id')
    price = data.get('price')
    quantity = data.get('quantity')
    threshold = data.get('threshold', 0)
    description = data.get('description', "")
    category = data.get('category', "")
    is_serialized = data.get('isSerialized', False)

    if not name or not shop_id or not price or not quantity:
        return jsonify({"error": "Missing required fields"}), 400

    product = Product(
        name=name,
        shop=shop_id,
        price=price,
        quantity=quantity,
        threshold=threshold,
        description=description,
        category=category,
        isSerialized=is_serialized
    )
    product.save()

    return jsonify({"message": "Product added successfully", "product_id": str(product.id)}), 201

@product_bp.route('/update/<product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    data = request.get_json()
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    product.quantity = data.get('quantity', product.quantity)
    product.threshold = data.get('threshold', product.threshold)
    product.description = data.get('description', product.description)
    product.category = data.get('category', product.category)
    product.save()

    return jsonify({"message": "Product updated successfully"}), 200

@product_bp.route('/delete/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    product.delete()
    return jsonify({"message": "Product deleted successfully"}), 200

@product_bp.route('/scan-barcode', methods=['POST'])
@jwt_required()
def scan_barcode():
    data = request.get_json()
    barcode = data.get('barcode')

    if not barcode:
        return jsonify({"error": "Missing barcode field"}), 400

    item = Item.get_by_barcode(barcode)
    if not item:
        return jsonify({"error": "Product not found"}), 404

    product = item.product
    return jsonify({
        "product_id": str(product.id),
        "name": product.name,
        "shop_id": str(product.shop.id),
        "price": product.price,
        "quantity": product.quantity,
        "threshold": product.threshold,
        "description": product.description,
        "category": product.category,
        "barcode": item.barcode,
    }), 200

@product_bp.route('/add-item', methods=['POST'])
@jwt_required()
def add_item():
    data = request.get_json()
    product_id = data.get('product_id')
    barcode = data.get('barcode')

    if not product_id:
        return jsonify({"error": "Missing product_id"}), 400

    # Validate product_id as a valid ObjectId
    if not ObjectId.is_valid(product_id):
        return jsonify({"error": "Invalid product_id"}), 400

    # Fetch the product to ensure it exists
    product = Product.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Create the item
    item = Item(
        product=product,  # Use the product object
        barcode=barcode
    )
    item.save()

    return jsonify({
        "message": "Item added successfully",
        "item_id": str(item.id),
        "barcode": item.barcode,
        "product_id": str(item.product.id),
        "product_name": item.product.name,
        "shop_id": str(item.product.shop.id),
        "shop_name": item.product.shop.name,
        "price": item.product.price,
        "quantity": item.product.quantity,
        "threshold": item.product.threshold,
        "description": item.product.description,
        "category": item.product.category
    }), 201