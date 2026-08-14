from supabase import create_client
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

r = sb.table('product_demand_forecast').select('*').execute()
df = pd.DataFrame(r.data)

print(f"Total records in Supabase : {len(df)}")
print(f"Unique products           : {df['product_name'].nunique()}")
print(f"Columns                   : {df.columns.tolist()}")
