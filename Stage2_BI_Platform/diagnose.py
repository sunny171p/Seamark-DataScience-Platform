import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Check forecast
pf = pd.DataFrame(sb.table('product_demand_forecast').select('*').execute().data)
print(f"=== SUPABASE FORECAST ===")
print(f"Records       : {len(pf)}")
print(f"Columns       : {pf.columns.tolist()}")
print(f"Sample        : {pf.head(2).to_string()}")

# Check sales forecast
sf = pd.read_csv('outputs/sales_forecast_90days.csv')
print(f"\n=== SALES FORECAST CSV ===")
print(f"Rows          : {len(sf)}")
print(f"Columns       : {sf.columns.tolist()}")
print(f"Date range    : {sf['ds'].min()} to {sf['ds'].max()}")
print(f"Sample yhat   : {sf['yhat'].head(5).tolist()}")

# Check sessions
ses = pd.read_csv('raw_data/sessions_by_month_365d.csv')
print(f"\n=== SESSIONS ===")
print(ses.to_string())

# Check price check
pc = pd.read_csv('outputs/price_check_enriched.csv')
print(f"\n=== PRICE CHECK ===")
print(f"Product Status values: {pc['Product Status'].value_counts().to_dict()}")
print(f"Category sample      : {pc['Category'].value_counts().head(5).to_dict()}")
