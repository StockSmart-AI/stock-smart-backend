from flask import Blueprint
import joblib

prophet_bp = Blueprint('prophet', __name__)

file = open('../ai_models/prophet_model (2).pkl','rb')
prophet_model = joblib.load(file)
@prophet_bp.route('/predict', methods=['POST'])

