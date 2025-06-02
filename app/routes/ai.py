from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
from bson import ObjectId

prophet_bp = Blueprint('prophet', __name__)

# Step 1: Load original CSV
df = pd.read_csv('../data/demand_forecasting_pattern.csv')

# Step 2: Generate MongoDB-safe ObjectIds
store_id_map = {store_id: str(ObjectId()) for store_id in df['Store ID'].unique()}
product_id_map = {product_id: str(ObjectId()) for product_id in df['Product ID'].unique()}

# Step 3: Add ObjectId columns to DataFrame
df['store_oid'] = df['Store ID'].map(store_id_map)
df['product_oid'] = df['Product ID'].map(product_id_map)


def demand_forecast(store_oid, product_oid, periods=7, plot=False):
    # Use ObjectId-based IDs for filtering
    sub_df = df[(df['store_oid'] == store_oid) & (df['product_oid'] == product_oid)].copy()

    sub_df.drop(columns=[
        'Product ID',
        'Store ID',
        'Price',
        'Promotions',
        'Seasonality Factors',
        'External Factors',
        'Demand Trend',
        'Customer Segments',
        'DayOfWeek',
        'IsWeekend',
        'Month',
        'Season',
        'IsHoliday',
        'IsFestival',
        'Seasonal Type',
        'store_oid',
        'product_oid'
    ], inplace=True)

    sub_df.columns = ['ds', 'y']
    sub_df['ds'] = pd.to_datetime(sub_df['ds'])

    train = sub_df[:-periods]
    test = sub_df[-periods:]

    if train['y'].notnull().sum() < 2:
        print(f"Not enough data for store {store_oid}")
        return None, f"Not enough data for store {store_oid}"

    m = Prophet(interval_width=0.95)
    m.fit(train)
    future = m.make_future_dataframe(periods=periods, freq='D')
    forecast = m.predict(future)

    merged = forecast[['ds', 'yhat']].merge(test[['ds', 'y']], on='ds', how='inner')
    mae = mean_absolute_error(merged['y'], merged['yhat'])
    print(f"Store {store_oid} - MAE: {mae:.2f}")

    if plot:
        fig = m.plot(forecast)
        plt.title(f"Forecast for Store {store_oid}")
        plt.show()

    return forecast, mae


@prophet_bp.route('/forecast', methods=['POST'])
@jwt_required()
def get_forecast():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON payload. Please send a JSON object."}), 400

    store_id = data.get('store_id')
    product_id = data.get('product_id')
    periods = data.get('periods', 7)

    if not store_id or not product_id:
        return jsonify({"error": "store_id and product_id are required."}), 400
    if not isinstance(periods, int) or periods <= 0:
        return jsonify({"error": "periods must be a positive integer."}), 400

    try:
        forecast_df, mae = demand_forecast(store_id, product_id, periods)
        if forecast_df is None:
            return jsonify({"error": mae}), 400

        forecast_data = forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).to_dict(orient='records')

        return jsonify({
            "store_id": store_id,
            "product_id": product_id,
            "periods": periods,
            "mae": mae,
            "forecast": forecast_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
