# ==
# pipeline.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# ==
#
# WHY THIS EXISTS:
# Running eight analysis scripts one by one every time I want a full
# data refresh was getting tedious, and it's easy to forget one of
# the middle stages and end up looking at outputs based on stale
# data without realising it. This master runner executes all eight
# stages in the correct order, captures whether each one succeeded
# or failed, and prints a clean summary at the end.
#
# This replaces an earlier version of the same idea that used to
# live in a since-deleted Stage2_BI_Platform folder and only knew
# about the first six stages. This one lives at the project root,
# next to README.md, and covers all eight.
#
# HOW TO RUN:
#   python pipeline.py
#
# STAGE ORDER MATTERS:
# Stage 1 must run before Stage 2 because classification depends on
# the cleaned CSV. Stage 4 and 5 depend on Stage 2 having added the
# Auto_Category column. Stage 8 needs outputs/price_check_enriched.csv,
# which is written by automation/forecasting/enrich_price_check.py —
# that script now runs as Stage 4.5, right after the internal pricing
# audit and before anything downstream needs its output. (It used to
# be a separate, undocumented script nobody ran automatically, which
# meant a fresh clone running this pipeline would crash at Stage 8 —
# fixed here rather than papered over with a fallback, since the
# Pricing integrity score Stage 8 reports needs this file to be real.)
# Running out of order will cause a missing-file or KeyError failure
# in the downstream scripts.
#
# TIMEOUT:
# Each stage has a 120 second timeout. In practice they all finish
# in a few seconds — the timeout is a safety net for if a script
# hangs waiting for input it doesn't get when run this way.
#
# WHAT TO DO IF A STAGE FAILS:
# Check the error message printed below the failed stage. Most
# failures are either a missing CSV in Stage1_Analytics/raw_data/
# or a column name mismatch after a Shopify export format change.
# ==

import subprocess
import sys
import os
from datetime import datetime

START_TIME = datetime.now()

print("=" * 62)
print("  SEAMARK GLOBAL INNOVATIONS")
print("  Automated Data Science Pipeline")
print(f"  Started: {START_TIME.strftime('%d %B %Y at %H:%M:%S')}")
print("=" * 62)


# -
# PIPELINE STAGES
# -
# Ordered list — do not change the sequence.
# Each tuple is (script filename, human readable stage name)
# -

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_DIR = os.path.join(PROJECT_ROOT, "Stage1_Analytics", "analytics")

# Each tuple is (script path, human readable stage name, working directory
# the script expects to run from). Every stage used to run from
# ANALYTICS_DIR implicitly; Stage 4.5 is the exception because
# enrich_price_check.py's own paths ("Stage1_Analytics/raw_data/...",
# "outputs/...") are written relative to the project root, not the
# analytics folder — same script, unmodified, just run from where it
# actually expects to sit.
pipeline_stages = [
    ("01_data_cleaning.py",          "Stage 1 — Data Cleaning & Preparation", ANALYTICS_DIR),
    ("02_product_classification.py", "Stage 2 — Product Classification", ANALYTICS_DIR),
    ("03_funnel_analysis.py",        "Stage 3 — Conversion Funnel Analysis", ANALYTICS_DIR),
    ("04_pricing_analysis.py",       "Stage 4 — Internal Pricing Audit", ANALYTICS_DIR),
    ("automation/forecasting/enrich_price_check.py", "Stage 4.5 — Enriched Price Check (feeds Stage 8)", PROJECT_ROOT),
    ("05_competitive_pricing.py",    "Stage 5 — Competitive Pricing vs Amazon", ANALYTICS_DIR),
    ("06_affiliate_analysis.py",     "Stage 6 — Affiliate Programme Analysis", ANALYTICS_DIR),
    ("07_traffic_analysis.py",       "Stage 7 — Traffic & Landing Page Analysis", ANALYTICS_DIR),
    ("08_pipeline_health.py",        "Stage 8 — Pipeline Health & Data Quality", ANALYTICS_DIR),
]

results = []


# --
# EXECUTE EACH STAGE
# -

for filename, stage_name, stage_cwd in pipeline_stages:

    print(f"\n{'─' * 62}")
    print(f"  {stage_name}")
    print(f"  Running: {filename}")
    print(f"{'─' * 62}")

    try:
        result = subprocess.run(
            [sys.executable, filename],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=stage_cwd,
        )

        if result.returncode == 0:
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")
            print(f"\n  Result: SUCCESS")
            results.append((stage_name, "SUCCESS", None))

        else:
            print(f"\n  Result: FAILED")
            error_snippet = result.stderr[-300:] if result.stderr else "No error output captured"
            print(f"  Error : {error_snippet}")
            results.append((stage_name, "FAILED", error_snippet))

    except subprocess.TimeoutExpired:
        print(f"\n  Result: TIMEOUT — exceeded 120 seconds")
        results.append((stage_name, "TIMEOUT", "Exceeded 120 second limit"))

    except Exception as e:
        print(f"\n  Result: ERROR — {str(e)}")
        results.append((stage_name, "ERROR", str(e)))


# -
# PIPELINE SUMMARY
# -

END_TIME = datetime.now()
DURATION = (END_TIME - START_TIME).seconds

success_count = sum(1 for _, status, _ in results if status == "SUCCESS")
fail_count = len(results) - success_count

print(f"\n\n{'=' * 62}")
print("  PIPELINE SUMMARY")
print(f"{'=' * 62}")

for stage_name, status, error in results:
    status_label = "OK  " if status == "SUCCESS" else "FAIL"
    print(f"  [{status_label}]  {stage_name}")
    if error:
        print(f"         {error[:120]}")

print(f"\n{'─' * 62}")
print(f"  Stages run    : {len(pipeline_stages)}")
print(f"  Successful    : {success_count}")
print(f"  Failed        : {fail_count}")
print(f"  Duration      : {DURATION} seconds")
print(f"  Finished      : {END_TIME.strftime('%d %B %Y at %H:%M:%S')}")
print(f"{'─' * 62}")

if fail_count == 0:
    print("\n  ALL STAGES PASSED")
    print("  Charts saved to  : Stage1_Analytics/outputs/")
    print("  CSV outputs      : outputs/")
    print("  Cleaned data     : Stage1_Analytics/cleaned_data/")
    print("  Next: streamlit run dashboard/seamark_dashboard.py")
else:
    print(f"\n  PIPELINE FINISHED WITH {fail_count} FAILURE(S)")
    print("  Common causes:")
    print("  - Missing CSV in Stage1_Analytics/raw_data/")
    print("  - Column name changed in latest Shopify export")
    print("  - Run the failed stage individually to see the full error")

print(f"{'=' * 62}\n")
