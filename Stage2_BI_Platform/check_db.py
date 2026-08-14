import pandas as pd

df = pd.read_csv('raw_data/products_export.csv')

# Get unique products with prices
products = df[['Title', 'Variant Price']].dropna(subset=['Variant Price'])
products = products[products['Title'].notna()]
products = products.drop_duplicates(subset=['Title'])
products = products.sort_values('Variant Price')

print(f"Total products: {len(products)}")
print("\n=== PRODUCTS & PRICES ===")
print(products.head(30).to_string())
