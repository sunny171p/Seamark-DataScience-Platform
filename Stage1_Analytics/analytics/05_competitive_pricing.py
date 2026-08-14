# ===
# 05_competitive_pricing.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# =
#
# WHY I BUILT THIS:
# As a dropshipping and multi-vendor marketplace we do not
# manufacture products — so pricing is one of our main levers
# for competitiveness. I wanted to know whether we are priced
# above or below Amazon UK across our key categories.
#
# HOW I GOT THE BENCHMARKS:
# I manually checked Amazon UK prices for 3-5 representative
# products in each category during June 2026 and took the
# average. These are not live prices — they are a snapshot
# benchmark I plan to update quarterly.
#
# LIMITATIONS I AM AWARE OF:
# - Amazon prices change daily so this is a point-in-time view
# - Our product quality varies so direct comparison is not
#   always fair — a £15 dress vs a £35 dress are different things
# - I plan to automate this with a scraper or API in future
# ==

import pandas as pd
import matplotlib.pyplot as plt

# Load classified product data
seamark_products = pd.read_csv('../cleaned_data/products_clean.csv')

print(f"Loaded {len(seamark_products)} products for competitive analysis")


# ---
# AMAZON UK BENCHMARKS
# --
# Manually researched June 2026 — checked 3-5 products per
# category on Amazon UK and averaged the mid-range prices.
# Excluded obvious outliers (luxury items, bulk packs).
# --

amazon_benchmarks = {
    'Apparel': 25.00,
    'Footwear': 45.00,
    'Smart TV': 399.00,
    'Kitchen Appliances': 89.00,
    'Health & Beauty': 22.00,
    'Electronics': 55.00,
    'Fitness': 35.00,
    'Audio': 40.00,
    'Photography': 65.00,
    'Other': 30.00
}


# --
# PRICE COMPARISON
# --
# Calculating our average price per category and comparing
# directly against the Amazon benchmark for that category
# --

seamark_avg_by_category = (
    seamark_products.groupby('Auto_Category')['Variant Price']
    .mean()
    .round(2)
)

comparison = pd.DataFrame({
    'Seamark Avg Price (£)': seamark_avg_by_category,
    'Amazon Benchmark (£)': pd.Series(amazon_benchmarks)
})

comparison['Price Difference (£)'] = (
    comparison['Seamark Avg Price (£)'] - comparison['Amazon Benchmark (£)']
).round(2)

# Label positioning clearly for business reporting
comparison['vs Amazon'] = comparison['Price Difference (£)'].apply(
    lambda x: 'CHEAPER' if x < 0 else 'MORE EXPENSIVE'
)

# Percentage difference — more useful than raw £ difference
comparison['Difference %'] = (
    (comparison['Price Difference (£)'] / comparison['Amazon Benchmark (£)']) * 100
).round(1)

print("\n=== SEAMARK vs AMAZON UK PRICE POSITIONING ===")
print(comparison.to_string())

# Summary insight
cheaper_count = (comparison['vs Amazon'] == 'CHEAPER').sum()
expensive_count = (comparison['vs Amazon'] == 'MORE EXPENSIVE').sum()
print(f"\nCategories where we are cheaper than Amazon: {cheaper_count}")
print(f"Categories where we are more expensive than Amazon: {expensive_count}")
print("\nNote: Being more expensive is not always bad — depends on product quality and brand positioning")


# --
# VISUALISATION
# --
# Side by side bars make the comparison immediately obvious.
# Gold = Seamark, Steelblue = Amazon — consistent with brand.
# This chart goes into the monthly business review deck.
# -

fig, ax = plt.subplots(figsize=(12, 7))

x = range(len(comparison))
width = 0.35

ax.bar(
    [i - width / 2 for i in x],
    comparison['Seamark Avg Price (£)'],
    width,
    label='Seamark',
    color='gold',
    edgecolor='darkgreen'
)

ax.bar(
    [i + width / 2 for i in x],
    comparison['Amazon Benchmark (£)'],
    width,
    label='Amazon UK Benchmark (June 2026)',
    color='steelblue',
    edgecolor='navy'
)

ax.set_title('Seamark vs Amazon UK — Price Positioning by Category', fontsize=13)
ax.set_xlabel('Product Category')
ax.set_ylabel('Average Price (£)')
ax.set_xticks(list(x))
ax.set_xticklabels(comparison.index, rotation=45, ha='right')
ax.legend()

plt.tight_layout()
plt.savefig('../outputs/competitive_pricing.png')

print("\nChart saved to outputs/competitive_pricing.png")
print("Benchmarks should be refreshed quarterly to stay accurate")
