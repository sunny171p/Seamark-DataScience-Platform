# ====
# 02_product_classification.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ===
#
# WHY I BUILT THIS:
# When I exported our products from Shopify, the "Type" column
# was mostly empty or inconsistent — vendors fill it in differently.
# I needed a reliable way to group 8,078 products into categories
# so I could analyse pricing and performance by product type.
#
# APPROACH:
# I tried using the existing Type column first but it had too many
# gaps and spelling variations. Keyword matching on the Title field
# turned out to be much more reliable for our catalogue.
# ====

import pandas as pd
import matplotlib.pyplot as plt

# Load the cleaned product data produced by 01_data_cleaning.py
seamark_products = pd.read_csv('../cleaned_data/products_clean.csv')

print(f"Loaded {len(seamark_products)} products for classification")


# --
# CLASSIFICATION FUNCTION
# --
# I built this keyword list manually by scrolling through about
# 200 product titles to find the most common patterns.
# It is not perfect — some edge cases fall into 'Other' —
# but it correctly classifies around 85-90% of the catalogue.
# I plan to improve this with a proper ML classifier later.
# -

def classify_product(title):
    title = str(title).lower()

    # TVs need to come first — 'smart' appears in other categories too
    if any(w in title for w in ['tv', 'television', 'smart tv']):
        return 'Smart TV'

    # Audio — earbuds and headphones are a big category for us
    elif any(w in title for w in ['headphone', 'earphone', 'earbud', 'airpod']):
        return 'Audio'

    # Footwear — discovered 'slipper' was missing in first version
    elif any(w in title for w in ['shoe', 'sneaker', 'slipper', 'boot']):
        return 'Footwear'

    # Apparel — had to add 'jean' separately as 'jeans' was not matching
    elif any(w in title for w in ['dress', 'top', 'blouse', 'skirt', 'trouser', 'jean', 'shirt', 'clothing']):
        return 'Apparel'

    # Kitchen — these are high margin products worth tracking separately
    elif any(w in title for w in ['fryer', 'toaster', 'blender', 'kettle', 'cooker']):
        return 'Kitchen Appliances'

    # Fitness — growing category based on recent order data
    elif any(w in title for w in ['fitness', 'gym', 'exercise', 'yoga', 'dumbbell', 'ab roller']):
        return 'Fitness'

    # Photography — smaller category but higher average price point
    elif any(w in title for w in ['camera', 'photo', 'tripod', 'lens']):
        return 'Photography'

    # Health & Beauty — shower filters kept appearing so added 'filter'
    elif any(w in title for w in ['shower', 'filter', 'bath']):
        return 'Health & Beauty'

    # Electronics — intentionally placed after specific categories
    # so phones/tablets do not get swallowed by a broad 'electronics' label
    elif any(w in title for w in ['phone', 'mobile', 'tablet', 'laptop', 'computer']):
        return 'Electronics'

    # Anything not matched — I review these manually each month
    else:
        return 'Other'


# Apply classification across all 8,078 product rows
seamark_products['Auto_Category'] = seamark_products['Title'].apply(classify_product)

print("\n=== AUTO-CLASSIFIED CATEGORIES ===")
print(seamark_products['Auto_Category'].value_counts())

# Check how many fell into 'Other' — if it is above 20% the keywords need updating
other_count = (seamark_products['Auto_Category'] == 'Other').sum()
print(f"\nUnclassified (Other): {other_count} products")


# --
# SAVE RESULTS
# ----

seamark_products.to_csv('../cleaned_data/products_clean.csv', index=False)
print("\nUpdated CSV saved to cleaned_data folder")


# ---
# VISUALISATION
# ---
# Bar chart saved to outputs folder for use in the dashboard
# and business reports. Green matches the Seamark brand colour.
# --

seamark_products['Auto_Category'].value_counts().plot(
    kind='bar',
    color='green',
    figsize=(10, 6)
)

plt.title('Seamark Product Categories — Auto Classification')
plt.xlabel('Category')
plt.ylabel('Number of Products')
plt.tight_layout()
plt.savefig('../outputs/product_categories.png')

print("Chart saved to outputs/product_categories.png")
