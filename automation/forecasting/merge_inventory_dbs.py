"""
SEAMARK - Merge Inventory Databases
Copies real stock values from automation/seamark_inventory.db
into the root seamark_inventory.db by matching on item_name
"""

import sqlite3
import os

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))

ROOT_DB = os.path.join(PROJECT_ROOT, 'seamark_inventory.db')
AUTO_DB = os.path.join(PROJECT_ROOT, 'automation', 'seamark_inventory.db')

# Load real stock from automation DB
conn_auto = sqlite3.connect(AUTO_DB)
cursor_auto = conn_auto.cursor()
cursor_auto.execute("SELECT item_name, stock FROM inventory WHERE stock > 0")
real_stock = cursor_auto.fetchall()
conn_auto.close()

print(f"✅ Real stock entries found: {len(real_stock)}")

# Update root DB with real stock values
conn_root   = sqlite3.connect(ROOT_DB)
cursor_root = conn_root.cursor()

updated = 0
for item_name, stock in real_stock:
    cursor_root.execute(
        "UPDATE inventory SET stock = ? WHERE item_name LIKE ?",
        (stock, f"%{item_name[:30]}%")
    )
    if cursor_root.rowcount > 0:
        updated += 1
        print(f"  Updated: {item_name[:50]} → {stock} units")

conn_root.commit()
conn_root.close()

print(f"\n✅ Updated {updated} products in root seamark_inventory.db")
print("   Now run: python automation/forecasting/process_inventory.py")
