# =
# live_exchange.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ==
#
# WHY I BUILT THIS:
# We source products priced in USD through DSers and AliExpress
# but sell in GBP on our UK storefront. When the exchange rate
# moves significantly our margins get squeezed without us
# noticing — especially on lower margin dropshipping products.
#
# This script fetches the live USD/GBP rate and recalculates
# retail prices across our inventory automatically so we are
# always pricing based on today's rate not last month's.
#
# WHY I USED urllib INSTEAD OF requests:
# requests is the more common choice but it requires installing
# an external package. urllib is built into Python so this
# script runs on any machine without any setup — important
# when I am running this from different environments.
#
# MARKUP LOGIC:
# I use a 1.5x multiplier on cost price as our baseline margin.
# This gives roughly 33% gross margin which covers shipping,
# platform fees, and leaves room for discounts.
# I review this multiplier quarterly based on actual margin data.
#
# FALLBACK RATE:
# If the API is unreachable I fall back to 0.80 which is a
# conservative rate — it slightly underprices rather than
# overprices which protects the customer experience.
# ==

import sqlite3
import urllib.request
import json


# --
# STEP 1 — FETCH LIVE EXCHANGE RATE
# --

def fetch_live_usd_to_gbp():
    """
    Fetches live USD to GBP rate from open.er-api.com
    Falls back to 0.80 if the API is unreachable.
    Free tier API — no key required, rate limited to 1500 calls/month.
    """
    url = "https://open.er-api.com/v6/latest/USD"

    print("Connecting to live currency exchange API...")

    try:
        # timeout=5 so the script does not hang if the API is slow
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            rate = data["rates"]["GBP"]
            print(f"Live rate fetched: 1 USD = {rate:.4f} GBP")
            return rate

    except Exception as e:
        # API occasionally goes down — fallback keeps the script running
        # 0.80 is conservative — better to underprice slightly than overprice
        print(f"Could not reach API ({e})")
        print("Using fallback rate: 1 USD = 0.80 GBP")
        return 0.80


# ---
# STEP 2 — RECALCULATE AND UPDATE RETAIL PRICES
# --

def recalibrate_store_pricing():
    """
    Reads all inventory rows from SQLite, applies live exchange rate
    and markup multiplier, then updates retail_gbp for each product.
    """

    db_file = "seamark_inventory.db"

    # Fetch today's live rate before opening the database
    live_rate = fetch_live_usd_to_gbp()

    # 1.5x markup on cost price = ~33% gross margin
    # Covers: Shopify fees, payment processing, shipping, and promotions
    # Reviewed quarterly — last reviewed June 2026
    markup_factor = 1.5

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT id, sku, cost_usd FROM inventory")
    inventory_rows = cursor.fetchall()

    if not inventory_rows:
        print("No inventory rows found in database — check seamark_inventory.db exists")
        conn.close()
        return

    print(f"\nRecalculating retail prices for {len(inventory_rows)} products...")
    print(f"Rate used: 1 USD = {live_rate:.4f} GBP | Markup: {markup_factor}x\n")

    updated_count = 0

    for row in inventory_rows:
        item_id, sku, cost_usd = row

        # Formula: (cost in USD × exchange rate) × markup = retail price in GBP
        new_retail_gbp = round((cost_usd * live_rate) * markup_factor, 2)

        cursor.execute(
            "UPDATE inventory SET retail_gbp = ? WHERE id = ?",
            (new_retail_gbp, item_id)
        )

        print(f"  SKU {sku}: ${cost_usd:.2f} USD -> £{new_retail_gbp:.2f} GBP")
        updated_count += 1

    conn.commit()
    conn.close()

    print(f"\nDone — {updated_count} products updated with live GBP pricing")
    print(f"Exchange rate applied: 1 USD = {live_rate:.4f} GBP")
    print("Run this script whenever the rate moves more than 2% to keep margins accurate")


# -
# ENTRY POINT
# -

if __name__ == "__main__":
    recalibrate_store_pricing()
