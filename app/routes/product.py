from flask import Blueprint, request, jsonify
from app.models import Product, Item
from flask_jwt_extended import jwt_required
from bson import ObjectId
import cloudinary
from app import utils  

product_bp = Blueprint('products', __name__)


#Get all products routes
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



#Get product by ID route
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



#Get all product by barcode route
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


# Add a product route
@product_bp.route('/add', methods=['POST'])
@jwt_required()
def add_product():
    data = request.form
    image_file = request.files.get('image')
    if not image_file:
        return jsonify({"error": "Image file is required"}), 400

    
    try:
        image_url = utils.upload_image_to_cloudinary(image_file)
    except cloudinary.exceptions.Error as e:
        return jsonify({"error": "Image upload failed", "details": str(e)}), 500
  
    name = data.get('name')
    price = data.get('price')
    shop_id = data.get('shop_id')
    quantity = 0
    threshold = data.get('threshold', 0)
    description = data.get('description', "")
    category = data.get('category', "")
    is_serialized = data.get('isSerialized', False)
    image_url = image_url if image_url else ""

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
        isSerialized=is_serialized,
        image_url=image_url
    )
    product.save()

    return jsonify({"message": "Product added successfully", "product_id": str(product.id)}), 201



#Update product route
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



#Delete product route
@product_bp.route('/delete/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    product.delete()
    return jsonify({"message": "Product deleted successfully"}), 200



#Get by barcode
@product_bp.route('/barcode/<barcode>', methods=['GET'])
@jwt_required()
def scan_barcode(barcode):

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



#Add Item route
@product_bp.route('/restock', methods=['POST'])
@jwt_required()
def restock():
    data = request.get_json()
    products = []
    items = []

    for product_id, payload in data:
        product = Product.get_product_by_id(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        if product.isSerialized:
            for i in range(payload.quantity):
                item = Item(product=product, barcode=payload.barcode[i])
                item.save()
        else:
            product.quantity += payload.quantity
            product.save()


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


@product_bp.route('/delete-item/<item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    item = Item.objects(id=item_id).first()
    if not item:
        return jsonify({"error": "Item not found"}), 404

    item.delete()

    return jsonify({"message": "Item deleted successfully"}), 200
@product_bp.route('/get-items/<product_id>', methods=['GET'])
@jwt_required()
def get_items_by_product_id(product_id):
    items = Item.objects(product=product_id)
    if not items:
        return jsonify({"error": "No items found for this product"}), 404

    item_list = [
        {
            "id": str(item.id),
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
        }
        for item in items
    ]

    return jsonify(item_list), 200