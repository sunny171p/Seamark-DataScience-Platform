# ==
# view_inventory.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ==
#
# WHY I BUILT THIS:
# Before this I was opening DB Browser for SQLite every time
# I wanted to check stock levels — which meant launching a
# separate application, navigating to the right table, and
# scrolling through rows. Too slow for a quick check.
#
# This script prints a clean formatted inventory table in the
# terminal in under a second. I use it several times a day
# to spot low stock before it becomes a problem.
#
# DIFFERENCE FROM manage_inventory.py:
# - view_inventory.py is READ ONLY — it never writes anything
# - manage_inventory.py is for making stock updates
# I kept them separate deliberately so there is no risk of
# accidentally modifying data when I just want to check levels.
#
# WHAT I LOOK FOR WHEN I RUN THIS:
# - Any product with stock below 10 units needs a reorder check
# - Any product where retail_gbp looks wrong after a rate update
# - New products added via CSV import showing up correctly
# ==

import sqlite3


# -
# LOW STOCK THRESHOLD
# -
# Set here so it is easy to adjust without hunting through code.
# Below 10 units I flag for attention — based on our average
# weekly sales velocity this gives roughly one week of buffer.
# --

LOW_STOCK_THRESHOLD = 10


def display_live_inventory():
    """
    Reads and displays all inventory rows from seamark_inventory.db
    in a formatted table. Read-only — makes no changes to the data.
    """

    db_file = "seamark_inventory.db"

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Ordering by stock ascending so low stock items appear first
        # — the most important thing to see at a glance
        cursor.execute("""
            SELECT sku, item_name, category, source, cost_usd, retail_gbp, stock 
            FROM inventory
            ORDER BY stock ASC
        """)

        rows = cursor.fetchall()

        if not rows:
            print("\nInventory table is empty.")
            print("Run csv_bulk_import.py to load product data first.")
            return

        # --
        # DISPLAY TABLE
        # --

        print("\n" + "=" * 105)
        print("  SEAMARK GLOBAL INNOVATIONS — LIVE INVENTORY VIEW")
        print("=" * 105)

        # Column headers
        print(f"  {'SKU':<18} | "
              f"{'PRODUCT NAME':<22} | "
              f"{'CATEGORY':<22} | "
              f"{'SRC':<6} | "
              f"{'COST (USD)':<10} | "
              f"{'RETAIL (GBP)':<12} | "
              f"{'STOCK':<5} | "
              f"STATUS")

        print("  " + "-" * 100)

        low_stock_count = 0
        total_products = len(rows)

        for row in rows:
            sku, item_name, category, source, cost_usd, retail_gbp, stock = row

            # Flag low stock items clearly so they stand out in the terminal
            if stock <= LOW_STOCK_THRESHOLD:
                status = "*** LOW ***"
                low_stock_count += 1
            elif stock == 0:
                status = "*** OUT OF STOCK ***"
                low_stock_count += 1
            else:
                status = "OK"

            print(f"  {sku:<18} | "
                  f"{item_name:<22} | "
                  f"{category:<22} | "
                  f"{source:<6} | "
                  f"${cost_usd:<9.2f} | "
                  f"£{retail_gbp:<11.2f} | "
                  f"{stock:<5} | "
                  f"{status}")

        # -
        # SUMMARY
        # -

        print("  " + "=" * 100)
        print(f"\n  Total products: {total_products}")
        print(f"  Low stock items (under {LOW_STOCK_THRESHOLD} units): {low_stock_count}")

        if low_stock_count > 0:
            print(f"\n  ACTION: {low_stock_count} product(s) need stock review")
            print("  Use manage_inventory.py to update stock levels")
            print("  Use csv_bulk_import.py to bulk update from a CSV file")

        print()

    except sqlite3.OperationalError as e:
        # This usually means the database file does not exist yet
        # or setup_analytics_db.py has not been run
        print(f"\nDatabase error: {e}")
        print("Make sure setup_analytics_db.py has been run first")
        print("Expected database file: seamark_inventory.db")

    finally:
        # finally block ensures connection always closes
        # even if an error occurs mid-read
        conn.close()


# --
# ENTRY POINT
# -

if __name__ == "__main__":
    display_live_inventory()
