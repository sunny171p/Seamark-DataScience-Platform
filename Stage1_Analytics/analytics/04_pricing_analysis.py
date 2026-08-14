# ==
# 04_pricing_analysis.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ==
#
# WHY I BUILT THIS:
# When I was reviewing products manually I spotted a few where
# the selling price was actually higher than the compare-at price
# which means the discount badge was showing incorrectly on the
# storefront. Customers would see a "sale" price that was not
# actually a discount — which is both misleading and bad for
# conversion. I needed to find all of these systematically
# across 8,078 products rather than checking one by one.
#
# SECONDARY PURPOSE:
# Understanding our price distribution by category helps with
# positioning decisions — are we priced competitively in the
# categories that matter most?
# ==

import pandas as pd
import matplotlib.pyplot as plt

# Load classified product data — requires 02_product_classification.py
# to have been run first so Auto_Category column exists
seamark_products = pd.read_csv('../cleaned_data/products_clean.csv')

print(f"Loaded {len(seamark_products)} products for pricing analysis")


# --
# BASIC PRICE DISTRIBUTION
# --
# Running describe() first to get a feel for the data before
# diving into specific issues — always good to see the range
# --

print("\n=== PRICE DISTRIBUTION ACROSS FULL CATALOGUE ===")
print(seamark_products['Variant Price'].describe().round(2))


# -
# AVERAGE PRICE BY CATEGORY
# --
# Sorted descending so the highest value categories appear first
# Photography and Electronics tend to sit at the top
# -

print("\n=== AVERAGE PRICE BY CATEGORY ===")
price_by_category = (
    seamark_products.groupby('Auto_Category')['Variant Price']
    .mean()
    .round(2)
    .sort_values(ascending=False)
)
print(price_by_category)


# ----
# PRICING ISSUE DETECTION
# ---
# A product has a pricing issue when:
# Variant Price > Variant Compare At Price
# This means the "was" price is lower than the current price
# which breaks the discount display on the storefront.
#
# Note: products with no compare-at price are excluded
# automatically because NaN comparisons return False
# ---

seamark_products['Pricing Issue'] = (
    seamark_products['Variant Price'] > seamark_products['Variant Compare At Price']
)

pricing_issues = seamark_products[seamark_products['Pricing Issue'] == True]

print(f"\n=== PRICING ISSUES DETECTED ===")
print(f"Products where selling price exceeds compare-at price: {len(pricing_issues)}")

if len(pricing_issues) > 0:
    print("\nTop 10 affected products:")
    print(pricing_issues[[
        'Title',
        'Variant Price',
        'Variant Compare At Price'
    ]].head(10).to_string())
    print("\nACTION NEEDED: These products need compare-at prices corrected in Shopify")
else:
    print("No pricing issues found — catalogue looks clean")


# ---
# VISUALISATION
# --
# Gold bars with dark green edges match the Seamark brand
# colours — emerald green and gold. Consistent across all
# charts in this project for a professional report look.
# -

fig, ax = plt.subplots(figsize=(12, 6))

price_by_category.plot(
    kind='bar',
    color='gold',
    edgecolor='darkgreen',
    ax=ax
)

ax.set_title('Average Product Price by Category — Seamark Global Innovations', fontsize=13)
ax.set_xlabel('Category')
ax.set_ylabel('Average Price (£)')

plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('../outputs/pricing_analysis.png')

print("\nChart saved to outputs/pricing_analysis.png")
print(f"Summary: {len(pricing_issues)} pricing issues found across {len(seamark_products)} products")
