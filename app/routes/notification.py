from flask import Blueprint, request, jsonify
from app.models import Notification, Shop, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    notifications = Notification.get_notifications_for_user(user.id)
    return jsonify([notif.get_serialized() for notif in notifications]), 200

@notification_bp.route('/shop/<shop_id>/request-access', methods=['POST'])
@jwt_required()
def request_shop_access(shop_id):
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if user.role != "employee":
        return jsonify({"error": "Only employees can request shop access"}), 403
    
    shop = Shop.get_by_id(shop_id)
    if not shop:
        return jsonify({"error": "Shop not found"}), 404
    
    # Check if user already has a pending request
    existing_request = Notification.objects(
        sender=user,
        shop=shop,
        type='access_request',
        status='pending'
    ).first()
    
    if existing_request:
        return jsonify({"error": "You already have a pending request for this shop"}), 400
    
    # Create new access request notification
    notification = Notification(
        sender=user,
        recipient=shop.owner,
        shop=shop,
        type='access_request',
        message=f"{user.name} is requesting access to {shop.name}",
        status='pending'
    )
    notification.save()
    
    return jsonify(notification.get_serialized()), 201

@notification_bp.route('/notifications/<notification_id>/respond', methods=['POST'])
@jwt_required()
def respond_to_access_request(notification_id):
    email = get_jwt_identity()
    user = User.get_by_email(email)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    notification = Notification.get_by_id(notification_id)
    if not notification:
        return jsonify({"error": "Notification not found"}), 404
    
    # Verify that the responding user is the shop owner
    if str(notification.recipient.id) != str(user.id):
        return jsonify({"error": "Unauthorized to respond to this request"}), 403
    
    data = request.get_json()
    action = data.get('action')
    
    if action not in ['approve', 'reject']:
        return jsonify({"error": "Invalid action. Must be 'approve' or 'reject'"}), 400
    
    if notification.status != 'pending':
        return jsonify({"error": "This request has already been processed"}), 400
    
    # Update notification status
    notification.status = 'approved' if action == 'approve' else 'rejected'
    notification.updated_at = datetime.utcnow()
    notification.save()
    
    # If approved, update user's shop reference
    if action == 'approve':
        employee = notification.sender
        employee.shop = notification.shop
        employee.save()
        
        # Create a notification for the employee
        response_notification = Notification(
            sender=user,
            recipient=employee,
            shop=notification.shop,
            type='access_granted',
            message=f"Your access request for {notification.shop.name} has been approved",
            status='approved'
        )
        response_notification.save()
    else:
        # Create a notification for the employee
        response_notification = Notification(
            sender=user,
            recipient=notification.sender,
            shop=notification.shop,
            type='access_denied',
            message=f"Your access request for {notification.shop.name} has been denied",
            status='rejected'
        )
        response_notification.save()
    
    return jsonify(notification.get_serialized()), 200 