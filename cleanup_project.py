# ==
# cleanup_project.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: September 2026
# ==
#
# WHY THIS EXISTS:
# The project picked up a lot of dead weight over the debugging
# sessions — one-off check_*.py / fix_*.py scripts, a second
# abandoned dashboard, a stale duplicate raw_data folder, and a
# couple of empty database files. This deletes exactly those and
# nothing else.
#
# HOW TO RUN IT:
# Put this file in the project root (next to README.md) and run:
#   python cleanup_project.py
# By default it only PRINTS what it would delete — nothing is
# removed until you run it again with --live:
#   python cleanup_project.py --live
#
# Stage2_BI_Platform is deliberately left out of the delete list —
# see the comment near the bottom for why, and how to add it in
# once you've confirmed you don't still use pipeline.py.
# ==

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
LIVE_RUN = '--live' in sys.argv

# --
# ROOT-LEVEL DEBUG SCRIPTS
# --
# check1.py through check11.py and fix_*.py — one-off scripts from
# the original bug-hunting sessions. Nothing in the pipeline or the
# dashboard imports or runs any of these.
# --
dead_scripts = [
    "check.py", "check2.py", "check3.py", "check4.py", "check5.py",
    "check6.py", "check8.py", "check9.py", "check10.py", "check11.py",
    "fix_cats.py", "fix_cats2.py", "fix_cats3.py", "fix_checkout.py",
    "fix_final.py", "fix_kpi.py", "fix_products.py", "fix_products2.py",
    "fix_rev.py", "fix_rev2.py", "fix_tp.py", "fix_tp2.py", "fix_tp3.py",
    "patch_dashboard.py",
]

# --
# SUPERSEDED OR EMPTY
# --
# online app.py is a second dashboard built with plain http.server
# instead of Streamlit, pointing at a database that's empty anyway.
# The root-level raw_data folder is a stale duplicate of files that
# now live properly under Stage1_Analytics/raw_data — it's missing
# the files several scripts actually need, so nothing reads from it.
# Both seamark_inventory.db files here are 0 bytes.
# --
dead_files = [
    "dashboard/online app.py",
    "automation/seamark_inventory.db",
    "Stage1_Analytics/analytics/seamark_inventory.db",
    "tests/test_placeholder.py",
]

dead_folders = [
    "raw_data",  # the root-level one — Stage1_Analytics/raw_data is the real one
]


def delete_path(rel_path, is_folder=False):
    full_path = PROJECT_ROOT / rel_path
    if not full_path.exists():
        print(f"  (skip — not found) {rel_path}")
        return
    if not LIVE_RUN:
        print(f"  would delete: {rel_path}")
        return
    if is_folder:
        import shutil
        shutil.rmtree(full_path)
    else:
        full_path.unlink()
    print(f"  deleted: {rel_path}")


def main():
    mode = "LIVE — files will actually be deleted" if LIVE_RUN else "DRY RUN — nothing will be deleted yet"
    print("=" * 60)
    print(f"  SEAMARK PROJECT CLEANUP — {mode}")
    print("=" * 60)

    print("\nRoot-level debug scripts:")
    for f in dead_scripts:
        delete_path(f)

    print("\nSuperseded / empty files:")
    for f in dead_files:
        delete_path(f)

    print("\nStale folders:")
    for f in dead_folders:
        delete_path(f, is_folder=True)

    if not LIVE_RUN:
        print("\nThis was a dry run — nothing was deleted.")
        print("Review the list above, then run: python cleanup_project.py --live")
    else:
        print("\nCleanup complete.")

    # --
    # STAGE2_BI_PLATFORM — LEFT OUT ON PURPOSE
    # --
    # Its automation/, dashboard/, and assets/ subfolders are empty,
    # and most of what's left is either placeholder seed data or the
    # same kind of one-off debug script as the ones above. But
    # pipeline.py in there actually runs the six real Stage 1
    # analytics scripts in sequence — if you're not using that to
    # kick off your pipeline, uncomment the two lines below and
    # re-run. If you are still using it, copy pipeline.py somewhere
    # else first.
    # --
    # dead_folders_confirmed = ["Stage2_BI_Platform"]
    # for f in dead_folders_confirmed:
    #     delete_path(f, is_folder=True)


if __name__ == "__main__":
    main()
