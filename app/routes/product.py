from flask import Blueprint, request, jsonify
from app.models import Product, Item, Transaction, Shop, User, RestockItemPayload, SaleItemPayload
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
    shop_id = data.get('shop_id')
    product_id = data.get('product_id')
    cost_price = data.get('cost_price')
    barcodes = data.get('barcodes', [])
    quantity = data.get('quantity')
    email = get_jwt_identity()

    user = User.get_by_email(email)

    if not all([shop_id, product_id, cost_price]):
        return jsonify({"error": "Missing required fields: shop_id, product_id, cost_price"}), 400
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    shop = Shop.get_by_id(shop_id)
    if not shop:
        return jsonify({"error": "Shop not found"}), 404

    product = Product.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    restock_payload_item = RestockItemPayload(
        product_id=str(product.id),
        cost_price=cost_price,
        isSerialized=product.isSerialized
    )

    if product.isSerialized:
        for barcode in barcodes:
            new_item = Item(barcode=barcode, product=product)
            new_item.save() 
        restock_payload_item.barcodes = barcodes
    else:
        quantity = int(quantity)
        product.quantity += quantity
        product.save()
        restock_payload_item.quantity = quantity

    transaction = Transaction(
        shop=shop, 
        user=user, 
        transaction_type="restock", 
        payload=[restock_payload_item]
    )

    try:
        transaction.save()
    except Exception as e:
        print(f"Transaction save error: {e}")
        if product.isSerialized:
            Item.objects(product=product, barcode__in=barcodes).delete()
        else:
            product.quantity -= quantity
            product.save()
        return jsonify({"error": f"Transaction Failed: {str(e)}"}), 400

    return jsonify({"message": "Product restocked successfully", "transaction_id": str(transaction.id)}), 201


# Sell route
@product_bp.route('/sell', methods=['POST'])
@jwt_required()
def sell():
    data = request.get_json()
    shop_id = data.get('shop_id')
    cart = data.get('cart') # Expected to be a list of sale items
    email = get_jwt_identity()

    if not shop_id or not cart:
        return jsonify({"error": "Missing required fields: shop_id, cart"}), 400
    
    if not isinstance(cart, list) or not cart:
        return jsonify({"error": "Cart must be a non-empty list"}), 400

    user = User.get_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    shop = Shop.get_by_id(shop_id)
    if not shop:
        return jsonify({"error": "Shop not found"}), 404
    
    sale_payload_items = []
    committed_stock_changes_for_rollback = []

    try:
        for cart_item in cart:
            product_id = cart_item.get('product_id')
            quantity_sold = cart_item.get('quantity')
            price_at_sale = cart_item.get('price') # Price per unit at time of sale
            barcodes_from_cart = cart_item.get('barcodes', [])

            if not all([product_id, quantity_sold, price_at_sale]):
                raise ValueError("Each cart item must have product_id, quantity, and price.")
            
            try:
                quantity_sold = int(quantity_sold)
                price_at_sale = float(price_at_sale)
                if quantity_sold <= 0 or price_at_sale < 0: # Price can be 0 for giveaways, but not negative
                    raise ValueError("Quantity must be positive and price non-negative.")
            except ValueError as e:
                raise ValueError(f"Invalid quantity or price for product_id {product_id}: {e}")


            product = Product.get_by_id(product_id)
            if not product:
                raise ValueError(f"Product with ID {product_id} not found.")
            if product.shop.id != shop.id:
                raise ValueError(f"Product {product.name} does not belong to shop {shop.name}.")

            current_item_barcodes_sold = []
            if product.isSerialized:
                if not barcodes_from_cart or len(barcodes_from_cart) != quantity_sold:
                    raise ValueError(f"Barcode information mismatch for serialized product {product.name}. Expected {quantity_sold} barcodes.")
                
                current_item_barcodes_sold = barcodes_from_cart
                for barcode in barcodes_from_cart:
                    item_to_sell = Item.objects(barcode=barcode, product=product).first()
                    if not item_to_sell:
                        raise ValueError(f"Item with barcode {barcode} not found, does not belong to product {product.name}, or already sold.")
                    
                    item_to_sell.delete() # This also decrements product.quantity via Item.delete()
                    committed_stock_changes_for_rollback.append({
                        'type': 'serialized_item_deleted',
                        'barcode': barcode,
                        'product_id': str(product.id)
                    })
            else: # Not serialized
                if product.quantity < quantity_sold:
                    raise ValueError(f"Insufficient stock for {product.name}. Available: {product.quantity}, Requested: {quantity_sold}.")
                
                Product.objects(id=product.id).update_one(dec__quantity=quantity_sold)
                committed_stock_changes_for_rollback.append({
                    'type': 'nonserialized_product_decremented',
                    'product_id': str(product.id),
                    'quantity': quantity_sold
                })
            
            sale_item_payload = SaleItemPayload(
                product_id=str(product.id),
                name=product.name,
                category=product.category,
                quantity=quantity_sold,
                price=price_at_sale, # Selling price per unit
                isSerialized=product.isSerialized,
                barcodes=current_item_barcodes_sold 
            )
            sale_payload_items.append(sale_item_payload)

        transaction = Transaction(
            shop=shop, 
            user=user, 
            transaction_type="sale", 
            payload=sale_payload_items
            # Total will be calculated by transaction.save()
        )
        
        transaction.save() # This will also run transaction.clean()

        return jsonify({"message": "Items sold successfully", "transaction_id": str(transaction.id)}), 201

    except (ValueError, Exception) as e: # Catch custom ValueErrors and other exceptions
        # Rollback stock changes
        for change in reversed(committed_stock_changes_for_rollback):
            try:
                if change['type'] == 'serialized_item_deleted':
                    prod_for_rollback = Product.get_by_id(change['product_id'])
                    if prod_for_rollback:
                        # Re-creating the item will trigger Item.save() which increments product quantity
                        reverted_item = Item(barcode=change['barcode'], product=prod_for_rollback)
                        reverted_item.save()
                elif change['type'] == 'nonserialized_product_decremented':
                    Product.objects(id=change['product_id']).update_one(inc__quantity=change['quantity'])
            except Exception as rollback_e:
                # Log rollback error, as the state might be inconsistent
                print(f"Critical error during rollback: {rollback_e}")
        
        error_message = str(e)
        if isinstance(e, ValueError): # Custom validation errors
             return jsonify({"error": f"Sale validation failed: {error_message}"}), 400
        # Check if it's a MongoEngine ValidationError (e.g. from Transaction.clean)
        elif "ValidationError" in type(e).__name__ : # A bit fragile, but captures mongoengine.errors.ValidationError
            return jsonify({"error": f"Transaction data invalid: {error_message}"}), 400
        else: # Other unexpected errors
            print(f"Unexpected error during sale: {e}") # Log for server admin
            return jsonify({"error": "Sale failed due to an unexpected error. Stock changes have been reverted."}), 500


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