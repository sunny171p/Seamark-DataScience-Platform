from supabase import create_client
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

pf = pd.DataFrame(sb.table('product_demand_forecast').select('*').execute().data)
pf = pf.drop_duplicates(subset=['product_name'], keep='first').reset_index(drop=True)

sf = pd.read_csv('outputs/sales_forecast_90days.csv')
sf['ds'] = pd.to_datetime(sf['ds'])

sh = pd.read_csv('raw_data/sales_data.csv')
sh['sale_date'] = pd.to_datetime(sh['sale_date'])

avg_price = pf['price_gbp'].mean()
sf['yhat_revenue']       = (sf['yhat']       * avg_price).round(2)
sf['yhat_upper_revenue'] = (sf['yhat_upper'] * avg_price).round(2)
sf['yhat_lower_revenue'] = (sf['yhat_lower'] * avg_price).round(2)

print("=== SUPABASE ===")
print(f"Records        : {len(pf)}")
print(f"Columns        : {pf.columns.tolist()}")
print(f"Avg price      : £{avg_price:.2f}")
print(f"Top forecast   : £{pf['forecast_revenue_90_days'].max():,.0f}")

print("\n=== SALES FORECAST ===")
print(f"Rows           : {len(sf)}")
print(f"Date range     : {sf['ds'].min().date()} to {sf['ds'].max().date()}")
print(f"yhat_revenue   : {sf['yhat_revenue'].head(3).tolist()}")

print("\n=== SALES HISTORY ===")
print(f"Rows           : {len(sh)}")
print(f"Columns        : {sh.columns.tolist()}")
print(f"Date range     : {sh['sale_date'].min().date()} to {sh['sale_date'].max().date()}")
