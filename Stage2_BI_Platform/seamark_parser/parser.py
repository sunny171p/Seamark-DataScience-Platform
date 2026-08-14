# =
# parser.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# =
#
# WHY I BUILT THIS AS A SEPARATE MODULE:
# Every supplier sends product data in a slightly different
# format. AliExpress exports look different from DSers exports
# which look different again from manual supplier spreadsheets.
#
# Rather than writing cleaning logic inside every script that
# needs it, I pulled it out into this reusable module. Any
# script in the project can import clean_and_format_feed()
# and get consistently structured data back every time.
#
# WHAT THIS FIXES IN RAW SUPPLIER DATA:
# - SKUs come in mixed case ("smk-tv-05", "SMK-TV-05", "Smk-Tv-05")
#   — standardised to uppercase throughout
# - Price fields sometimes come through as strings ("29.99")
#   or missing entirely — converted to float with a 0.0 fallback
# - Category field is often blank in AliExpress exports
#   — defaults to "Uncategorized" so downstream scripts do not break
# - Stock occasionally comes through as a float (e.g. 10.0)
#   — cast to int to keep the database schema happy
#
# HOW TO USE THIS IN OTHER SCRIPTS:
#   from seamark_parser.parser import clean_and_format_feed
#   cleaned = clean_and_format_feed(raw_supplier_data)
#
# INPUT:  list of dicts (raw supplier rows)
# OUTPUT: list of dicts (cleaned, standardised rows ready for DB insert)
# =


def clean_and_format_feed(raw_items):
    """
    Cleans and standardises a list of raw supplier product rows.
    Returns a list of consistently structured dicts ready for
    insertion into the inventory table or further analysis.

    Args:
        raw_items: list of dicts from supplier export or API response

    Returns:
        cleaned_list: list of standardised product dicts
    """

    cleaned_list = []
    skipped_count = 0

    for index, item in enumerate(raw_items):

        try:
            # ---
            # SKU — standardise to uppercase and strip whitespace
            # ---
            # Suppliers are inconsistent with casing — seen all three:
            # "smk-earbuds-01", "SMK-EARBUDS-01", "Smk-Earbuds-01"
            # Uppercase throughout so database lookups always match
            # ---
            raw_sku = item.get("sku", f"UNKNOWN-{index}")
            clean_sku = str(raw_sku).strip().upper()

            # ---
            # PRICE — convert to float safely
            # --
            # Some feeds send price as a string, some as None, some missing
            # entirely. float() handles "29.99" -> 29.99 cleanly.
            # Default to 0.0 so the row is not lost — I review 0.0 cost
            # items manually after import to assign the correct price.
            # --
            raw_price = item.get("price", 0.0)
            clean_price = round(float(raw_price), 2)

            # --
            # STOCK — cast to int
            # --
            # AliExpress occasionally sends stock as 10.0 not 10
            # which causes a SQLite type error on insert. int() fixes this.
            # --
            raw_stock = item.get("stock", 0)
            clean_stock = int(raw_stock)

            # Build the standardised output row
            structured_row = {
                "sku":      clean_sku,
                "name":     str(item.get("name", "Unnamed Product")).strip(),
                "category": str(item.get("category", "Uncategorized")).strip(),
                "cost_usd": clean_price,
                "stock":    clean_stock
            }

            cleaned_list.append(structured_row)

        except Exception as e:
            # Log the bad row and continue — do not let one bad row
            # stop the entire feed from processing
            print(f"  Row {index}: Skipped due to data error — {e}")
            skipped_count += 1
            continue

    # Summary so the calling script knows what came back
    print(f"Parser complete: {len(cleaned_list)} rows cleaned, {skipped_count} rows skipped")

    return cleaned_list
