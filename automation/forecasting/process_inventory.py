"""
SEAMARK - Inventory Stock-Out Risk Processor (Dropshipping Model)
Reads stock from seamark_inventory.db, matches to Prophet forecast,
flags stock-out risks by velocity + revenue + supplier demand
and saves report to raw_data/inventory_data.csv
"""

import sqlite3
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

print("=" * 60)
print("  SEAMARK - INVENTORY STOCK-OUT RISK PROCESSOR")
print("  Dropshipping Model: Velocity + Revenue + Demand")
print("=" * 60)

# ── Load inventory from SQLite ─────────────────────────────────
conn = sqlite3.connect('seamark_inventory.db')
inv  = pd.read_sql("SELECT item_name, sku, stock, retail_gbp FROM inventory", conn)
conn.close()
print(f"✅ Inventory loaded : {len(inv)} products from seamark_inventory.db")

# ── Load forecast from Supabase ────────────────────────────────
pf = pd.DataFrame(sb.table('product_demand_forecast').select('*').execute().data)
pf = pf.drop_duplicates(subset=['product_name'], keep='first').reset_index(drop=True)
print(f"✅ Forecast loaded  : {len(pf)} products from Supabase")

# ── Match inventory to forecast ────────────────────────────────
inv = inv.rename(columns={'item_name': 'product_name', 'stock': 'stock_qty'})
merged = pf.merge(inv[['product_name', 'stock_qty', 'sku']], on='product_name', how='left')
merged['stock_qty'] = merged['stock_qty'].fillna(0)

# ── Flag stock-out risk (Dropshipping model) ───────────────────
def risk_level(row):
    units   = row['forecast_units_90_days']
    revenue = row['forecast_revenue_90_days']

    # CRITICAL — high revenue AND fast moving
    if revenue >= 500 and units >= 3:  return 'CRITICAL'
    # HIGH — high revenue OR fast moving
    if revenue >= 200 or units >= 5:   return 'HIGH'
    # MEDIUM — moderate demand
    if revenue >= 100 or units >= 3:   return 'MEDIUM'
    # LOW — slow movers
    if units >= 1:                     return 'LOW'
    # OK — no demand forecast
    return 'OK'

merged['stock_risk'] = merged.apply(risk_level, axis=1)

# ── Save report ────────────────────────────────────────────────
out = merged[[
    'product_name', 'price_gbp', 'stock_qty',
    'forecast_units_90_days', 'forecast_revenue_90_days', 'stock_risk'
]].sort_values('stock_risk')

os.makedirs('raw_data', exist_ok=True)
out.to_csv('raw_data/inventory_data.csv', index=False)

# ── Print summary ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("  SEAMARK - STOCK RISK SUMMARY (Dropshipping Model)")
print("=" * 60)
for risk in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'OK']:
    count   = len(merged[merged['stock_risk'] == risk])
    revenue = merged[merged['stock_risk'] == risk]['forecast_revenue_90_days'].sum()
    bar     = '█' * min(count, 30)
    print(f"  {risk:<10} : {count:>4} products  £{revenue:>9,.0f} at risk  {bar}")
print("=" * 60)
print(f"  Report saved to: raw_data/inventory_data.csv")
print("=" * 60)

# ── Top critical products ──────────────────────────────────────
critical = merged[merged['stock_risk'] == 'CRITICAL'].nlargest(10, 'forecast_revenue_90_days')
if len(critical) > 0:
    print("\n  TOP 10 CRITICAL PRODUCTS (supplier check needed):")
    print(f"  {'Product':<45} {'Units':>6} {'Revenue':>10}")
    print("  " + "-" * 65)
    for _, row in critical.iterrows():
        print(f"  {str(row['product_name'])[:44]:<45} {int(row['forecast_units_90_days']):>6} £{row['forecast_revenue_90_days']:>9,.2f}")

# ── Top HIGH risk products ─────────────────────────────────────
high = merged[merged['stock_risk'] == 'HIGH'].nlargest(10, 'forecast_revenue_90_days')
if len(high) > 0:
    print("\n  TOP 10 HIGH RISK PRODUCTS (monitor closely):")
    print(f"  {'Product':<45} {'Units':>6} {'Revenue':>10}")
    print("  " + "-" * 65)
    for _, row in high.iterrows():
        print(f"  {str(row['product_name'])[:44]:<45} {int(row['forecast_units_90_days']):>6} £{row['forecast_revenue_90_days']:>9,.2f}")

print("\n" + "=" * 60)
print("  COMPLETE ✅")
print("=" * 60)
