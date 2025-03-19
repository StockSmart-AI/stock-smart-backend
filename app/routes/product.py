from flask import Blueprint, request, jsonify
from app.models import Product
from bson import ObjectId
from app.db import db
product_bp = Blueprint('products', __name__)



@product_bp.route('/', methods=['GET'])
def get_all_products():
    products = list(db.products.find())
    product_list = []
    
    for product in products:
        product_list.append({
            "id": str(product["_id"]),
            "name": product["name"],
            "shop_id": product["shop_id"],
            "price": product["price"],
            "quantity": product["quantity"],
            "threshold": product.get("threshold", 0),
            "description": product.get("description", ""),
            "category": product.get("category", ""),
            "barcode": product.get("barcode", "")
        })

    return jsonify(product_list), 200



@product_bp.route('/<product_id>', methods=['GET'])
def get_product_by_id(product_id):
    if not ObjectId.is_valid(product_id):
        return jsonify({"error": "Invalid product ID"}), 400

    product = db.products.find_one({"_id": ObjectId(product_id)})
    
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "id": str(product["_id"]),
        "name": product["name"],
        "shop_id": product["shop_id"],
        "price": product["price"],
        "quantity": product["quantity"],
        "threshold": product.get("threshold", 0),
        "description": product.get("description", ""),
        "category": product.get("category", ""),
        "barcode": product.get("barcode", "")
    }), 200


# Get a product by barcode
@product_bp.route('/barcode/<barcode>', methods=['GET'])
def get_product_by_barcode(barcode):
    product = db.products.find_one({"barcode": barcode})

    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "id": str(product["_id"]),
        "name": product["name"],
        "shop_id": product["shop_id"],
        "price": product["price"],
        "quantity": product["quantity"],
        "threshold": product.get("threshold", 0),
        "description": product.get("description", ""),
        "category": product.get("category", ""),
        "barcode": product.get("barcode", "")
    }), 200


@product_bp.route('/add', methods=['POST'])
def add_product():
    data = request.get_json()
    name = data.get('name')
    shop_id = data.get('shop_id')
    price = data.get('price')
    quantity = data.get('quantity')
    threshold = data.get('threshold')
    description = data.get('description', "")
    category = data.get('category', "")
    barcode = data.get('barcode')

    if not name or not shop_id or not price or not quantity or not threshold:
        return jsonify({"error": "Missing required fields"}), 400

    new_product = Product(name, shop_id, price, quantity, threshold, description, category, barcode)
    new_product.save_to_db()

    return jsonify({"message": "Product added successfully", "product_id": new_product.id}), 201

@product_bp.route('/update/<product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    product.name = data.get('name', product.name)
    product.shop_id = data.get('shop_id', product.shop_id)
    product.price = data.get('price', product.price)
    product.quantity = data.get('quantity', product.quantity)
    product.threshold = data.get('threshold', product.threshold)
    product.description = data.get('description', product.description)
    product.category = data.get('category', product.category)
    product.barcode = data.get('barcode', product.barcode)

    product.save_to_db()

    return jsonify({"message": "Product updated successfully"})

@product_bp.route('/delete/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    product.delete_from_db()

    return jsonify({"message": "Product deleted successfully"})

@product_bp.route('/scan-barcode', methods=['POST'])
def scan_barcode():
    data = request.get_json()
    barcode = data.get('barcode')

    if not barcode:
        return jsonify({"error": "Missing barcode field"}), 400

    product = Product.get_by_barcode(barcode)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "product_id": product.id,
        "name": product.name,
        "shop_id": product.shop_id,
        "price": product.price,
        "quantity": product.quantity,
        "threshold": product.threshold,
        "description": product.description,
        "category": product.category,
        "barcode": product.barcode
    })

