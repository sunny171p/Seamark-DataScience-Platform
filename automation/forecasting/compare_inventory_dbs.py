"""
One-off diagnostic: compares the two non-empty copies of
seamark_inventory.db (root and automation/) side by side so we can see
which one holds real, hand-curated data and which is likely the
auto-generated placeholder created by today's setup script.

Run from anywhere — this works out the project root itself based on
where this file is saved, so it no longer matters which folder your
terminal happens to be sitting in when you run it:

    python automation/forecasting/compare_inventory_dbs.py
"""

import sqlite3
import os

# This file lives at <project_root>/automation/forecasting/compare_inventory_dbs.py
# so the project root is two folders up from here — computed from the
# file's own location instead of relying on the terminal's current
# directory, which is what caused confusion before.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))

candidates = [
    os.path.join(PROJECT_ROOT, 'seamark_inventory.db'),
    os.path.join(PROJECT_ROOT, 'automation', 'seamark_inventory.db'),
]

for path in candidates:
    print("=" * 70)
    print(f"  {path}")
    print("=" * 70)

    if not os.path.exists(path):
        print("  File not found.")
        continue

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM inventory")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count}")

        print("\n  First 5 rows:")
        cursor.execute("SELECT sku, item_name, category, stock, retail_gbp FROM inventory LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"    {row}")

        # Distinct stock values gives a hint: real curated data tends to
        # have varied, specific numbers; auto-generated placeholder data
        # often has a suspiciously uniform or round pattern.
        cursor.execute("SELECT DISTINCT stock FROM inventory ORDER BY stock LIMIT 10")
        distinct_stock = [r[0] for r in cursor.fetchall()]
        print(f"\n  Sample of distinct stock values: {distinct_stock}")

    except sqlite3.OperationalError as e:
        print(f"  Error reading table: {e}")

    conn.close()
    print()