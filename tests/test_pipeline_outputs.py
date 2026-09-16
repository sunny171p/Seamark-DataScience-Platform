# ==
# test_pipeline_outputs.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# ==
#
# WHY THIS EXISTS:
# 05_competitive_pricing.py, 07_traffic_analysis.py and
# 08_pipeline_health.py each read raw data, do a calculation, and
# save a one-row (or one-table) summary CSV that the dashboard
# trusts completely — it never redoes the maths itself. 
# right way to avoid the dashboard and the terminal scripts drifting
# apart, but it only works as long as the saved CSV actually matches
# what the raw data says. These tests redo each calculation
# independently, straight from raw_data/ and cleaned_data/, and
# check the answer against whatever the script already saved to
# outputs/. If a raw CSV changes, or someone edits the maths in one
# place and not the other, one of these fails instead of the
# dashboard quietly showing a stale or wrong number.

import pandas as pd
import pytest


def test_pipeline_health_matches_recomputation(raw_data_dir, cleaned_data_dir, outputs_dir):
    products_raw = pd.read_csv(raw_data_dir / "products_export.csv")
    products_clean = pd.read_csv(cleaned_data_dir / "products_clean.csv")
    price_checked = pd.read_csv(outputs_dir / "price_check_enriched.csv")

    expected_raw_rows = len(products_raw)
    expected_clean_rows = len(products_clean)
    expected_checked_rows = len(price_checked)
    expected_misleading = len(price_checked[price_checked["Pricing Status"] == "Misleading Discount"])
    expected_quality_score = round(
        (expected_checked_rows - expected_misleading) / expected_checked_rows * 100, 1
    )

    saved = pd.read_csv(outputs_dir / "pipeline_health_summary.csv").iloc[0]

    assert int(saved["raw_rows"]) == expected_raw_rows
    assert int(saved["clean_rows"]) == expected_clean_rows
    assert int(saved["checked_rows"]) == expected_checked_rows
    assert int(saved["misleading_discount_count"]) == expected_misleading
    assert saved["quality_score_pct"] == pytest.approx(expected_quality_score, abs=0.05)


def test_competitive_pricing_matches_recomputation(raw_data_dir, cleaned_data_dir, outputs_dir):
    products_clean = pd.read_csv(cleaned_data_dir / "products_clean.csv")
    benchmarks = pd.read_csv(raw_data_dir / "amazon_uk_benchmarks.csv")
    benchmark_lookup = dict(zip(benchmarks["Category"], benchmarks["Amazon Benchmark (GBP)"]))

    expected_avg = (
        products_clean.groupby("Auto_Category")["Variant Price"].mean().round(2)
    )

    saved = pd.read_csv(outputs_dir / "competitive_pricing.csv").set_index("Category")

    for category, expected_price in expected_avg.items():
        assert category in saved.index, f"{category} is missing from competitive_pricing.csv"
        assert saved.loc[category, "Seamark Avg Price (£)"] == pytest.approx(expected_price, abs=0.01)
        assert saved.loc[category, "Amazon Benchmark (£)"] == pytest.approx(
            benchmark_lookup[category], abs=0.01
        )


def test_traffic_analysis_matches_recomputation(raw_data_dir, outputs_dir):
    sessions = pd.read_csv(raw_data_dir / "sessions_by_month_365d.csv")
    sources = pd.read_csv(raw_data_dir / "traffic_sources_365d.csv")
    landing = pd.read_csv(raw_data_dir / "top_landing_pages_365d.csv")
    page_loads = pd.read_csv(raw_data_dir / "web_performance_page_loads_365d.csv")

    total_sessions = int(sessions["Sessions"].sum())
    total_checkout = int(sessions["Sessions that reached checkout"].sum())
    expected_checkout_rate = round(total_checkout / total_sessions * 100, 2)

    direct_sessions = int(sources[sources["Referrer source"] == "direct"]["Sessions"].sum())
    expected_direct_pct = round(direct_sessions / sources["Sessions"].sum() * 100, 1)

    home_landing = int(landing[landing["Landing page path"] == "/"]["Sessions"].sum())
    expected_home_landing_pct = round(home_landing / landing["Sessions"].sum() * 100, 1)

    total_loads = int(page_loads["Page loads"].sum())
    product_loads = int(page_loads[page_loads["Page path"].str.startswith("/products/")]["Page loads"].sum())
    expected_product_pageload_pct = round(product_loads / total_loads * 100, 1)

    saved = pd.read_csv(outputs_dir / "traffic_analysis_summary.csv").iloc[0]

    assert int(saved["total_sessions"]) == total_sessions
    assert saved["checkout_rate_pct"] == pytest.approx(expected_checkout_rate, abs=0.01)
    assert saved["direct_traffic_pct"] == pytest.approx(expected_direct_pct, abs=0.05)
    assert saved["home_landing_pct"] == pytest.approx(expected_home_landing_pct, abs=0.05)
    assert saved["product_pageload_pct"] == pytest.approx(expected_product_pageload_pct, abs=0.05)
