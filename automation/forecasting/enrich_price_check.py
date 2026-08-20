import pandas as pd
import numpy as np

print("Loading products export...")
df = pd.read_csv('raw_data/products_export.csv')

# Keep only the columns we need
cols = ['Title', 'Type', 'Product Category', 'Variant Price',
        'Variant Compare At Price', 'Cost per item', 'Status']
df = df[cols].copy()

# Clean numeric columns
df['Variant Price'] = pd.to_numeric(df['Variant Price'], errors='coerce')
df['Variant Compare At Price'] = pd.to_numeric(df['Variant Compare At Price'], errors='coerce')
df['Cost per item'] = pd.to_numeric(df['Cost per item'], errors='coerce')

# Drop rows with no price
df = df.dropna(subset=['Variant Price'])
df = df[df['Variant Price'] > 0]
df = df.drop_duplicates(subset=['Title'])
df = df.reset_index(drop=True)

# Calculate fields
df['Price Difference'] = (df['Variant Compare At Price'] - df['Variant Price']).round(2)
df['Discount %'] = ((df['Price Difference'] / df['Variant Compare At Price']) * 100).round(1)
df['Profit Margin'] = (df['Variant Price'] - df['Cost per item']).round(2)

# Assign pricing status
def get_status(row):
    if pd.isna(row['Variant Compare At Price']) or row['Variant Compare At Price'] == 0:
        return 'No Discount'
    elif row['Variant Price'] > row['Variant Compare At Price']:
        return 'Misleading Discount'
    elif row['Discount %'] > 50:
        return 'High Discount'
    elif row['Discount %'] > 0:
        return 'OK'
    else:
        return 'No Discount'

df['Pricing Status'] = df.apply(get_status, axis=1)

# Clean category
df['Category'] = df['Type'].fillna(
    df['Product Category'].fillna('Uncategorised')
).str.strip()
df['Category'] = df['Category'].replace('', 'Uncategorised')

# Final columns
result = df[[
    'Title', 'Category', 'Variant Price', 'Variant Compare At Price',
    'Cost per item', 'Price Difference', 'Discount %',
    'Profit Margin', 'Pricing Status', 'Status'
]].rename(columns={
    'Variant Price': 'Price',
    'Variant Compare At Price': 'Compare At Price',
    'Cost per item': 'Cost',
    'Status': 'Product Status'
})

# Save
result.to_csv('outputs/price_check_enriched.csv', index=False)

# Summary
print("\n" + "=" * 60)
print("  SEAMARK — ENRICHED PRICE CHECK COMPLETE")
print("=" * 60)
print(f"  Total products     : {len(result)}")
print(f"  No Discount        : {len(result[result['Pricing Status'] == 'No Discount'])}")
print(f"  OK (discounted)    : {len(result[result['Pricing Status'] == 'OK'])}")
print(f"  High Discount      : {len(result[result['Pricing Status'] == 'High Discount'])}")
print(f"  Misleading Discount: {len(result[result['Pricing Status'] == 'Misleading Discount'])}")
print(f"  Saved to           : outputs/price_check_enriched.csv")
print("=" * 60)
