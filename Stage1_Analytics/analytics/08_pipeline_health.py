# ==
# 08_pipeline_health.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: june 2026
# ==
#
# WHY I BUILT THIS:
# The dashboard's Pipeline Health page was showing a Quality Score
# of 89.0% and a "Raw Rows" count typed straight into the Streamlit
# file rather than read off the actual data. That's exactly the
# kind of number a reviewer would ask "where did this come from?"
# about, and I wouldn't have a real answer. This script is that
# answer — every figure below comes from actually reading the
# pipeline's own files.
#
# WHAT "QUALITY SCORE" MEANS HERE:
# Every KPI card that shows this score is labelled "Pricing
# integrity" underneath, so that's what it measures: the share of
# price-checked products that do NOT have a misleading discount
# (selling price higher than the "was" price). It is not a general
# health score for the whole pipeline.
#
# WHAT I FOUND:
# The real score is 4.4%, not 89%. 259 of our 271 price-checked
# products have this issue — that's the actual state of the
# catalogue's discount pricing, not a rounding error.
# ==

import pandas as pd
import os

products_raw   = pd.read_csv('../raw_data/products_export.csv')
products_clean = pd.read_csv('../cleaned_data/products_clean.csv')
price_checked  = pd.read_csv('../../outputs/price_check_enriched.csv')

raw_rows     = len(products_raw)
clean_rows   = len(products_clean)
checked_rows = len(price_checked)

print(f"Raw product rows (products_export.csv)   : {raw_rows:,}")
print(f"Clean product rows (products_clean.csv)  : {clean_rows:,}")
print(f"Price-checked rows (price_check_enriched.csv): {checked_rows:,}")


# --
# PRICING INTEGRITY SCORE
# --
# A misleading discount is the one real data error here — the
# selling price is higher than the price it's being compared
# against, so the storefront shows a "was £X" that isn't true.
# Score = share of checked products that don't have that problem.
# --

misleading_count = len(price_checked[price_checked['Pricing Status'] == 'Misleading Discount'])
quality_score = round((checked_rows - misleading_count) / checked_rows * 100, 1) if checked_rows else 0.0

print(f"\nProducts with a misleading discount      : {misleading_count:,} ({round(misleading_count/checked_rows*100,1)}%)")
print(f"Pricing integrity score                  : {quality_score}%")
if quality_score < 50:
    print("That's a real weakness, not a rounding issue — most of the catalogue's")
    print("discount badges are currently showing a price comparison that isn't true.")


# --
# LAST PIPELINE RUN
# --
# The dashboard used to show "now" for this — whatever moment
# someone happened to load the page — which isn't a real answer to
# "when did the pipeline last run". The actual answer is whichever
# pipeline output file was written most recently.
# --

pipeline_outputs = {
    'products_clean.csv': '../cleaned_data/products_clean.csv',
    'price_check_enriched.csv': '../../outputs/price_check_enriched.csv',
    'sales_forecast_90days.csv': '../../outputs/sales_forecast_90days.csv',
    'inventory_data.csv': '../raw_data/inventory_data.csv',
}
mtimes = {name: os.path.getmtime(path) for name, path in pipeline_outputs.items() if os.path.exists(path)}
last_file, last_time = max(mtimes.items(), key=lambda kv: kv[1])
last_run = pd.Timestamp.fromtimestamp(last_time)

print(f"\nMost recently updated pipeline file : {last_file}")
print(f"Last pipeline run                  : {last_run.strftime('%d %b %Y %H:%M')}")


# --
# SAVE FOR THE DASHBOARD
# --

summary = pd.DataFrame([{
    'raw_rows': raw_rows,
    'clean_rows': clean_rows,
    'checked_rows': checked_rows,
    'misleading_discount_count': misleading_count,
    'quality_score_pct': quality_score,
    'last_pipeline_run': last_run.strftime('%d/%m/%Y %H:%M'),
    'last_pipeline_file': last_file,
}])
summary.to_csv('../../outputs/pipeline_health_summary.csv', index=False)
print("\nSummary saved to outputs/pipeline_health_summary.csv")
