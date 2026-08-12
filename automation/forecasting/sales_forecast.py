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
my_orders = pd.read_csv('data/orders_export.csv')


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

# Step 6: Build and train the AI forecasting model
prediction_model = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=False,
    daily_seasonality=False
)
prediction_model.fit(sales_per_day)

# Step 7: Predict the next 90 days
next_90_days = prediction_model.make_future_dataframe(periods=90)
my_forecast = prediction_model.predict(next_90_days)

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
