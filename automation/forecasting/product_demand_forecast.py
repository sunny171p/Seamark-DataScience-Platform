# ==
# REWRITTEN (Claude, September 2026) — read this before re-running
# ==
#
# WHAT CHANGED AND WHY:
# This script used to forecast per-product demand from
# Stage1_Analytics/raw_data/sales_data.csv, which used to have one row
# per sale with real product_name/price/sale_date columns. That file has
# since been edited (by Sunday) to 11 monthly totals instead — columns
# are now `Created at`, `Lineitem price`, `Lineitem quantity`, with NO
# product name anywhere in it. There is no per-product signal left in
# this file to forecast from.
#
# Rather than keep the old per-product code and feed it a file it can no
# longer honestly support — which would mean either crashing on the
# missing columns, or silently reinventing a per-product split with no
# real basis (exactly the kind of fabricated precision this whole
# project's other scripts go out of their way to avoid, see
# 02_product_classification.py's clustering-not-behavioural-segmentation
# choice and Project 2's forecast API for the same principle) — this
# script now forecasts what the data actually supports: a STORE-WIDE
# 90-day revenue and units forecast from the real monthly totals.
#
# WHAT THIS MEANS FOR THE DASHBOARD:
# seamark_dashboard.py currently reads the OLD `product_demand_forecast`
# Supabase table for three per-product sections (a top-10-products table
# and two charts). That table's rows are from before sales_data.csv was
# edited down to monthly totals — Sunday confirmed that old data is from
# a previous, buggy run and should be cleared, not kept around looking
# authoritative. So this script now does two things on every run: it
# clears every row out of the old `product_demand_forecast` table (empty,
# not deleted — the table itself still exists), and it writes the real
# store-wide forecast to a new table, `store_demand_forecast`. The three
# dashboard sections that read the old table will show empty/zero once
# this runs, which is the honest state until either real per-product sales
# data exists again or the dashboard is updated to read the new store-wide
# table instead — ask for that dashboard update explicitly if you want it.
#
# The delete step also re-checks the table afterward and prints how many
# rows are actually left (should be 0) rather than assuming the delete
# worked — Sunday asked for the old data to be fully removed, not just
# mostly removed.
#
# BEFORE RUNNING THIS:
#   1. Run supabase_store_demand_forecast.sql once in the Supabase SQL
#      editor (creates the store_demand_forecast table).
#   2. pip install prophet python-dotenv supabase pandas  (already in
#      requirements.txt / your .venv if the rest of this project runs)
#
# HOW TO RUN:
#   python automation/forecasting/product_demand_forecast.py
#   (from the project root — same as before)
# ==

import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
from prophet import Prophet

# --
# STEP 1 — LOAD THE REAL MONTHLY SALES TOTALS
# --

print("Loading Seamark monthly sales totals...")
sales_history = pd.read_csv('Stage1_Analytics/raw_data/sales_data.csv')
sales_history['ds'] = pd.to_datetime(sales_history['Created at'])
sales_history = sales_history.sort_values('ds').reset_index(drop=True)

total_revenue = sales_history['Lineitem price'].sum()
total_units = sales_history['Lineitem quantity'].sum()

print("\n" + "=" * 65)
print("  SEAMARK - IMPORTED MONTHLY SALES SUMMARY")
print("=" * 65)
for _, row in sales_history.iterrows():
    print(f"  {row['ds'].date()}  |  Units: {int(row['Lineitem quantity']):>3}  |  "
          f"Revenue: £{row['Lineitem price']:.2f}")
print("=" * 65)
print(f"  Months of history    : {len(sales_history)}")
print(f"  Total units          : {int(total_units)}")
print(f"  Total revenue        : £{total_revenue:.2f}")
print("=" * 65)


# --
# STEP 2 — STORE-WIDE PROPHET FORECAST (REVENUE + UNITS)
# --
# 11 monthly points is thin for Prophet — and the first real run of this
# script (15 Sep 2026) proved it: Prophet's default trend has automatic
# "changepoints" that let it bend the trend line partway through the
# series, and with only 11 points it locked onto a late uptick and
# extrapolated it into a 90-day revenue forecast of £123,512 — about 33x
# the actual monthly average (£1,244/month) — while units came out at
# 1,021 against a real monthly average of ~10. That's not "a wide
# confidence interval", it's a wrong number, and this project's whole
# point is not shipping fabricated precision.
#
# FIX: growth='flat' turns off trend-fitting entirely — Prophet then
# models the series as a stationary level plus noise (no changepoints to
# run away with), which matches what the real data actually looks like:
# noisy but flat around its own average, not a runaway climb. This is a
# real, documented Prophet setting (Prophet >= 1.1), not a workaround.
#
# BELT AND SUSPENDERS: even with growth='flat', the result is still
# checked against a naive projection (recent monthly average x 3) before
# being trusted. If it's ever more than 2.5x that naive number, or
# negative, this script falls back to the naive number itself and labels
# the row as a fallback rather than silently publishing whatever Prophet
# produced. The dashboard/consumer should still treat this as a
# store-wide trend estimate, not a precise prediction.
# --

print("\nTraining store-wide Prophet AI model on monthly revenue...")
revenue_model = Prophet(
    growth='flat',
    daily_seasonality=False,
    weekly_seasonality=False,
    yearly_seasonality=False,
)
revenue_model.fit(sales_history[['ds', 'Lineitem price']].rename(columns={'Lineitem price': 'y'}))
revenue_future = revenue_model.make_future_dataframe(periods=90)
revenue_forecast = revenue_model.predict(revenue_future)
revenue_future_only = revenue_forecast[revenue_forecast['ds'] > sales_history['ds'].max()]

print("Training store-wide Prophet AI model on monthly units...")
units_model = Prophet(
    growth='flat',
    daily_seasonality=False,
    weekly_seasonality=False,
    yearly_seasonality=False,
)
units_model.fit(sales_history[['ds', 'Lineitem quantity']].rename(columns={'Lineitem quantity': 'y'}))
units_future = units_model.make_future_dataframe(periods=90)
units_forecast = units_model.predict(units_future)
units_future_only = units_forecast[units_forecast['ds'] > sales_history['ds'].max()]

predicted_revenue_90d = round(revenue_future_only['yhat'].clip(lower=0).sum(), 2)
predicted_units_90d = round(units_future_only['yhat'].clip(lower=0).sum(), 0)

# --
# Sanity guard — described above. "months_of_history" months averaging
# to total_revenue/total_units gives a simple run-rate; 90 days is
# treated as 3 months of that run-rate for this comparison.
# --
naive_90d_revenue = round((total_revenue / len(sales_history)) * 3, 2)
naive_90d_units = round((total_units / len(sales_history)) * 3, 0)

forecast_note = None
if predicted_revenue_90d < 0 or predicted_revenue_90d > naive_90d_revenue * 2.5:
    print(f"\n  WARNING: Prophet's revenue forecast (£{predicted_revenue_90d:,.2f}) is not")
    print(f"  credible against the recent run-rate (~£{naive_90d_revenue:,.2f} for 90 days).")
    print(f"  Falling back to the run-rate-based estimate instead of publishing it.")
    predicted_revenue_90d = naive_90d_revenue
    forecast_note = 'revenue'

if predicted_units_90d < 0 or predicted_units_90d > naive_90d_units * 2.5:
    print(f"\n  WARNING: Prophet's units forecast ({predicted_units_90d:.0f}) is not")
    print(f"  credible against the recent run-rate (~{naive_90d_units:.0f} for 90 days).")
    print(f"  Falling back to the run-rate-based estimate instead of publishing it.")
    predicted_units_90d = naive_90d_units
    forecast_note = 'units' if forecast_note is None else 'revenue and units'

print("\n" + "=" * 65)
print("  SEAMARK - STORE-WIDE 90-DAY AI FORECAST")
print("=" * 65)
print(f"  Predicted units (90 days)   : {predicted_units_90d:.0f}")
print(f"  Predicted revenue (90 days) : £{predicted_revenue_90d:,.2f}")
if forecast_note:
    print(f"  NOTE: {forecast_note} used the run-rate fallback, not Prophet's raw output.")
print("=" * 65)
print("  This is a STORE-WIDE forecast, not per-product — see this file's")
print("  header comment for why the old per-product breakdown was retired.")
print("=" * 65)


# --
# STEP 3 — SAVE LOCALLY
# --

os.makedirs('outputs', exist_ok=True)
forecast_row = pd.DataFrame([{
    'forecast_generated_at': pd.Timestamp.now().isoformat(timespec='seconds'),
    'months_of_history': len(sales_history),
    'total_revenue_to_date_gbp': round(total_revenue, 2),
    'total_units_to_date': int(total_units),
    'predicted_revenue_90_days_gbp': predicted_revenue_90d,
    'predicted_units_90_days': int(predicted_units_90d),
    'scope': 'store-wide, NOT per-product',
    'why_not_per_product': (
        "Stage1_Analytics/raw_data/sales_data.csv has 11 monthly totals with "
        "no product_name column — there is no per-product signal to forecast "
        "from. See this script's header comment."
        + (
            f" ALSO: Prophet's raw {forecast_note} forecast was not credible "
            "against the recent run-rate and was replaced with a simple "
            "average-based estimate — see the Step 2 comment in this script."
            if forecast_note else ""
        )
    ),
}])
output_path = 'outputs/store_demand_forecast.csv'
forecast_row.to_csv(output_path, index=False)
print(f"\nSaved to {output_path}")


# --
# STEP 4 — UPLOAD TO SUPABASE (new table, doesn't touch the old one)
# --

print("\nUploading store-wide forecast to Supabase cloud database...")

try:
    from supabase import create_client
    from dotenv import load_dotenv
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase = create_client(supabase_url, supabase_key)

    # --
    # 4a — Clear the old per-product table, IF it still exists.
    # --
    # Sunday confirmed these rows are the OLD project 1 (a previous, buggy
    # run) and should be fully removed rather than sit next to the new
    # store-wide numbers. Originally this just emptied the table's rows
    # (keeping the table itself so the dashboard's query wouldn't error).
    # Sunday has since deleted the whole table directly in Supabase, which
    # is a more thorough version of the same request — so a "table not
    # found" error here means the job's already done, not a failure.
    #
    # This whole step is isolated in its own try/except so that whatever
    # happens to the old table can NEVER block Step 4b from running. That
    # used to not be true: the first time Sunday dropped this table instead
    # of just clearing it, this script hit the error here and skipped the
    # new store_demand_forecast upload entirely, even though the error had
    # nothing to do with the new table.
    old_row_count = 0
    remaining_count = 0
    old_table_existed = True
    try:
        old_rows = supabase.table('product_demand_forecast').select('*').execute().data
        old_row_count = len(old_rows) if old_rows else 0
        if old_row_count:
            # Two delete calls, not one: Postgres treats a NULL product_name
            # as neither equal nor not-equal to '__none__', so a plain
            # .neq() alone can silently leave NULL-named rows behind.
            supabase.table('product_demand_forecast').delete().neq('product_name', '__none__').execute()
            supabase.table('product_demand_forecast').delete().is_('product_name', 'null').execute()
        remaining = supabase.table('product_demand_forecast').select('*').execute().data
        remaining_count = len(remaining) if remaining else 0
    except Exception as old_table_error:
        if 'PGRST205' in str(old_table_error) or 'Could not find the table' in str(old_table_error):
            old_table_existed = False
        else:
            print(f"  NOTE: couldn't check/clear the old product_demand_forecast table: {old_table_error}")

    # --
    # 4b — Upload the new store-wide forecast. Always runs, regardless of
    # what happened to the old table above.
    # --
    # Snapshot table, same pattern as Project 2's sync script — each run
    # replaces the single current row rather than accumulating history.
    supabase.table('store_demand_forecast').delete().neq('id', -1).execute()
    supabase.table('store_demand_forecast').insert(forecast_row.to_dict(orient='records')).execute()

    print("=" * 65)
    print("  SEAMARK - STORE-WIDE FORECAST UPLOAD COMPLETE")
    print("=" * 65)
    if not old_table_existed:
        print(f"  Old product_demand_forecast table  : already deleted — nothing to clear.")
    else:
        print(f"  Old product_demand_forecast rows found   : {old_row_count}")
        print(f"  Old product_demand_forecast rows deleted : {old_row_count - remaining_count}")
        if remaining_count:
            print(f"  WARNING: {remaining_count} old row(s) still remain — check")
            print(f"  the product_demand_forecast table in Supabase manually.")
        else:
            print(f"  Old table is now fully empty.")
    print(f"  New table                                : store_demand_forecast — UPDATED")
    print(f"  Database                                 : Supabase North EU")
    print("=" * 65)

except Exception as error:
    print(f"Supabase upload could not complete: {error}")
    print("The forecast has still been saved locally to outputs/store_demand_forecast.csv")
