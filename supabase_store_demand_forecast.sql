-- ==
-- supabase_store_demand_forecast.sql
-- Seamark Global Innovations — Project 1
-- ==
--
-- Run this once in the Supabase SQL editor before running the rewritten
-- automation/forecasting/product_demand_forecast.py. Creates a NEW table —
-- it does not touch or replace the existing product_demand_forecast table,
-- which still holds whatever real per-product data it last had. See the
-- header comment in product_demand_forecast.py for why the two are now
-- separate: sales_data.csv no longer has per-product columns to forecast
-- from, so this is a store-wide number, not a per-product one.

create table if not exists store_demand_forecast (
    id bigint generated always as identity primary key,
    forecast_generated_at text,
    months_of_history integer,
    total_revenue_to_date_gbp numeric,
    total_units_to_date integer,
    predicted_revenue_90_days_gbp numeric,
    predicted_units_90_days integer,
    scope text,
    why_not_per_product text,
    synced_at timestamptz default now()
);

-- Row Level Security left off by default, matching this project's existing
-- product_demand_forecast table and Project 2's Supabase tables.
