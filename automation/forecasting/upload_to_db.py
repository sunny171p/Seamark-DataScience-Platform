# ============================================================
# SEAMARK GLOBAL INNOVATIONS
# Upload Forecast Data to Supabase Cloud Database
# ============================================================

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

print("Connecting to Seamark cloud database...")

# Connect to Supabase
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

cursor = conn.cursor()
print("Connected successfully! ✅")

# Create the forecast table if it does not exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_forecast (
        id SERIAL PRIMARY KEY,
        forecast_date DATE,
        predicted_revenue NUMERIC(10,2),
        lower_bound NUMERIC(10,2),
        upper_bound NUMERIC(10,2),
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()
print("Table ready ✅")

# Load the forecast CSV
forecast = pd.read_csv('outputs/sales_forecast_90days.csv')
forecast = forecast[forecast['ds'] > '2026-08-10']

# Upload each row
count = 0
for _, row in forecast.iterrows():
    cursor.execute("""
        INSERT INTO sales_forecast (forecast_date, predicted_revenue, lower_bound, upper_bound)
        VALUES (%s, %s, %s, %s)
    """, (row['ds'], round(row['yhat'], 2), round(row['yhat_lower'], 2), round(row['yhat_upper'], 2)))
    count += 1

conn.commit()
cursor.close()
conn.close()

print("=" * 55)
print("  SEAMARK — DATABASE UPLOAD COMPLETE")
print("=" * 55)
print(f"  Rows uploaded : {count} forecast days")
print(f"  Database      : Supabase (North EU)")
print(f"  Table         : sales_forecast")
print("=" * 55)
