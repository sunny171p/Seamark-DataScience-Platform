# ============================================================
# SEAMARK GLOBAL INNOVATIONS
# AI Sales Forecasting Model — Next 90 Days
# Tool: Facebook Prophet (AI Prediction Engine)
# Currency: GBP (£)
# ============================================================

import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import os

# Step 1: Load the sales history file
print("Loading Seamark sales data...")
my_orders = pd.read_csv('Stage1_Analytics/data/orders_export.csv')


# Step 2: Rename columns so Prophet understands them
my_orders = my_orders.rename(columns={
    'Order Date':  'ds',
    'Total (GBP)': 'y'
})

# Step 3: Make sure dates are in the correct format
my_orders['ds'] = pd.to_datetime(my_orders['ds'])

# Step 4: Remove any empty rows
my_orders = my_orders[['ds', 'y']].dropna()

# Step 5: Add up all sales per day
sales_per_day = my_orders.groupby('ds')['y'].sum().reset_index()

print(f"  Data loaded: {len(sales_per_day)} orders found")
print(f"  Training the AI model — please wait...")

# Step 5b: Fill in the quiet days between orders as £0
#
# == FIXED (September 2026) ==
# sales_per_day above only has the 11 days that actually had an order —
# Prophet never saw the 126 quiet days in between, so it trained on
# "average revenue on a day with an order" (£33.77) instead of "average
# daily revenue" (£2.71 across the real 137-day span). That mismatch is
# what caused this script's first real run to forecast £44-60/day for the
# next 90 days — 16-22x too high — and is also why the fitted line jumped
# from ~£34/day to a small manually-capped number right at the forecast
# cutoff, instead of being one continuous, honest line.
#
# Reindexing to every calendar day (filling gaps with £0) fixes this at
# the source: Prophet now trains on what actually happened, quiet days
# included, so its own flat/noise estimate lands close to the real £2.71
# /day run-rate without needing to be overridden afterward. The original
# order-only sales_per_day is kept for the chart's scatter dots below, so
# the chart still only marks the days something was actually sold.
daily_series = (
    sales_per_day.set_index('ds')
    .reindex(pd.date_range(sales_per_day['ds'].min(), sales_per_day['ds'].max(), freq='D'), fill_value=0)
    .rename_axis('ds')
    .reset_index()
)

# Step 6: Build and train the AI forecasting model
#
# growth='flat' also added: even with the quiet days filled in, 11 real
# data points out of 137 is still thin, and flat growth stops Prophet's
# automatic trend-changepoints from locking onto a small wiggle and
# extrapolating it into a runaway trend (documented Prophet setting,
# Prophet >= 1.1) — it models the series as its own flat average plus
# noise instead, which matches this data's actual shape far better than a
# fitted trend line would.
prediction_model = Prophet(
    growth='flat',
    yearly_seasonality=False,
    weekly_seasonality=False,
    daily_seasonality=False
)
prediction_model.fit(daily_series)

# Step 7: Predict the next 90 days
next_90_days = prediction_model.make_future_dataframe(periods=90)
my_forecast = prediction_model.predict(next_90_days)

# Belt-and-suspenders sanity guard, same principle as
# automation/forecasting/product_demand_forecast.py's Step 2: even with
# growth='flat', don't blindly trust the output on 11 sparse data points.
# Compare it to the simplest possible honest estimate — the real historical
# average rate spread over 90 days — and fall back to that flat, clearly
# non-fabricated number if Prophet's forecast is still wildly off from it.
_history_span_days = (my_orders['ds'].max() - my_orders['ds'].min()).days or 1
_naive_daily_avg = my_orders['y'].sum() / _history_span_days
_naive_90d_total = _naive_daily_avg * 90
_future_mask = my_forecast['ds'] > my_orders['ds'].max()
_predicted_90d_total = my_forecast.loc[_future_mask, 'yhat'].sum()

if _predicted_90d_total < 0 or _predicted_90d_total > _naive_90d_total * 2.5:
    print(f"  WARNING: Prophet's forecast (£{_predicted_90d_total:,.2f} over 90 days) is not")
    print(f"  credible against the historical run-rate (~£{_naive_90d_total:,.2f} for 90 days).")
    print(f"  Replacing the future portion of the forecast with a flat run-rate projection.")
    my_forecast.loc[_future_mask, 'yhat'] = _naive_daily_avg
    my_forecast.loc[_future_mask, 'yhat_lower'] = 0.0
    my_forecast.loc[_future_mask, 'yhat_upper'] = _naive_daily_avg * 2

# Step 8: Save forecast to CSV
os.makedirs('outputs', exist_ok=True)
my_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(
    'outputs/sales_forecast_90days.csv', index=False
)

# Step 9: Draw a professional branded chart
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 7))

# Background colour
fig.patch.set_facecolor('#F8F9FA')
ax.set_facecolor('#FFFFFF')

# Split historical data and forecast
historical = my_forecast[my_forecast['ds'] <= '2026-08-10']
future = my_forecast[my_forecast['ds'] > '2026-08-10']

# Draw the confidence zone (light blue shading)
ax.fill_between(my_forecast['ds'],
                my_forecast['yhat_lower'],
                my_forecast['yhat_upper'],
                color='#AED6F1', alpha=0.4, label='Forecast Range (Best/Worst Case)')

# Draw the forecast trend line
ax.plot(my_forecast['ds'], my_forecast['yhat'],
        color='#1A5276', linewidth=2.5, label='Predicted Revenue Trend')

# Draw the actual sales dots
ax.scatter(sales_per_day['ds'], sales_per_day['y'],
           color='#E74C3C', s=60, zorder=5, label='Actual Orders (Mar–Aug 2026)')

# Add a vertical line showing where forecast begins
ax.axvline(x=pd.Timestamp('2026-08-10'),
           color='#E67E22', linestyle='--', linewidth=1.5, label='Forecast Starts Here')

# Labels and title
ax.set_title('Seamark Global Innovations\n90-Day Sales Revenue Forecast',
             fontsize=16, fontweight='bold', color='#1A252F', pad=20)
ax.set_xlabel('Date', fontsize=12, color='#555555')
ax.set_ylabel('Predicted Revenue (£)', fontsize=12, color='#555555')

# Grid styling
ax.grid(True, linestyle='--', alpha=0.5, color='#CCCCCC')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Legend
ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

# Footer branding
fig.text(0.99, 0.01,
         'Seamark Global Innovations | theseamarkglobalinnovations.com | Confidential',
         ha='right', fontsize=8, color='#AAAAAA')

plt.tight_layout()
plt.savefig('outputs/sales_forecast_chart.png', dpi=150, bbox_inches='tight')
plt.show()


# Step 10: Print summary
forecast_only = my_forecast[my_forecast['ds'] > '2026-08-10']
print("=" * 55)
print("  SEAMARK — 90-DAY FORECAST COMPLETE")
print("=" * 55)
print(f"  Forecast period  : Aug — Nov 2026")
print(f"  Predicted revenue: £{forecast_only['yhat'].sum():,.2f}")
print(f"  Chart saved to   : outputs/sales_forecast_chart.png")
print(f"  Data saved to    : outputs/sales_forecast_90days.csv")
print("=" * 55)

# --
# Step 11 — UPLOAD TO SUPABASE (added September 2026)
# --
# This script used to only save locally. Sunday asked for this forecast to
# go to Supabase too, same as automation/forecasting/product_demand_forecast.py
# already does for the store-wide monthly forecast. Same snapshot pattern:
# clear the table, then insert the current run — no history pile-up.
#
# BEFORE RUNNING THIS: run supabase_sales_forecast.sql once in the Supabase
# SQL editor (creates a clean sales_forecast table with the exact columns
# this insert expects — see that file for why a fresh create is used
# instead of assuming an existing table's shape).
print("\nUploading daily forecast to Supabase cloud database...")
try:
    from supabase import create_client
    from dotenv import load_dotenv
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase = create_client(supabase_url, supabase_key)

    upload_rows = my_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    upload_rows['ds'] = upload_rows['ds'].dt.strftime('%Y-%m-%d')
    upload_rows = upload_rows.round(2)

    # FIXED (September 2026): this used to filter on
    # .neq('ds', '__none__') to delete every row — but ds is a `date`
    # column, and '__none__' isn't a valid date, so Postgres rejected the
    # whole delete before it ever ran. That silently failed and got
    # swallowed by this block's own except below, which is why nothing
    # ever reached Supabase even though the connection itself was fine.
    # id is an integer, so comparing it to -1 (a value no real row will
    # ever have) is always true and safely clears the table — same
    # pattern already proven working in product_demand_forecast.py.
    supabase.table('sales_forecast').delete().neq('id', -1).execute()
    supabase.table('sales_forecast').insert(upload_rows.to_dict(orient='records')).execute()

    print("=" * 55)
    print("  SEAMARK — SUPABASE UPLOAD COMPLETE")
    print(f"  Table    : sales_forecast")
    print(f"  Rows     : {len(upload_rows)} (full history + 90-day forecast)")
    print("=" * 55)
except Exception as error:
    print(f"Supabase upload could not complete: {error}")
    print("The forecast has still been saved locally to outputs/sales_forecast_90days.csv")
