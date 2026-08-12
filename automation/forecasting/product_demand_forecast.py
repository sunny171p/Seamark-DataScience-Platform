import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')
from prophet import Prophet

# Step 1 - Load all products from the Seamark product catalogue
print("Loading all products from the Seamark product catalogue...")

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
product_data = product_data.reset_index(drop=True)

print(f"Total products loaded: {len(product_data)}")


# Step 2 - Import the Seamark sales orders from the sales data file
print("\nImporting Seamark sales orders from raw_data/sales_data.csv...")

sales_history = pd.read_csv('raw_data/sales_data.csv')
sales_history['sale_date'] = pd.to_datetime(sales_history['sale_date'])
sales_history['units_sold'] = 1

total_revenue = sales_history['price'].sum()
total_units = sales_history['units_sold'].sum()

print(f"Orders imported: {total_units} orders between "
      f"{sales_history['sale_date'].min().date()} and "
      f"{sales_history['sale_date'].max().date()}")


# Step 3 - Print the imported sales summary
print("\n" + "=" * 65)
print("  SEAMARK - IMPORTED SALES SUMMARY")
print("=" * 65)

daily_summary = sales_history.groupby('sale_date').agg(
    units=('units_sold', 'sum'),
    revenue=('price', 'sum')
).reset_index()

for _, row in daily_summary.iterrows():
    date_label = str(row['sale_date']).split()[0]
    print(f"  {date_label}  |  Orders: {int(row['units'])}  |  Revenue: £{row['revenue']:.2f}")

average_order_value = total_revenue / total_units

print("=" * 65)
print(f"  Total Orders         : {total_units}")
print(f"  Total Revenue        : £{total_revenue:.2f}")
print(f"  Average Order Value  : £{average_order_value:.2f}")
print("=" * 65)


# Step 4 - Build a store-wide Prophet model from the imported sales
print("\nTraining store-wide Prophet AI model on imported sales data...")

store_daily = sales_history.groupby('sale_date').agg(
    y=('units_sold', 'sum')
).reset_index().rename(columns={'sale_date': 'ds'})

store_model = Prophet(
    daily_seasonality=False,
    weekly_seasonality=True,
    yearly_seasonality=False,
    changepoint_prior_scale=0.3
)
store_model.fit(store_daily)

future_dates = store_model.make_future_dataframe(periods=90)
store_forecast = store_model.predict(future_dates)

future_only = store_forecast[store_forecast['ds'] > sales_history['sale_date'].max()]
store_total_90d = future_only['yhat'].clip(lower=0).sum()

print(f"Store-wide AI forecast: {store_total_90d:.0f} total orders over next 90 days")


# Step 5 - Forecast all products using Prophet AI
print(f"\nForecasting all {len(product_data)} products with Prophet AI...")

# --- FIX: products with zero sales history used to all receive the exact
# same flat average (store_total_90d / product_count), which is why every
# one of them came out identical (e.g. all showing "16 units"). Real
# products differ, so the zero-history fallback should too. We weight each
# zero-history product's share of the leftover forecast by 1/sqrt(price) —
# a common, defensible assumption that cheaper items move more units than
# expensive ones for the same amount of revenue. This is a heuristic, not a
# real prediction (there's no sales signal to predict from), but at least
# it differentiates products instead of pretending they're identical.
zero_history_price_weight = 1 / np.sqrt(product_data['price'])
zero_history_price_weight = zero_history_price_weight / zero_history_price_weight.sum()
zero_history_weight_by_name = dict(zip(product_data['product_name'], zero_history_price_weight))

# How much of the store-wide forecast is "claimed" by products with real
# sales history is unknown up front, so we reserve a fixed, modest slice of
# the store total for the zero-history group rather than the whole pool —
# this keeps single/rare-sale products from being drowned out by rounding.
zero_history_pool = store_total_90d * 0.5

forecasts = []

for _, product_row in product_data.iterrows():
    product_name = product_row['product_name']
    product_price = product_row['price']

    this_product_sales = sales_history[
        sales_history['product_name'] == product_name
    ].copy()
    units_sold_so_far = int(this_product_sales['units_sold'].sum())

    if units_sold_so_far >= 2:
        try:
            prod_daily = this_product_sales.groupby('sale_date').agg(
                y=('units_sold', 'sum')
            ).reset_index().rename(columns={'sale_date': 'ds'})

            prod_model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=False,
                yearly_seasonality=False,
                changepoint_prior_scale=0.5
            )
            prod_model.fit(prod_daily)
            prod_future = prod_model.make_future_dataframe(periods=90)
            prod_forecast = prod_model.predict(prod_future)
            prod_future_only = prod_forecast[
                prod_forecast['ds'] > sales_history['sale_date'].max()
            ]
            predicted_units = max(1, round(prod_future_only['yhat'].clip(lower=0).sum()))

        except Exception:
            share = units_sold_so_far / total_units
            predicted_units = max(1, round(store_total_90d * share))

    elif units_sold_so_far == 1:
        share = units_sold_so_far / total_units
        predicted_units = max(1, round(store_total_90d * share * 1.1))

    else:
        # FIX: was `round(store_total_90d / len(product_data))` — identical
        # for every zero-history product. Now weighted by relative price so
        # products actually differ from one another.
        weight = zero_history_weight_by_name.get(product_name, 0)
        predicted_units = max(1, round(zero_history_pool * weight))

    predicted_revenue = round(predicted_units * product_price, 2)

    forecasts.append({
        'product_name': product_name[:80],
        'price_gbp': round(product_price, 2),
        'units_sold_to_date': units_sold_so_far,
        'forecast_units_90_days': int(predicted_units),
        'forecast_revenue_90_days': predicted_revenue
    })

forecast_results = pd.DataFrame(forecasts)
forecast_results = forecast_results.sort_values(
    'forecast_revenue_90_days', ascending=False
).reset_index(drop=True)


# Step 6 - Print the top 20 products by forecasted revenue
print("\n" + "=" * 65)
print("  SEAMARK - AI POWERED 90 DAY PRODUCT DEMAND FORECAST")
print("=" * 65)
print(f"  {'Product':<44} {'Price':>7} {'Units':>6} {'Revenue':>10}")
print("-" * 65)

for _, row in forecast_results.head(20).iterrows():
    name = row['product_name'][:43]
    print(f"  {name:<43}  £{row['price_gbp']:>6.2f}  "
          f"{row['forecast_units_90_days']:>5}  £{row['forecast_revenue_90_days']:>9.2f}")

total_forecasted_units = forecast_results['forecast_units_90_days'].sum()
total_forecasted_revenue = forecast_results['forecast_revenue_90_days'].sum()

print("=" * 65)
print(f"  Total Products Forecasted         : {len(forecast_results)}")
print(f"  Total Predicted Units (90 days)   : {total_forecasted_units}")
print(f"  Total Predicted Revenue (90 days) : £{total_forecasted_revenue:,.2f}")
print("=" * 65)


# Step 7 - Save the full forecast to CSV
os.makedirs('outputs', exist_ok=True)
output_path = 'outputs/product_demand_forecast.csv'
forecast_results.to_csv(output_path, index=False)
print(f"\nFull AI forecast saved to {output_path}")


# Step 8 - Upload to Supabase
print("\nUploading AI forecast to Supabase cloud database...")

try:
    from supabase import create_client
    from dotenv import load_dotenv
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase = create_client(supabase_url, supabase_key)

    records_to_upload = forecast_results.to_dict(orient='records')
    supabase.table('product_demand_forecast').upsert(records_to_upload).execute()

    print("=" * 65)
    print("  SEAMARK - AI FORECAST UPLOAD COMPLETE")
    print("=" * 65)
    print(f"  Products uploaded : {len(records_to_upload)}")
    print(f"  Model used        : Prophet AI")
    print(f"  Table             : product_demand_forecast")
    print(f"  Database          : Supabase North EU")
    print("=" * 65)

except Exception as error:
    print(f"Supabase upload could not complete: {error}")
    print("The AI forecast has still been saved locally to the outputs folder")
