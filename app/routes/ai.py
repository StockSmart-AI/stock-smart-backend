from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import os

prophet_bp = Blueprint('prophet', __name__)

# Get the absolute path to the data directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'demand_forecasting_pattern.csv')

# Create sample data if file doesn't exist
if not os.path.exists(CSV_PATH):
    # Create sample data
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    sample_data = {
        'Store ID': ['store1'] * len(dates),
        'Product ID': ['product1'] * len(dates),
        'Date': dates,
        'Demand': [100 + i % 7 * 20 for i in range(len(dates))],  # Weekly pattern
        'Price': [10.0] * len(dates),
        'Promotions': [0] * len(dates),
        'Seasonality Factors': [1.0] * len(dates),
        'External Factors': [0] * len(dates),
        'Demand Trend': ['stable'] * len(dates),
        'Customer Segments': ['regular'] * len(dates),
        'DayOfWeek': dates.dayofweek,
        'IsWeekend': (dates.dayofweek >= 5).astype(int),
        'Month': dates.month,
        'Season': ['winter', 'spring', 'summer', 'fall'][(dates.month % 12) // 3],
        'IsHoliday': [0] * len(dates),
        'IsFestival': [0] * len(dates),
        'Seasonal Type': ['regular'] * len(dates)
    }
    df = pd.DataFrame(sample_data)
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    # Save to CSV
    df.to_csv(CSV_PATH, index=False)

# Read the CSV file
df = pd.read_csv(CSV_PATH)

def demand_forecast(store_id, product_id, periods=7, plot=False):
    sub_df = df[(df['Store ID'] == store_id) & (df['Product ID'] == product_id)].copy()
    
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
    ], inplace=True)

    sub_df.columns = ['ds', 'y']
    sub_df['ds'] = pd.to_datetime(sub_df['ds'])
    
    train = sub_df[:-periods]
    test = sub_df[-periods:]

    if train['y'].notnull().sum() < 2:
        print(f"Not enough data for store {store_id}")
        return None

    m = Prophet(interval_width=0.95)
    m.fit(train)
    future = m.make_future_dataframe(periods=periods, freq='D')
    forecast = m.predict(future)
    
    merged = forecast[['ds', 'yhat']].merge(test[['ds', 'y']], on='ds', how='inner')
    mae = mean_absolute_error(merged['y'], merged['yhat'])
    print(f"Store {store_id} - MAE: {mae:.2f}")
    
    if plot:
        fig = m.plot(forecast)
        plt.title(f"Forecast for Store {store_id}")
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
            return jsonify({"error": "Not enough data for forecasting"}), 400

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






    