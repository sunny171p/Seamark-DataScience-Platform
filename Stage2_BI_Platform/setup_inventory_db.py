"""
SEAMARK - Setup Inventory Database
Creates the inventory table and populates it from products_export.csv
"""

import sqlite3
import pandas as pd

DB_FILE  = 'seamark_inventory.db'
CSV_FILE = 'raw_data/products_export.csv'

# Load products
df = pd.read_csv(CSV_FILE)
df = df[df['Title'].notna()][['Title', 'Variant SKU', 'Variant Price']].copy()
df = df.drop_duplicates(subset=['Title']).reset_index(drop=True)
df.columns = ['item_name', 'sku', 'retail_gbp']
df['sku']        = df['sku'].fillna(pd.Series(['SKU-' + str(i) for i in df.index]))
df['category']   = 'General'
df['stock']      = 0
df['retail_gbp'] = pd.to_numeric(df['retail_gbp'], errors='coerce').fillna(0)

# Create database and table
conn   = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        sku        TEXT UNIQUE,
        item_name  TEXT,
        category   TEXT,
        stock      INTEGER DEFAULT 0,
        retail_gbp REAL
    )
""")

# Insert products
inserted = 0
for _, row in df.iterrows():
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO inventory (sku, item_name, category, stock, retail_gbp)
            VALUES (?, ?, ?, ?, ?)
        """, (row['sku'], row['item_name'], row['category'], row['stock'], row['retail_gbp']))
        inserted += 1
    except Exception as e:
        print(f"Skipped: {row['item_name']} — {e}")

conn.commit()
conn.close()

print("=" * 50)
print("  SEAMARK INVENTORY DB SETUP COMPLETE")
print("=" * 50)
print(f"  Products inserted : {inserted}")
print(f"  Database          : {DB_FILE}")
print(f"\n  Next: run manage_inventory.py to update stock levels")
print("=" * 50)
