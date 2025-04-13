from flask import Blueprint, request, jsonify
import cloudinary.uploader

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image = request.files['image']
    
    # Upload to Cloudinary
    result = cloudinary.uploader.upload(image)

    # Return the secure URL
    return jsonify({
        "message": "Upload successful",
        "url": result.get("secure_url"),
        "public_id": result.get("public_id")
    }), 200
