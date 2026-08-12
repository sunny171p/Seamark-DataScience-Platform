import pandas as pd

# The 30 sales orders for Seamark Global Innovations
# Date range: 28 July 2026 to 8 August 2026

sales_data = [
    {'order_id': 'SMK-001', 'sale_date': '2026-07-28', 'product_name': 'Men Sport T-shirt Quick Dry Bodybuilding', 'price': 11.99},
    {'order_id': 'SMK-002', 'sale_date': '2026-07-28', 'product_name': "Women's Clothing Autumn New Style Elegant", 'price': 16.99},
    {'order_id': 'SMK-003', 'sale_date': '2026-07-28', 'product_name': 'Red Light Therapy Eye Mask Rechargeable', 'price': 14.99},
    {'order_id': 'SMK-004', 'sale_date': '2026-07-28', 'product_name': 'Smart LED Strip Lights with Adhesive', 'price': 16.99},
    {'order_id': 'SMK-005', 'sale_date': '2026-07-29', 'product_name': '100% Cotton Breathable Short Sleeve T-Shirt', 'price': 12.99},
    {'order_id': 'SMK-006', 'sale_date': '2026-08-01', 'product_name': '100% Cotton Breathable Short Sleeve T-Shirt', 'price': 12.99},
    {'order_id': 'SMK-007', 'sale_date': '2026-08-01', 'product_name': 'Medieval Hooded Woollen Cloak Elf Halloween', 'price': 17.99},
    {'order_id': 'SMK-008', 'sale_date': '2026-08-01', 'product_name': 'LED Beauty Light Red Blue Light Device', 'price': 15.99},
    {'order_id': 'SMK-009', 'sale_date': '2026-08-01', 'product_name': 'Underwear Dress Women Striped Perspective', 'price': 7.99},
    {'order_id': 'SMK-010', 'sale_date': '2026-08-01', 'product_name': 'Red And Black Plaid Shirt Men Shirts', 'price': 12.99},
    {'order_id': 'SMK-011', 'sale_date': '2026-08-01', 'product_name': "Women's Clothing Autumn New Style Elegant", 'price': 16.99},
    {'order_id': 'SMK-012', 'sale_date': '2026-08-04', 'product_name': 'Mens Bodybuilding Sports Tight T-Shirt', 'price': 14.99},
    {'order_id': 'SMK-013', 'sale_date': '2026-08-04', 'product_name': 'Hawaii Shirts for Men 3D Paisley Graphic', 'price': 14.99},
    {'order_id': 'SMK-014', 'sale_date': '2026-08-04', 'product_name': 'LED Red Light Therapy Panel Lamp', 'price': 19.99},
    {'order_id': 'SMK-015', 'sale_date': '2026-08-04', 'product_name': "Women's Clothing 2025 Spring And Summer", 'price': 15.99},
    {'order_id': 'SMK-016', 'sale_date': '2026-08-04', 'product_name': 'Smart LED Strip Lights Music Sync RGB', 'price': 16.99},
    {'order_id': 'SMK-017', 'sale_date': '2026-08-06', 'product_name': 'Car Cordless Vacuum Cleaner Portable', 'price': 11.99},
    {'order_id': 'SMK-018', 'sale_date': '2026-08-06', 'product_name': "Women's High-Neck Colour Block Graffiti", 'price': 18.99},
    {'order_id': 'SMK-019', 'sale_date': '2026-08-08', 'product_name': 'Led Lights for Room Music Sync RGB', 'price': 19.99},
    {'order_id': 'SMK-020', 'sale_date': '2026-08-08', 'product_name': 'Hawaii Shirts for Men 3D Paisley Graphic', 'price': 14.99},
    {'order_id': 'SMK-021', 'sale_date': '2026-08-08', 'product_name': 'Led Lights for Room Music Sync RGB', 'price': 19.99},
    {'order_id': 'SMK-022', 'sale_date': '2026-08-08', 'product_name': 'Ladies Dress Autumn Women Hooded Dress', 'price': 17.99},
    {'order_id': 'SMK-023', 'sale_date': '2026-08-08', 'product_name': 'Car Cordless Vacuum Cleaner Portable', 'price': 11.99},
    {'order_id': 'SMK-024', 'sale_date': '2026-08-08', 'product_name': 'New Portable Juice Maker Blender', 'price': 19.99},
    {'order_id': 'SMK-025', 'sale_date': '2026-08-08', 'product_name': 'Portable Blender Bottle Electric 6 Blades', 'price': 19.99},
    {'order_id': 'SMK-026', 'sale_date': '2026-08-08', 'product_name': 'Portable Blender Bottle Electric 6 Blades', 'price': 19.99},
    {'order_id': 'SMK-027', 'sale_date': '2026-08-08', 'product_name': '2Pcs HEPA Replacement Filter Activated', 'price': 7.99},
    {'order_id': 'SMK-028', 'sale_date': '2026-08-08', 'product_name': 'Smart LED Strip Lights with Adhesive', 'price': 16.99},
    {'order_id': 'SMK-029', 'sale_date': '2026-08-08', 'product_name': '2-Pack Air Purifier Replacement Filter', 'price': 12.99},
    {'order_id': 'SMK-030', 'sale_date': '2026-08-08', 'product_name': 'Autumn Men Wide Loose Casual Pants', 'price': 16.99},
]

# Save to CSV
df = pd.DataFrame(sales_data)
df.to_csv('raw_data/sales_data.csv', index=False)

print("=" * 55)
print("  SEAMARK - SALES DATA FILE CREATED")
print("=" * 55)
print(f"  File saved  : raw_data/sales_data.csv")
print(f"  Total orders: {len(df)}")
print(f"  Total revenue: £{df['price'].sum():.2f}")
print(f"  Date range  : {df['sale_date'].min()} to {df['sale_date'].max()}")
print("=" * 55)
