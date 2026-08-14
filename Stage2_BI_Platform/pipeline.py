# =
# pipeline.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# =
#
# WHY I BUILT THIS:
# Running six analysis scripts one by one every time I want
# a full data refresh was getting tedious — and I kept forgetting
# to run one of the middle stages which meant the outputs were
# based on stale data without me realising.
#
# This master runner executes all six stages in the correct
# order, captures whether each one succeeded or failed, and
# prints a clean summary at the end. One command, full pipeline.
#
# HOW TO RUN:
#   cd analytics
#   python pipeline.py
#
# STAGE ORDER MATTERS:
# Stage 1 must run before Stage 2 because classification depends
# on the cleaned CSV. Stage 4 and 5 depend on Stage 2 having
# added the Auto_Category column. Running out of order will
# cause KeyError failures in the downstream scripts.
#
# TIMEOUT:
# Each stage has a 120 second timeout. In practice they all
# finish in under 30 seconds — the timeout is a safety net
# for if a script hangs waiting for user input accidentally
# (manage_inventory.py has input() calls so it is excluded).
#
# WHAT TO DO IF A STAGE FAILS:
# Check the error message printed below the failed stage.
# Most failures are either a missing CSV file in raw_data/
# or a column name mismatch after a Shopify export format change.
# =

import subprocess
import sys
from datetime import datetime
import os

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

pipeline_stages = [
    ("analytics/01_data_cleaning.py",          "Stage 1 — Data Cleaning & Preparation"),
    ("analytics/02_product_classification.py", "Stage 2 — Product Classification"),
    ("analytics/03_funnel_analysis.py",        "Stage 3 — Conversion Funnel Analysis"),
    ("analytics/04_pricing_analysis.py",       "Stage 4 — Internal Pricing Audit"),
    ("analytics/05_competitive_pricing.py",    "Stage 5 — Competitive Pricing vs Amazon"),
    ("analytics/06_affiliate_analysis.py",     "Stage 6 — Affiliate Programme Analysis"),
]

results = []


# --
# EXECUTE EACH STAGE
# -

for filename, stage_name in pipeline_stages:

    print(f"\n{'─' * 62}")
    print(f"  {stage_name}")
    print(f"  Running: {filename}")
    print(f"{'─' * 62}")

    try:
        result = subprocess.run(
    [sys.executable, filename.replace("analytics/", "")],
    capture_output=True,
    text=True,
    timeout=120,
    cwd=os.path.join(os.path.dirname(__file__), "analytics")
)
# Safety net — scripts should finish in <30s


        if result.returncode == 0:
            # Print the script's own output so I can see what it did
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")
            print(f"\n  Result: SUCCESS")
            results.append((stage_name, "SUCCESS", None))

        else:
            print(f"\n  Result: FAILED")
            # Show last 300 chars of stderr — usually enough to identify the issue
            error_snippet = result.stderr[-300:] if result.stderr else "No error output captured"
            print(f"  Error : {error_snippet}")
            results.append((stage_name, "FAILED", error_snippet))

    except subprocess.TimeoutExpired:
        # Script ran for more than 120 seconds — something is wrong
        print(f"\n  Result: TIMEOUT — exceeded 120 seconds")
        print(f"  Check the script is not waiting for user input")
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
    print("  Charts saved to  : ../outputs/")
    print("  Cleaned data     : ../cleaned_data/")
    print("  Next: open online_app.py to view the dashboard")
else:
    print(f"\n  PIPELINE FINISHED WITH {fail_count} FAILURE(S)")
    print("  Common causes:")
    print("  - Missing CSV in raw_data/ folder")
    print("  - Column name changed in latest Shopify export")
    print("  - Run the failed stage individually to see the full error")

print(f"{'=' * 62}\n")
