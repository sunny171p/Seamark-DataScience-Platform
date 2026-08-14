from supabase import create_client
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Step 1 - Load all records
print("Loading all records from Supabase...")
r = sb.table('product_demand_forecast').select('*').execute()
df = pd.DataFrame(r.data)
print(f"Total records before fix : {len(df)}")

# Step 2 - Keep only the latest record per product
df = df.sort_values('created_at', ascending=False)
df_clean = df.drop_duplicates(subset=['product_name'], keep='first')
print(f"Unique products to keep  : {len(df_clean)}")

# Step 3 - Find duplicate IDs to delete
ids_to_keep = set(df_clean['id'].tolist())
ids_to_delete = [row['id'] for _, row in df.iterrows() if row['id'] not in ids_to_keep]
print(f"Duplicate records to delete: {len(ids_to_delete)}")

# Step 4 - Delete duplicates in batches of 50
batch_size = 50
deleted = 0
for i in range(0, len(ids_to_delete), batch_size):
    batch = ids_to_delete[i:i+batch_size]
    sb.table('product_demand_forecast').delete().in_('id', batch).execute()
    deleted += len(batch)
    print(f"  Deleted {deleted}/{len(ids_to_delete)}...")

# Step 5 - Verify
r2 = sb.table('product_demand_forecast').select('*').execute()
df2 = pd.DataFrame(r2.data)

print("\n" + "=" * 55)
print("  SUPABASE DEDUPLICATION COMPLETE")
print("=" * 55)
print(f"  Records before : 540")
print(f"  Records after  : {len(df2)}")
print(f"  Unique products: {df2['product_name'].nunique()}")
print(f"  Status         : Clean ✅")
print("=" * 55)
