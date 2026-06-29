# ===
# csv_bulk_import.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ===
#
# WHY I BUILT THIS:
# When I add new products via DSers or a supplier CSV I need
# to get them into the analytics database quickly. Doing it
# row by row through manage_inventory.py would take hours
# for a batch of 50+ products.
#
# This script reads a formatted CSV and loads all rows into
# the inventory table in one go — with duplicate checking,
# error handling, and a summary at the end so I know exactly
# what was imported and what was skipped.
#
# CSV FORMAT REQUIRED:
# The import file must have these exact column headers:
#   SKU | Product Name | Category | Source Feed | Cost (USD) | Current Stock
#
# I keep a template CSV in the project folder so I do not
# have to remember the column names each time.
#
# PRICING ON IMPORT:
# New products get a temporary retail price calculated as:
# cost_usd × 0.75 (USD to GBP) × 1.5 (markup) = retail_gbp
#
# This is intentionally conservative — it gives a safe starting
# price before live_exchange.py runs and applies the real rate.
# I always run live_exchange.py after a bulk import to correct
# the prices with the actual exchange rate.
#
# DUPLICATE HANDLING:
# If a SKU already exists in the database the row is skipped
# not overwritten. This is intentional — I do not want a bulk
# import to accidentally overwrite manually corrected prices.
# To update existing products use manage_inventory.py instead.
# ==

import csv
import sqlite3
import os

DB_NAME = "seamark_inventory.db"
IMPORT_FILE = "seamark_bulk_import_sample.csv"

# Temporary pricing factor applied on import
# USD cost × GBP rate (0.75) × markup (1.5) = starting retail price
# Run live_exchange.py after import to apply the real rate
INITIAL_PRICING_FACTOR = 0.75 * 1.5


def import_csv_catalog():
    """
    Reads seamark_bulk_import_sample.csv and inserts new products
    into the inventory table. Skips duplicates without overwriting.
    """

    # --
    # PRE-FLIGHT CHECK
    # --
    # Check the file exists before opening a database connection
    # — no point connecting to the database if there is nothing to import
    # --

    if not os.path.exists(IMPORT_FILE):
        print(f"\nImport file not found: {IMPORT_FILE}")
        print("Make sure the CSV is in the same folder as this script")
        print("Expected columns: SKU | Product Name | Category | Source Feed | Cost (USD) | Current Stock")
        return

    print(f"\nStarting bulk import from: {IMPORT_FILE}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    imported_count = 0
    skipped_count = 0
    error_count = 0

    # ---
    # READ AND PROCESS CSV
    # --

    with open(IMPORT_FILE, mode='r', encoding='utf-8') as file:

        # DictReader maps each row to column headers automatically
        # so I can access row['SKU'] instead of row[0] — much cleaner
        reader = csv.DictReader(file)

        for row_num, row in enumerate(reader, start=1):

            try:
                # Strip whitespace from text fields — supplier CSVs
                # often have trailing spaces that break SKU lookups
                sku       = row['SKU'].strip()
                item_name = row['Product Name'].strip()
                category  = row['Category'].strip()
                source    = row['Source Feed'].strip()
                cost_usd  = float(row['Cost (USD)'])
                stock     = int(row['Current Stock'])

                # Basic data validation before inserting
                if not sku:
                    print(f"  Row {row_num}: SKU is blank — skipping")
                    skipped_count += 1
                    continue

                if cost_usd < 0 or stock < 0:
                    print(f"  Row {row_num}: Negative cost or stock value — skipping {sku}")
                    skipped_count += 1
                    continue

                # --
                # DUPLICATE CHECK
                # -
                # Check if SKU already exists before inserting.
                # Skipping rather than overwriting is intentional —
                # existing products may have manually corrected prices
                # that I do not want a bulk import to wipe out.
                # --

                cursor.execute("SELECT sku FROM inventory WHERE sku = ?", (sku,))

                if cursor.fetchone():
                    print(f"  Row {row_num}: SKU {sku} already exists — skipping")
                    skipped_count += 1
                    continue

                # Calculate temporary retail price
                # live_exchange.py will correct this with the real rate after import
                retail_gbp = round(cost_usd * INITIAL_PRICING_FACTOR, 2)

                cursor.execute("""
                    INSERT INTO inventory (sku, item_name, category, source, cost_usd, retail_gbp, stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sku, item_name, category, source, cost_usd, retail_gbp, stock))

                print(f"  Row {row_num}: Imported {sku} — {item_name[:30]} | £{retail_gbp}")
                imported_count += 1

            except KeyError as e:
                # Column header does not match expected name
                # Stopping here because if one header is wrong they are probably all wrong
                print(f"\nColumn header error: {e} not found in CSV")
                print("Check your CSV headers match exactly:")
                print("SKU | Product Name | Category | Source Feed | Cost (USD) | Current Stock")
                conn.close()
                return

            except (ValueError, TypeError) as e:
                # Usually means a price or stock field has non-numeric data
                print(f"  Row {row_num}: Data format error — skipping ({e})")
                error_count += 1
                skipped_count += 1

    # ---
    # COMMIT AND SUMMARY
    # --

    conn.commit()
    conn.close()

    print("\n" + "=" * 45)
    print("  BULK IMPORT COMPLETE")
    print("=" * 45)
    print(f"  Imported successfully : {imported_count} products")
    print(f"  Skipped (duplicates)  : {skipped_count} rows")
    print(f"  Errors (bad data)     : {error_count} rows")
    print("=" * 45)

    if imported_count > 0:
        print(f"\nNext step: run live_exchange.py to apply the real")
        print(f"exchange rate to the {imported_count} newly imported products")

    if skipped_count > 0:
        print(f"\nNote: {skipped_count} rows were skipped — use manage_inventory.py")
        print("to update existing products individually")


# --
# ENTRY POINT
# -

if __name__ == "__main__":
    import_csv_catalog()
