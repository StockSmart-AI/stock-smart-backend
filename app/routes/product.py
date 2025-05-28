from flask import Blueprint, request, jsonify
from app.models import Product, Item, Transaction, Shop, User
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from bson import ObjectId
import cloudinary
from app import utils  

product_bp = Blueprint('products', __name__)


#Get all products routes
@product_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_products():
    shop_id = request.args.get('shop_id')
    if not shop_id:
        return jsonify({"error": "shop_id is required"}), 400

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        return jsonify({"error": "Invalid page or per_page parameter"}), 400

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10
    if per_page > 100: # Optional: limit max items per page
        per_page = 100

    products_query = Product.objects(shop=ObjectId(shop_id))
    total_products = products_query.count()
    
    # Calculate skip and limit for pagination
    skip = (page - 1) * per_page
    paginated_products = products_query.skip(skip).limit(per_page)

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
            "image_url": product.image_url  # Added image_url
        }
        for product in paginated_products
    ]

    total_pages = (total_products + per_page - 1) // per_page # Ceiling division

    return jsonify({
        "products": product_list,
        "page": page,
        "per_page": per_page,
        "total_products": total_products,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }), 200



#Get product by ID route
@product_bp.route('/<product_id>', methods=['GET'])
@jwt_required()
def get_product_by_id(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product=product.get_serialized()), 200



#Get all product by barcode route
@product_bp.route('/barcode/<barcode>', methods=['GET'])
@jwt_required()
def get_product_by_barcode(barcode):
    shop_id = request.args.get('shop_id')

    matching = []
    items = Item.get_by_barcode(barcode)
    if not items:
        return jsonify({"error": "Product not found"}), 404

    for item in items:
        product = item.product
        if shop_id and str(product.shop.id) == shop_id:
            matching.append({item.barcode: item.product.get_serialized()})
        
    if not matching:
        return jsonify({"error": "Product not found"}), 404
    
    print(matching)

    return jsonify(matching), 200


# Add a product route
@product_bp.route('/add', methods=['POST'])
@jwt_required()
def add_product():
    data = request.form
    image_file = request.files.get('image')
    
    product_image_url = ""  # Default image URL

    if image_file:
        # If an image file is provided, upload it to Cloudinary
        try:
            product_image_url = utils.upload_image_to_cloudinary(image_file)
        except cloudinary.exceptions.Error as e:
            return jsonify({"error": "Image upload failed", "details": str(e)}), 500
    elif data.get('image_url'):
        # If no image file, but image_url is in form data (from script), use it
        product_image_url = data.get('image_url')
    # If neither image_file nor data.get('image_url') is present, 
    # product_image_url will remain "" (or you can set a default placeholder here)

    name = data.get('name')
    price = data.get('price')
    shop_id = data.get('shop_id')
    quantity = 0  # Default quantity for a new product
    threshold = data.get('threshold', 0)
    description = data.get('description', "")
    category = data.get('category', "")
    # Ensure boolean conversion for isSerialized
    is_serialized_str = data.get('isSerialized', 'False').lower()
    is_serialized = is_serialized_str == 'true' 

    if not name or not shop_id or not price:
        return jsonify({"error": "Missing required fields: name, shop_id, price"}), 400

    product = Product(
        name=name,
        shop=shop_id,
        price=price,
        quantity=quantity,
        threshold=threshold,
        description=description,
        category=category,
        isSerialized=is_serialized,
        image_url=product_image_url  # Use the determined image URL
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


# Restock route
@product_bp.route('/restock', methods=['POST'])
@jwt_required()
def restock():
    data = request.get_json()
    shop = data.get('shop')
    crate = data.get('crate')
    email = get_jwt_identity()

    user = User.get_by_email(email)

    total = 0
    for item in crate:
        product = Product.get_by_id(item["product_id"])
        if product.isSerialized:
            for barcode in item["barcodes"]:
                new_item = Item(barcode=barcode, product=product)
                new_item.save()
        else:
            product.quantity += item["quantity"]
        
        total += (item["price"] * item["quantity"])
            


    transaction = Transaction(shop=shop, user=user, transaction_type="restock", payload=crate, total=total)
    if not transaction:
        return jsonify({"error": "Transaction Failed"}), 400
    
    transaction.save()

    return jsonify({"message": "Item added successfully"}), 201


# Sell route
@product_bp.route('/sell', methods=['POST'])
@jwt_required()
def sell():
    data = request.get_json()
    shop = data.get('shop')
    cart = data.get('cart')
    email = get_jwt_identity()

    user = User.get_by_email(email)

    total = 0
    for item in cart:
        product = Product.get_by_id(item['product_id'])
        if product.isSerialized:
            for barcode in item['barcodes']:
                sold_item = Item.get_by_barcode(barcode)
                sold_item.delete()
        else:
            product.quantity -= item['quantity']
        
        total += (item['price'] * item['quantity'])
            


    transaction = Transaction(shop=shop, user=user, transaction_type="sale", payload=cart, total=total)
    if not transaction:
        return jsonify({"error": "Transaction Failed"}), 400
    
    transaction.save()

    return jsonify({"message": "Items sold successfully"}), 201



# Delete item by barcode
@product_bp.route('/delete/barcode', methods=['DELETE'])
@jwt_required()
def delete_item(barcode):
    item = Item.objects(barcode=barcode).first()
    if not item:
        return jsonify({"error": "Item not found"}), 404

    item.delete()

    return jsonify({"message": "Item deleted successfully"}), 200


# get all items of a product
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
        }
        for item in items
    ]

    return jsonify(item_list), 200