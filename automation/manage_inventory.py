# ==
# manage_inventory.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ==
#
# WHY I BUILT THIS:
# Updating stock levels in Shopify admin requires logging in,
# navigating to the product, finding the right variant, and
# saving — which takes 2-3 minutes per product. When we receive
# a delivery or need to zero out sold-out items across multiple
# SKUs that adds up quickly.
#
# This CLI tool lets me look up any SKU and update its stock
# count in seconds directly from the terminal without touching
# the Shopify admin at all.
#
# WHY CLI INSTEAD OF A WEB INTERFACE:
# I built the web dashboard separately (online_app.py) but for
# quick stock corrections during the day a command line tool
# is faster — no browser, no login, just run and done.
#
# SAFETY DECISIONS:
# - Parameterised SQL queries throughout to prevent injection
# - Negative stock values are blocked at input validation
# - User must confirm before any update is written
# - Read-only lookup available without making any changes
#
# KNOWN LIMITATION:
# This updates the local SQLite database only — not Shopify
# directly. I sync changes back to Shopify via CSV import
# using csv_bulk_import.py after batch updates are done.
# ==

import sqlite3


# --
# MAIN FUNCTION — STOCK LOOKUP AND UPDATE
# --

def manage_store_item():
    """
    Interactive CLI tool for looking up and updating stock levels.
    Connects to seamark_inventory.db and updates the inventory table.
    """

    db_file = "seamark_inventory.db"

    print("\n" + "=" * 45)
    print("  SEAMARK STOCK MANAGEMENT TOOL")
    print("  Internal use only — Sunday Azeez")
    print("=" * 45)

    # Get SKU from user — strip whitespace to avoid lookup failures
    # from accidental spaces (happened a few times early on)
    sku_input = input("\nEnter Product SKU to look up: ").strip().upper()

    if not sku_input:
        print("SKU cannot be blank. Exiting.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # --
    # STEP 1 — LOOK UP THE PRODUCT
    # ---
    # Using parameterised query — never format SKU directly into
    # the SQL string as that would open an injection vulnerability
    # ---

    cursor.execute(
        "SELECT item_name, category, stock, retail_gbp FROM inventory WHERE sku = ?",
        (sku_input,)
    )
    row = cursor.fetchone()

    if not row:
        print(f"\nNo product found with SKU '{sku_input}'")
        print("Check the SKU is correct — remember it is case sensitive")
        conn.close()
        return

    item_name, category, current_stock, retail_price = row

    # Display current product details clearly before asking for changes
    print(f"\nProduct found:")
    print(f"  Name     : {item_name}")
    print(f"  Category : {category}")
    print(f"  Price    : £{retail_price:.2f}")
    print(f"  Stock    : {current_stock} units")

    # Flag low stock immediately so it is not missed
    if current_stock <= 5:
        print(f"  WARNING  : Stock is low — consider reordering soon")


    # ---
    # STEP 2 — OFFER STOCK UPDATE
    # ---

    choice = input("\nUpdate stock level for this item? (y/n): ").strip().lower()

    if choice != 'y':
        print("No changes made. Exiting.")
        conn.close()
        return

    try:
        new_stock = int(input("Enter new total stock count: ").strip())

        if new_stock < 0:
            print("Stock cannot be negative. No changes made.")
            conn.close()
            return

        # Show what is about to change and ask for confirmation
        # Added this after I accidentally zeroed out the wrong SKU once
        print(f"\nAbout to change: {item_name}")
        print(f"  Current stock : {current_stock} units")
        print(f"  New stock     : {new_stock} units")

        confirm = input("\nConfirm update? (y/n): ").strip().lower()

        if confirm != 'y':
            print("Update cancelled. No changes made.")
            conn.close()
            return

        # Write the update to the database
        cursor.execute(
            "UPDATE inventory SET stock = ? WHERE sku = ?",
            (new_stock, sku_input)
        )
        conn.commit()

        print(f"\nStock updated successfully")
        print(f"  SKU      : {sku_input}")
        print(f"  Product  : {item_name}")
        print(f"  Previous : {current_stock} units")
        print(f"  Updated  : {new_stock} units")
        print("\nRemember to sync this change to Shopify via csv_bulk_import.py")

    except ValueError:
        print("Invalid input — stock must be a whole number. No changes made.")

    finally:
        conn.close()


# --
# ENTRY POINT
# --

if __name__ == "__main__":
    manage_store_item()
