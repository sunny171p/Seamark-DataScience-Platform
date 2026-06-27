# ===
# 01_data_cleaning.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ===
#
# WHY I BUILT THIS:
# The raw Shopify product export is messy — it includes one row
# per variant which means a product with 5 sizes appears 5 times.
# Prices come through as strings not numbers, the Type column is
# mostly empty, and there are blank rows scattered throughout.
#
# This script is the foundation of the entire pipeline. Every
# other script depends on the cleaned CSV this produces, so
# getting this right was the first priority.
#
# WHAT THE RAW DATA LOOKED LIKE:
# - 8,078+ rows with duplicates and variant rows mixed in
# - Variant Price stored as text e.g. "29.99" not 29.99
# - Compare At Price missing for most products
# - Type column empty for roughly 70% of products
# - Some rows with no Title at all (Shopify export artefacts)
#
# DECISIONS I MADE:
# - Keep only rows with a valid Title (removes variant-only rows)
# - Fill missing Type with 'Unknown' rather than dropping rows
# - Convert prices to numeric and calculate Discount % myself
#   because Shopify does not export this directly
# ===

import pandas as pd

# Load raw exports from Shopify admin
# low_memory=False needed because price columns have mixed types
raw_products = pd.read_csv('raw_data/products_export.csv', low_memory=False)
raw_sessions = pd.read_csv('raw_data/sessions_by_month_365d.csv')

print(f"Raw product rows loaded: {len(raw_products)}")
print(f"Session months loaded: {len(raw_sessions)}")


# --
# STEP 1 — REMOVE INCOMPLETE ROWS
# --
# Rows without a Title are either blank rows or variant-only
# rows that Shopify includes in the export. Dropping these
# first before anything else to avoid skewing the analysis.
# -

products_clean = raw_products.dropna(subset=['Title'])
products_clean = products_clean[products_clean['Title'].str.strip() != '']

rows_removed = len(raw_products) - len(products_clean)
print(f"\nRows removed (no title): {rows_removed}")
print(f"Products remaining: {len(products_clean)}")


# --
# STEP 2 — KEEP ONLY RELEVANT COLUMNS
# --
# The raw Shopify export has 65+ columns — most are irrelevant
# for this analysis. Keeping only what I actually need keeps
# the file size small and the downstream scripts clean.
# --

useful_columns = [
    'Handle',
    'Title',
    'Vendor',
    'Type',
    'Tags',
    'Variant Price',
    'Variant Compare At Price',
    'Status'
]

products_clean = products_clean[useful_columns]


# --
# STEP 3 — FIX DATA TYPES AND FILL GAPS
# --
# Type column was empty for ~70% of products so filling with
# 'Unknown' rather than dropping — the classification script
# will assign proper categories using keyword matching anyway.
#
# Prices must be converted to numeric — they come through as
# strings from the Shopify CSV export which breaks any maths.
# errors='coerce' turns any non-numeric values into NaN safely.
# -

products_clean['Type'] = products_clean['Type'].fillna('Unknown')

products_clean['Variant Price'] = pd.to_numeric(
    products_clean['Variant Price'], errors='coerce'
)

products_clean['Variant Compare At Price'] = pd.to_numeric(
    products_clean['Variant Compare At Price'], errors='coerce'
)


# --
# STEP 4 — CALCULATE DISCOUNT PERCENTAGE
# --
# Shopify does not export discount % directly so calculating
# it here. Products with no compare-at price will show NaN
# which is correct — they are not on sale.
# --

products_clean['Discount %'] = (
    (products_clean['Variant Compare At Price'] - products_clean['Variant Price']) /
    products_clean['Variant Compare At Price'] * 100
).round(1)

discounted_count = products_clean['Discount %'].notna().sum()
print(f"\nProducts with a discount applied: {discounted_count}")


# --
# STEP 5 — SAVE CLEANED DATA
# --

products_clean.to_csv('cleaned_data/products_clean.csv', index=False)

print("\n=== CLEANING COMPLETE ===")
print(f"Final dataset shape: {products_clean.shape}")
print(f"\nProduct Types:\n{products_clean['Type'].value_counts()}")
print(f"\nTop 10 Vendors:\n{products_clean['Vendor'].value_counts().head(10)}")
print(f"\nDiscount % Summary:\n{products_clean['Discount %'].describe().round(2)}")
print("\nCleaned data saved to cleaned_data/products_clean.csv")
print("Ready for 02_product_classification.py")
