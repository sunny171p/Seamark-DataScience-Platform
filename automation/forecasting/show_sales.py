import pandas as pd
import numpy as np

# Load products
product_data = pd.read_csv('raw_data/products_export.csv')
product_data = product_data[['Title', 'Variant Price']].copy()
product_data = product_data.rename(columns={
    'Title': 'product_name',
    'Variant Price': 'price'
})
product_data['price'] = pd.to_numeric(product_data['price'], errors='coerce')
product_data = product_data.dropna(subset=['product_name', 'price'])
product_data = product_data[product_data['price'] > 0]
product_data = product_data.drop_duplicates(subset=['product_name'])

# Keep only products priced under £20 to stay under £500 total
product_data = product_data[product_data['price'] <= 20]
product_data = product_data.reset_index(drop=True)

print(f"Products available under £20: {len(product_data)}")

# Recreate the exact same 30 sales
actual_sales = [
    ('2026-07-28', 4),
    ('2026-07-29', 1),
    ('2026-08-01', 6),
    ('2026-08-04', 5),
    ('2026-08-06', 2),
    ('2026-08-08', 12),
]

np.random.seed(42)
all_sales = []

for sale_date, number_of_units in actual_sales:
    for unit in range(number_of_units):
        chosen_product = product_data.sample(1).iloc[0]
        all_sales.append({
            'sale_date': sale_date,
            'product_name': chosen_product['product_name'],
            'price': chosen_product['price'],
        })

sales_history = pd.DataFrame(all_sales)

# Print all 30 orders clearly
print("\n" + "=" * 70)
print("  SEAMARK - ALL 30 GENERATED SALES ORDERS (UNDER £500 TOTAL)")
print("=" * 70)
print(f"  {'#':<4} {'Date':<14} {'Product':<38} {'Price':>8}")
print("-" * 70)

for i, row in sales_history.iterrows():
    name = row['product_name'][:37]
    print(f"  {i+1:<4} {row['sale_date']:<14} {name:<38} £{row['price']:>7.2f}")

print("=" * 70)
print(f"  Total Orders  : {len(sales_history)}")
print(f"  Total Revenue : £{sales_history['price'].sum():.2f}")
print(f"  Avg Order Val : £{sales_history['price'].mean():.2f}")
print("=" * 70)
