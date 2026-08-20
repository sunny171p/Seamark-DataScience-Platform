# ====
# Seamark_store_insights.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ==
#
# WHY I BUILT THIS:
# I was spending time every week manually pulling numbers from
# different places — Shopify for sales, a spreadsheet for costs,
# another tab for supplier stock. It was slow and error-prone.
#
# This script joins all three tables in one place and prints
# a unified business report in seconds. It is the closest thing
# I have to a management dashboard before the web app is ready.
#
# WHAT IT REPORTS:
# 1. Profit margin per product — using actual cost vs retail
# 2. Supplier distribution — which partners hold how much stock
#
# CURRENCY NOTE:
# Costs are stored in USD (as supplied by DSers/AliExpress).
# I convert to GBP using 0.75 as a fixed rate in this script.
# The live_exchange.py script handles dynamic rate updates
# separately — this report uses a conservative fixed rate
# to give a worst-case margin view.
#
# HOW I USE THIS:
# I run this every Monday morning before checking Shopify admin.
# It gives me a quick read on which products are actually
# profitable and whether any suppliers are running low on stock.
# ==

import sqlite3

DB_FILE = "seamark_inventory.db"


def run_business_intelligence():
    """
    Generates a unified business intelligence report by joining
    sales_log, inventory, and suppliers tables in SQLite.
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("=" * 55)
    print("  SEAMARK GLOBAL INNOVATIONS")
    print("  Weekly Business Intelligence Report")
    print("  Internal use — Sunday Emmanuel Azeez")
    print("=" * 55)


    # -
    # REPORT 1 — PROFIT MARGIN ANALYSIS
    # --
    # Joins sales_log (what sold) with inventory (cost and price)
    # to calculate gross revenue, cost basis, and net profit
    # per product.
    #
    # I use INNER JOIN here deliberately — products with no sales
    # history should not appear in a profit report. LEFT JOIN
    # would include them with NULL values which clutters the output.
    #
    # The 0.75 rate converts USD cost to GBP. Conservative estimate
    # — actual rate varies but this gives a reliable floor margin.
    # --

    print("\n[1] PROFIT MARGIN BY PRODUCT")
    print("-" * 55)

    query_margins = """
        SELECT 
            i.item_name,
            SUM(s.qty_sold) AS total_qty_sold,
            SUM(s.qty_sold * i.retail_gbp) AS gross_revenue_gbp,
            SUM(s.qty_sold * (i.cost_usd * 0.75)) AS cost_basis_gbp,
            SUM(s.qty_sold * i.retail_gbp) - 
            SUM(s.qty_sold * (i.cost_usd * 0.75)) AS net_profit_gbp
        FROM sales_log s
        INNER JOIN inventory i ON s.sku = i.sku
        GROUP BY i.sku
        ORDER BY net_profit_gbp DESC;
    """

    cursor.execute(query_margins)
    margin_rows = cursor.fetchall()

    if not margin_rows:
        print("No sales data found — check sales_log table is populated")
    else:
        total_revenue = 0
        total_profit = 0

        for row in margin_rows:
            item_name, qty_sold, gross_revenue, cost_basis, net_profit = row

            # Flag negative margin products immediately
            margin_flag = " *** NEGATIVE MARGIN ***" if net_profit < 0 else ""

            print(f"  {item_name:<25} | "
                  f"Units: {qty_sold:<4} | "
                  f"Revenue: £{gross_revenue:>8,.2f} | "
                  f"Profit: £{net_profit:>8,.2f}"
                  f"{margin_flag}")

            total_revenue += gross_revenue
            total_profit += net_profit

        print(f"\n  TOTAL REVENUE : £{total_revenue:,.2f}")
        print(f"  TOTAL PROFIT  : £{total_profit:,.2f}")

        if total_revenue > 0:
            overall_margin = (total_profit / total_revenue) * 100
            print(f"  OVERALL MARGIN: {overall_margin:.1f}%")


    # ---
    # REPORT 2 — SUPPLIER STOCK AUDIT
    # ---
    # LEFT JOIN used here so suppliers with zero products still
    # appear — I want to know if a supplier relationship exists
    # but no inventory has been assigned to them yet.
    #
    # Added region column because we work with suppliers across
    # UK, China, and US — useful to see geographic distribution
    # of our stock holdings at a glance.
    # --

    print("\n\n[2] SUPPLIER STOCK DISTRIBUTION")
    print("-" * 55)

    query_suppliers = """
        SELECT 
            sup.name,
            COUNT(i.sku) AS product_count,
            COALESCE(SUM(i.stock), 0) AS total_stock_units
        FROM suppliers sup
        LEFT JOIN inventory i ON sup.id = i.supplier_id
        GROUP BY sup.id
        ORDER BY total_stock_units DESC;
    """

    cursor.execute(query_suppliers)
    supplier_rows = cursor.fetchall()

    if not supplier_rows:
        print("No supplier data found — check suppliers table is populated")
    else:
        for row in supplier_rows:
            supplier_name, product_count, total_stock = row

            # Flag suppliers with very low total stock
            stock_flag = " *** LOW STOCK ***" if total_stock < 10 else ""

            print(f"  {supplier_name:<28} | "
                  f"Products: {product_count:<4} | "
                  f"Stock: {total_stock} units"
                  f"{stock_flag}")

    conn.close()

    print("\n" + "=" * 55)
    print("  Report complete — run every Monday for weekly review")
    print("=" * 55)


# --
# ENTRY POINT
# --

if __name__ == "__main__":
    run_business_intelligence()
