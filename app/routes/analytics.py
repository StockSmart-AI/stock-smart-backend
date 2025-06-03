from flask import Blueprint, jsonify, request
from app.models import Transaction, Product, Shop, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

analytics_bp = Blueprint('analytics', __name__)

# Helper function to get shop by ID and check user access
def get_shop_or_404(shop_id_str):
    try:
        shop_id = ObjectId(shop_id_str)
    except Exception:
        return None, jsonify({"error": "Invalid shop_id format"}), 400
    
    shop = Shop.get_by_id(shop_id)
    if not shop:
        return None, jsonify({"error": "Shop not found"}), 404

    # Authorization check
    current_user_email = get_jwt_identity()
    user = User.get_by_email(current_user_email)

    if not user:
        return None, jsonify({"error": "User not found"}), 401 

    has_access = False
    if user.role == "owner":
        # Check if the shop_id is in the owner's list of shops
        if shop_id in [s.id for s in user.shops]:
            has_access = True
    elif user.role == "employee":
        # Check if the employee is assigned to this shop
        if user.shop and user.shop.id == shop_id:
            has_access = True
    
    if not has_access:
        return None, jsonify({"error": "Access forbidden: You do not have permission to view analytics for this shop."}), 403
        
    return shop, None, None


@analytics_bp.route('/summary_cards/<shop_id_str>', methods=['GET'])
@jwt_required()
def get_summary_cards_data(shop_id_str):
    shop, error_response, status_code = get_shop_or_404(shop_id_str)
    if error_response:
        return error_response, status_code

    products_in_shop = Product.objects(shop=shop.id)
    total_stock = products_in_shop.sum('quantity')
    
    low_stock_products_list = [p for p in products_in_shop if p.quantity <= p.threshold]
    low_stock_count = len(low_stock_products_list)
    
    out_of_stock_count = products_in_shop.filter(quantity=0).count()
    
    stock_value = 0
    for p in products_in_shop:
        stock_value += p.price * p.quantity
    
    summary_cards_data = [
        {"value": str(total_stock), "label": "Total Stock"},
        {"value": str(low_stock_count), "label": "Low Stock"},
        {"value": str(out_of_stock_count), "label": "Out of Stock"},
        {"value": f"{stock_value:.2f}", "label": "Stock Value (ETB)"},
    ]
    return jsonify(summary_cards_data), 200


@analytics_bp.route('/pie_chart/stock_by_category/<shop_id_str>', methods=['GET'])
@jwt_required()
def get_pie_chart_data(shop_id_str):
    shop, error_response, status_code = get_shop_or_404(shop_id_str)
    if error_response:
        return error_response, status_code

    products_in_shop = Product.objects(shop=shop.id)
    
    category_stock_distribution = defaultdict(int)
    for product in products_in_shop:
        category_name = product.category if product.category else "Uncategorized"
        category_stock_distribution[category_name] += product.quantity
    
    pie_chart_data = []
    for category, total_quantity in category_stock_distribution.items():
        if total_quantity > 0: # Only include categories with stock
            pie_chart_data.append({
                "name": category,
                "population": total_quantity  # "population" here means total quantity in stock for that category
            })
    
    return jsonify(pie_chart_data), 200


@analytics_bp.route('/line_chart/monthly_sales/<shop_id_str>', methods=['GET'])
@jwt_required()
def get_line_chart_data(shop_id_str):
    shop, error_response, status_code = get_shop_or_404(shop_id_str)
    if error_response:
        return error_response, status_code

    line_chart_labels = []
    line_chart_sales_data = []
    today = datetime.utcnow()
    for i in range(5, -1, -1): 
        target_date = today - timedelta(days=i * 30) 
        month_name = calendar.month_abbr[target_date.month]
        year_abbr = target_date.strftime("%y")
        line_chart_labels.append(f"{month_name} '{year_abbr}")

        first_day_of_month = datetime(target_date.year, target_date.month, 1)
        if target_date.month == 12:
            last_day_of_month = datetime(target_date.year, target_date.month, 31, 23, 59, 59)
        else:
            last_day_of_month = datetime(target_date.year, target_date.month + 1, 1) - timedelta(seconds=1)

        monthly_sales = Transaction.objects(
            shop=shop.id,
            transaction_type="sale",
            date__gte=first_day_of_month,
            date__lte=last_day_of_month
        ).sum('total')
        line_chart_sales_data.append(monthly_sales or 0)
            
    line_chart_data = {
        "labels": line_chart_labels,
        "datasets": [{"data": line_chart_sales_data}]
    }
    return jsonify(line_chart_data), 200


@analytics_bp.route('/bar_chart/daily_sales/<shop_id_str>', methods=['GET'])
@jwt_required()
def get_bar_chart_data(shop_id_str):
    shop, error_response, status_code = get_shop_or_404(shop_id_str)
    if error_response:
        return error_response, status_code

    bar_chart_labels = []
    bar_chart_sales_data = []
    today = datetime.utcnow()
    for i in range(6, -1, -1): 
        day_date = today - timedelta(days=i)
        bar_chart_labels.append(day_date.strftime("%a")) 
        
        start_of_day = datetime(day_date.year, day_date.month, day_date.day, 0, 0, 0)
        end_of_day = datetime(day_date.year, day_date.month, day_date.day, 23, 59, 59)
        
        daily_sales = Transaction.objects(
            shop=shop.id,
            transaction_type="sale",
            date__gte=start_of_day,
            date__lte=end_of_day
        ).sum('total')
        bar_chart_sales_data.append(daily_sales or 0)

    bar_chart_data = {
        "labels": bar_chart_labels,
        "datasets": [{"data": bar_chart_sales_data}]
    }
    return jsonify(bar_chart_data), 200


@analytics_bp.route('/critical_products/<shop_id_str>', methods=['GET'])
@jwt_required()
def get_critical_products_data(shop_id_str):
    shop, error_response, status_code = get_shop_or_404(shop_id_str)
    if error_response:
        return error_response, status_code

    products_in_shop = Product.objects(shop=shop.id)
    low_stock_products_list = [p for p in products_in_shop if p.quantity <= p.threshold]
    
    critical_products_list_data = []
    for p in low_stock_products_list: 
         critical_products_list_data.append({
            "name": p.name,
            "category": p.category,
            "stock": str(p.quantity),
            "lowStock": True 
        })
    return jsonify(critical_products_list_data), 200


@analytics_bp.route('/top_selling_products/<shop_id_str>', methods=['GET'])
@jwt_required()
def get_top_selling_products_data(shop_id_str):
    shop, error_response, status_code = get_shop_or_404(shop_id_str)
    if error_response:
        return error_response, status_code

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    sales_transactions = Transaction.objects(
        shop=shop.id, 
        transaction_type="sale",
        date__gte=thirty_days_ago
    )
    
    product_units_sold = defaultdict(int)
    for trans in sales_transactions: 
        for item in trans.payload:
            product_units_sold[item.name] += item.quantity 
    
    sorted_top_products = sorted(product_units_sold.items(), key=lambda x: x[1], reverse=True)[:5] 
    
    top_selling_products_list_data = []
    for name, units in sorted_top_products:
        top_selling_products_list_data.append({
            "name": name,
            "unitsSold": str(units)
        })
    return jsonify(top_selling_products_list_data), 200


@analytics_bp.route('/top_stocked_products/<shop_id_str>', methods=['GET'])
@jwt_required()
def get_top_stocked_products_data(shop_id_str):
    shop, error_response, status_code = get_shop_or_404(shop_id_str)
    if error_response:
        return error_response, status_code

    # Query products for the shop, order by quantity descending, and limit to top 5
    top_stocked_products = Product.objects(shop=shop.id).order_by('-quantity').limit(5)

    top_stocked_products_list_data = []
    for product in top_stocked_products:
        if product.quantity > 0: # Only include products that are in stock
            top_stocked_products_list_data.append({
                "name": product.name,
                "category": product.category,
                "stock": str(product.quantity)
            })
    
    return jsonify(top_stocked_products_list_data), 200
