from flask import Blueprint, jsonify, request
from app.models import Transaction, Shop, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime

transaction_bp = Blueprint('transactions', __name__)

# Helper function to check if user has access to a shop
def check_shop_access(user, shop_id):
    if user.role == "owner":
        return shop_id in [str(s.id) for s in user.shops]
    elif user.role == "employee":
        return user.shop and str(user.shop.id) == str(shop_id)
    return False

@transaction_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get query parameters for filtering
    shop_id = request.args.get('shop_id')
    transaction_type = request.args.get('type')  # 'sale' or 'restock'
    
    # Base query
    query = {}
    
    # If shop_id is provided, verify access and filter by shop
    if shop_id:
        if not check_shop_access(user, shop_id):
            return jsonify({"error": "Unauthorized access to shop"}), 403
        query['shop'] = ObjectId(shop_id)
    else:
        # If no shop_id provided, get all shops user has access to
        if user.role == "owner":
            shop_ids = [s.id for s in user.shops]
            if not shop_ids:
                return jsonify([]), 200
            query['shop__in'] = shop_ids
        elif user.role == "employee":
            if not user.shop:
                return jsonify([]), 200
            query['shop'] = user.shop.id
    
    # Add transaction type filter if provided
    if transaction_type in ['sale', 'restock']:
        query['transaction_type'] = transaction_type
    
    # Get transactions with pagination
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        if page < 1 or per_page < 1:
            return jsonify({"error": "Page and per_page must be positive integers"}), 400
    except ValueError:
        return jsonify({"error": "Invalid page or per_page parameters"}), 400
    
    skip = (page - 1) * per_page
    
    # Get transactions ordered by date (most recent first)
    transactions = Transaction.objects(**query).order_by('-date').skip(skip).limit(per_page)
    total = Transaction.objects(**query).count()
    
    # Serialize transactions
    transactions_list = []
    for transaction in transactions:
        transaction_data = transaction.get_serialized()
        # Add shop name and user name for better context
        shop = Shop.get_by_id(transaction.shop.id)
        user = User.get_by_id(transaction.user.id)
        transaction_data['shop_name'] = shop.name if shop else None
        transaction_data['user_name'] = user.name if user else None
        transactions_list.append(transaction_data)
    
    return jsonify({
        'transactions': transactions_list,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200

@transaction_bp.route('/transactions/<transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction_by_id(transaction_id):
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        transaction = Transaction.get_by_id(transaction_id)
    except:
        return jsonify({"error": "Invalid transaction ID format"}), 400
    
    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404
    
    # Check if user has access to the shop
    if not check_shop_access(user, str(transaction.shop.id)):
        return jsonify({"error": "Unauthorized access to transaction"}), 403
    
    # Get additional context
    transaction_data = transaction.get_serialized()
    shop = Shop.get_by_id(transaction.shop.id)
    transaction_user = User.get_by_id(transaction.user.id)
    
    transaction_data['shop_name'] = shop.name if shop else None
    transaction_data['user_name'] = transaction_user.name if transaction_user else None
    
    return jsonify(transaction_data), 200 