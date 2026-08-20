# ===
# setup_analytics_db.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ==
#
# WHY I BUILT THIS:
# All the automation scripts need a shared database to read
# from and write to. Rather than using separate CSV files for
# everything — which gets messy fast — I set up a proper
# relational SQLite database with three linked tables.
#
# I chose SQLite specifically because:
# - No server setup required — the database is just a file
# - Works on any machine without installing anything extra
# - Good enough for our current data volume (thousands not millions)
# - Easy to inspect with DB Browser for SQLite when debugging
#
# SCHEMA DECISIONS:
# Three tables that mirror how the business actually works:
# - suppliers: who we buy from
# - inventory: what we stock and at what price
# - sales_log: what has sold and when
#
# I added foreign keys so the database enforces relationships —
# you cannot add a sale for a SKU that does not exist in inventory.
# This caught a data entry error early on that would have skewed
# the profit margin calculations.
#
# SAMPLE DATA:
# The mock rows use real product types from our catalogue so
# the downstream reports produce meaningful output during testing.
# These get replaced with real data via csv_bulk_import.py.
# ===

import sqlite3

DB_FILE = "seamark_inventory.db"


def initialize_store_analytics_db():
    """
    Creates the three core tables for the Seamark analytics database
    and seeds them with sample data for testing downstream scripts.
    Run this once on any new machine before running other scripts.
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Foreign key enforcement is off by default in SQLite
    # Must be enabled per connection — easy to forget, important to include
    cursor.execute("PRAGMA foreign_keys = ON;")
    print("Foreign key enforcement enabled")


    # ---
    # TABLE 1 — SUPPLIERS
    # -
    # Stores our supplier partners and their regions.
    # Region matters for shipping time estimates and duty calculations
    # — East Asia suppliers have longer lead times than UK ones.
    # -

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name  TEXT NOT NULL UNIQUE,
            contact_email  TEXT,
            region         TEXT
        );
    """)
    print("Table ready: suppliers")


    # -
    # TABLE 2 — INVENTORY
    # --
    # Core product table. Links to suppliers via supplier_id.
    # ON DELETE SET NULL means if a supplier is removed the
    # product stays in the database — we do not lose stock records
    # just because a supplier relationship ends.
    #
    # cost_usd stores the AliExpress/DSers cost in USD.
    # retail_gbp is calculated by live_exchange.py and updated
    # whenever the exchange rate moves significantly.
    # --

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            sku            TEXT PRIMARY KEY,
            item_name      TEXT NOT NULL,
            category       TEXT,
            cost_usd       REAL NOT NULL,
            retail_gbp     REAL NOT NULL,
            stock          INTEGER NOT NULL,
            supplier_id    INTEGER,
            FOREIGN KEY (supplier_id) 
                REFERENCES suppliers(supplier_id) 
                ON DELETE SET NULL
        );
    """)
    print("Table ready: inventory")


    # -
    # TABLE 3 — SALES LOG
    # -
    # Records every sale transaction linked back to inventory by SKU.
    # ON DELETE CASCADE means if a product is removed from inventory
    # its sales history is also removed — keeps the data consistent.
    #
    # sale_date defaults to the current timestamp automatically
    # so I do not need to pass a date when inserting sales records.
    # --

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_log (
            sale_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sku            TEXT NOT NULL,
            qty_sold     INTEGER NOT NULL,
            sale_price_gbp REAL NOT NULL,
            sale_date      TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sku) 
                REFERENCES inventory(sku) 
                ON DELETE CASCADE
        );
    """)
    print("Table ready: sales_log")


    # ---
    # SEED DATA — SUPPLIERS
    # ---
    # Two real supplier types we work with — audio/wearables from
    # North America and appliances/electronics from East Asia.
    # INSERT OR IGNORE means re-running this script is safe —
    # it will not duplicate rows if the database already exists.
    # ---

    sample_suppliers = [
        ("Global Audio Logistics", "logistics@globalaudio.com", "North America"),
        ("Apex Appliance Factory", "orders@apexfactory.com", "East Asia")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO suppliers (supplier_name, contact_email, region)
        VALUES (?, ?, ?);
    """, sample_suppliers)

    print(f"Suppliers seeded: {len(sample_suppliers)} rows")


    # ---
    # SEED DATA — INVENTORY PRODUCTS
    # ---
    # Using real product types from the Seamark catalogue so the
    # profit margin reports produce meaningful numbers during testing.
    # Prices reflect approximate real costs and retail values.
    # ---

    sample_products = [
        ("SMK-EARBUDS-01", "Wireless Earbuds",    "Audio & Wearables",  19.99, 22.32,  40, 1),
        ("SMK-TV-05",      "4K Smart TV 55 inch", "Home Electronics",  299.00, 333.90, 15, 2),
        ("SMK-LAPTOP-02",  "Pro 15-inch Laptop",  "Home Electronics",  499.50, 550.00, 10, 2)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO inventory (sku, item_name, category, cost_usd, retail_gbp, stock, supplier_id)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, sample_products)

    print(f"Products seeded: {len(sample_products)} rows")


    # -
    # SEED DATA — SALES HISTORY
    # -
    # Simulating a realistic sales pattern for testing.
    # Earbuds sell in higher volume, laptops in lower volume —
    # which matches what we actually see in the Shopify data.
    # -

    sample_sales = [
        ("SMK-EARBUDS-01", 5, 22.32),
        ("SMK-EARBUDS-01", 2, 22.32),
        ("SMK-TV-05",      1, 333.90),
        ("SMK-LAPTOP-02",  3, 550.00)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO sales_log (sku, qty_sold, sale_price_gbp)
        VALUES (?, ?, ?);
    """, sample_sales)

    print(f"Sales records seeded: {len(sample_sales)} rows")


    # --
    # COMMIT AND CLOSE
    # --

    conn.commit()
    conn.close()

    print("\nDatabase initialised successfully: " + DB_FILE)
    print("Next step: run csv_bulk_import.py to load real product data")


# ---
# ENTRY POINT
# -

if __name__ == "__main__":
    initialize_store_analytics_db()
