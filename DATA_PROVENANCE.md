# Where Every Number On The Dashboard Actually Comes From

I wrote this after going through the dashboard page by page and asking, for every figure on it, "if someone technical asked me where this came from, could I actually answer that?" A few numbers used to fail that test. This file is the honest answer for all of them, split into the three categories any number on this dashboard falls into, so nothing has to be taken on trust.

## 1. Computed directly from the raw CSVs, every time the pipeline runs

This is almost everything on the dashboard. Each figure below is produced by a specific script reading a specific file in `Stage1_Analytics/raw_data/` or `Stage1_Analytics/cleaned_data/`, saved to `outputs/`, and read from there by the dashboard rather than being retyped:

- **Quality Score / Raw Rows / Last Pipeline Run** (Pipeline Health page) — `Stage1_Analytics/analytics/08_pipeline_health.py`, reading `products_export.csv`, `products_clean.csv` and `price_check_enriched.csv` (the last of these is itself produced by `automation/forecasting/enrich_price_check.py`, which runs as Stage 4.5 of `pipeline.py`). This page used to show a hardcoded, reassuring-looking figure that was never read from anything; the real quality score is 4.4%, because 259 of 271 price-checked products have a discount comparison that doesn't hold up.
- **Seamark vs Amazon UK pricing** (Competitive Pricing page) — `Stage1_Analytics/analytics/05_competitive_pricing.py`, comparing `products_clean.csv` against the benchmark file described in section 2 below.
- **Direct traffic %, homepage landing %, page-load depth** (Traffic & Funnel page) — `Stage1_Analytics/analytics/07_traffic_analysis.py`, reading the five Shopify Analytics exports in `raw_data/`.
- **Checkout rate, sessions, visitors** (Overview and Funnel pages) — one formula (`total_checkout / total_sessions`), used everywhere it appears, rather than two different formulas quietly giving two different answers on two different pages.
- **Category counts and average prices** — `products_clean.csv`'s own `Auto_Category` column throughout, not the separate raw category field, so the same product always lands in the same category on every page.

Every one of these is checked automatically now — see `tests/test_pipeline_outputs.py`, which independently redoes each calculation from the raw files and fails if a saved output ever stops matching.

## 2. Real inputs I supplied by hand, because there's no substitute yet

Two things on this dashboard are not derived from a Shopify export, and I want to be upfront about exactly what they are instead of leaving that ambiguous:

- **Amazon UK benchmark prices** (`Stage1_Analytics/raw_data/amazon_uk_benchmarks.csv`) — I manually checked 3-5 representative products per category on Amazon UK in June 2026 and averaged the mid-range prices. This is a real, dated, sourced observation, not invented, but it's a snapshot rather than a live feed, and it's due for a refresh — the note column in that file says so for each row.
- **Sample order data used to train the sales forecast** — the store has taken zero real orders so far, so `orders_export.csv` contains synthetic rows built only to give Prophet a training series to demonstrate the forecasting pipeline on. The dashboard states this directly wherever the forecast is shown, and `total_orders` is hardcoded to `0` on purpose, not derived from that synthetic file, because the honest business state is zero orders until real ones exist.

Neither of these is presented as more than it is anywhere on the dashboard.

## 3. Editorial judgement calls, not data

A handful of lines in the analytics scripts are `if` statements like `if direct_pct > 70` or `if quality_score < 50`. These don't change any number — they decide whether to print an extra warning sentence underneath a number that's already been computed honestly. 70% and 50% are my own judgement calls about where a metric stops being fine and starts being a real problem worth flagging, the same way a person would circle a number in red on a printed report. They're documented here so nobody mistakes them for data.

## How this stays true going forward

`tests/test_dashboard_honesty.py` scans the dashboard source for the specific fabricated figures this project used to have and fails if any of them are ever typed back in as a literal — the exact values it checks for are listed in that file itself, not repeated here, since keeping one copy of a "banned figure" list is the same principle as keeping one copy of the Amazon benchmarks. `tests/test_pipeline_outputs.py` and `tests/test_data_integrity.py` cover the calculations and the data shape underneath them. Running `pytest` from the project root checks all of it in under a second.
