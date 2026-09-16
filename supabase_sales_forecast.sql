-- ==
-- supabase_sales_forecast.sql
-- Seamark Global Innovations — Project 1
-- ==
--
-- Run this once in the Supabase SQL editor before running the updated
-- automation/forecasting/sales_forecast.py. That script now uploads its
-- daily 90-day forecast to Supabase (previously it only saved locally).
--
-- A table named sales_forecast already existed in this project, left over
-- from an older, abandoned script (upload_to_db.py) that used a different
-- connection method (raw psycopg2, not the supabase-py client the rest of
-- this project uses) and different env vars that were never set — so it
-- never actually ran. Sunday confirmed that old table has no real data in
-- it, so this drops it and creates a clean one with the exact columns
-- sales_forecast.py's upload step expects, rather than guessing whether
-- the old, never-used table's shape happens to match.

drop table if exists sales_forecast;

create table sales_forecast (
    id bigint generated always as identity primary key,
    ds date not null,
    yhat numeric,
    yhat_lower numeric,
    yhat_upper numeric,
    synced_at timestamptz default now()
);

-- Row Level Security left off by default, matching this project's other
-- tables (product_demand_forecast, store_demand_forecast).
