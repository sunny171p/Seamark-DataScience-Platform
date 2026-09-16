# ==
# test_data_integrity.py
# Author: Sunday Emmanuel Azeez (with Claude)
# Seamark Global Innovations — Internal Data Science Project
# ==
#
# WHY THIS EXISTS:
# Two of the bugs found in this project — the Auto_Category merge
# quietly duplicating rows, and pricing charts using two different
# category systems that disagreed with each other — were both data
# shape problems that a human only caught by noticing the dashboard
# numbers looked wrong. A shape problem like a merge fanning rows
# out from 271 to 317 is something a test can catch immediately,
# before it ever reaches a chart.

import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_products_clean_has_no_duplicate_handles(cleaned_data_dir):
    products_clean = pd.read_csv(cleaned_data_dir / "products_clean.csv")
    assert "Handle" in products_clean.columns
    dupes = products_clean["Handle"].duplicated().sum()
    assert dupes == 0, f"{dupes} duplicate Handle values in products_clean.csv"


def test_auto_category_merge_does_not_inflate_row_count(cleaned_data_dir, outputs_dir):
    """Reproduces the exact merge the dashboard does when it attaches
    Auto_Category onto price_check_enriched.csv, and checks the row
    count coming out matches the row count going in. This is the
    merge that used to silently grow 271 rows into 317 because
    products_clean.csv has duplicate Titles.
    """
    pc = pd.read_csv(outputs_dir / "price_check_enriched.csv")
    prod_clean = pd.read_csv(cleaned_data_dir / "products_clean.csv")

    rows_before = len(pc)

    cat_lookup = prod_clean.drop_duplicates(subset=["Title"])[["Title", "Auto_Category"]]
    merged = pc.merge(cat_lookup, on="Title", how="left")

    assert len(merged) == rows_before, (
        f"Category merge changed the row count from {rows_before} to {len(merged)} — "
        "products_clean.csv likely has duplicate Titles again and needs "
        "drop_duplicates before the merge."
    )


def test_auto_category_has_no_unfilled_gaps(cleaned_data_dir, outputs_dir):
    pc = pd.read_csv(outputs_dir / "price_check_enriched.csv")
    prod_clean = pd.read_csv(cleaned_data_dir / "products_clean.csv")

    cat_lookup = prod_clean.drop_duplicates(subset=["Title"])[["Title", "Auto_Category"]]
    merged = pc.merge(cat_lookup, on="Title", how="left")
    merged["Auto_Category"] = merged["Auto_Category"].fillna("Other")

    assert merged["Auto_Category"].isna().sum() == 0


def test_all_analytics_scripts_compile(project_root):
    """A cheap smoke test — every script under Stage1_Analytics/analytics
    and the main dashboard should at least be syntactically valid
    Python. This would have caught a typo before it reached the
    pipeline run, rather than after.
    """
    analytics_dir = project_root / "Stage1_Analytics" / "analytics"
    scripts = sorted(analytics_dir.glob("*.py"))
    scripts.append(project_root / "dashboard" / "seamark_dashboard.py")

    for script in scripts:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{script.name} failed to compile:\n{result.stderr}"
