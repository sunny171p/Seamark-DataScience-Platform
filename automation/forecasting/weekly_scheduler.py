"""
SEAMARK - Weekly Auto Scheduler
Runs every Monday at 8am (once registered with Windows Task Scheduler —
see the note at the bottom of this file for how to set that up; this
script does not schedule itself):
1. Re-runs Prophet AI forecast
2. Runs inventory_stock_risk.py to flag stock-out risks against real
   stock levels in automation/seamark_inventory.db
3. Reads that risk data and sends the email report
"""

import subprocess
import smtplib
import sys
import pandas as pd
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

SENDER_EMAIL    = os.getenv("REPORT_EMAIL")
SENDER_PASSWORD = os.getenv("REPORT_PASSWORD")
RECEIVER_EMAIL  = os.getenv("REPORT_EMAIL")
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")

# ── STEP 1: Re-run Prophet forecast ───────────────────────────────────────
def run_forecast():
    print("=" * 60)
    print("  SEAMARK WEEKLY SCHEDULER — STEP 1: Running Prophet AI")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "automation/forecasting/product_demand_forecast.py"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    return True

# ── STEP 2: Run the inventory stock-out risk processor ─────────────────────
def run_inventory_risk_check():
    """
    Runs inventory_stock_risk.py — the script that reads real stock from
    automation/seamark_inventory.db, matches it to the Prophet forecast, and
    writes a proper CRITICAL/HIGH/MEDIUM/LOW/OK risk rating for every
    product to raw_data/inventory_data.csv.
    """
    print("=" * 60)
    print("  SEAMARK WEEKLY SCHEDULER — STEP 2: Inventory Stock-Out Risk Check")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "automation/forecasting/inventory_stock_risk.py"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        print("  Continuing without inventory risk data — the email step")
        print("  below will report this cleanly rather than sending false alarms.")
        return False
    return True

# ── STEP 3: Read the stock-out risk results ─────────────────────────────────
def flag_stockout_risks():
    """
    Reads the risk report inventory_stock_risk.py already produced —
    that script does the real matching against the inventory database
    and computes stock_risk properly. This function's job is just to
    load that result, not to recalculate risk itself.
    """
    print("=" * 60)
    print("  SEAMARK WEEKLY SCHEDULER — STEP 3: Reading Stock-Out Risk Results")
    print("=" * 60)

    csv_path = 'raw_data/inventory_data.csv'

    if os.path.exists(csv_path):
        merged = pd.read_csv(csv_path)
    else:
        merged = pd.DataFrame()

    has_real_inventory = (not merged.empty) and ('stock_risk' in merged.columns)

    if not has_real_inventory:
        print(f"  No usable stock-risk data found at {csv_path} —")
        print("  (either inventory_stock_risk.py didn't run successfully, or")
        print("  hasn't been run yet). Skipping risk flagging for this report.")

        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        pf = pd.DataFrame(sb.table('product_demand_forecast').select('*').execute().data)
        merged = pf.drop_duplicates(subset=['product_name'], keep='first')
        merged['stock_qty'] = 0
        merged['stock_risk'] = 'NO_INVENTORY_DATA'
        critical = merged.iloc[0:0]
        high = merged.iloc[0:0]
        merged.to_csv('outputs/stock_risk_report.csv', index=False)
        return merged, critical, high, has_real_inventory

    critical = merged[merged['stock_risk'] == 'CRITICAL']
    high     = merged[merged['stock_risk'] == 'HIGH']

    print(f"  CRITICAL risk products : {len(critical)}")
    print(f"  HIGH risk products     : {len(high)}")

    merged.to_csv('outputs/stock_risk_report.csv', index=False)
    print("  Stock risk report saved to outputs/stock_risk_report.csv")

    return merged, critical, high, has_real_inventory

# ── STEP 4: Send email report ─────────────────────────────────────────────
def send_email_report(merged, critical, high, has_real_inventory):
    print("=" * 60)
    print("  SEAMARK WEEKLY SCHEDULER — STEP 4: Sending Email Report")
    print("=" * 60)

    now      = datetime.now().strftime('%d %B %Y')
    total_rev = merged['forecast_revenue_90_days'].sum()
    total_units = merged['forecast_units_90_days'].sum()

    inventory_notice = "" if has_real_inventory else """
        <div style="background:#2a1f0e;border-left:4px solid #f59e0b;border-radius:6px;
        padding:10px 14px;margin-bottom:16px;color:#fcd34d;font-size:12px">
            ⚠️ No inventory data found — stock-out risk flagging is unavailable this week.
            Ensure automation/seamark_inventory.db exists and has stock data to enable it.
        </div>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px">
    <div style="background:#0f1117;border-radius:12px;padding:30px;max-width:700px;margin:auto">
        <h1 style="color:#00d4aa;margin:0">🏢 SEAMARK GLOBAL INNOVATIONS</h1>
        <p style="color:#8b92a5;margin:4px 0 20px">Weekly AI Forecast Report — {now}</p>
        {inventory_notice}
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:20px">
            <div style="background:#1e2235;border-radius:8px;padding:14px;text-align:center">
                <div style="color:#8b92a5;font-size:11px">FORECAST REVENUE (90d)</div>
                <div style="color:#ffffff;font-size:22px;font-weight:700">£{total_rev:,.0f}</div>
            </div>
            <div style="background:#1e2235;border-radius:8px;padding:14px;text-align:center">
                <div style="color:#8b92a5;font-size:11px">FORECAST UNITS (90d)</div>
                <div style="color:#ffffff;font-size:22px;font-weight:700">{total_units:,}</div>
            </div>
            <div style="background:#1e2235;border-radius:8px;padding:14px;text-align:center">
                <div style="color:#8b92a5;font-size:11px">PRODUCTS FORECASTED</div>
                <div style="color:#ffffff;font-size:22px;font-weight:700">{len(merged)}</div>
            </div>
        </div>
    """

    if has_real_inventory:
        html += f"""
        <h2 style="color:#ff4b6e;font-size:14px">🚨 CRITICAL STOCK-OUT RISKS ({len(critical)} products)</h2>
        <table style="width:100%;border-collapse:collapse;font-size:12px;color:#ffffff">
            <tr style="background:#2a0e1a;color:#f87171">
                <th style="padding:8px;text-align:left">Product</th>
                <th style="padding:8px;text-align:right">Forecast Units</th>
                <th style="padding:8px;text-align:right">Forecast Revenue</th>
            </tr>
        """
        for _, row in critical.head(10).iterrows():
            html += f"""
                <tr style="border-bottom:1px solid #2e3450">
                    <td style="padding:8px;color:#fff">{str(row['product_name'])[:45]}</td>
                    <td style="padding:8px;text-align:right;color:#f59e0b">{int(row['forecast_units_90_days'])}</td>
                    <td style="padding:8px;text-align:right;color:#00d4aa">£{row['forecast_revenue_90_days']:,.2f}</td>
                </tr>"""

        html += f"""
            </table>
            <h2 style="color:#f59e0b;font-size:14px;margin-top:20px">⚠️ HIGH RISK PRODUCTS ({len(high)} products)</h2>
            <table style="width:100%;border-collapse:collapse;font-size:12px;color:#ffffff">
                <tr style="background:#2a1f0e;color:#fbbf24">
                    <th style="padding:8px;text-align:left">Product</th>
                    <th style="padding:8px;text-align:right">Forecast Units</th>
                    <th style="padding:8px;text-align:right">Forecast Revenue</th>
                </tr>"""
        for _, row in high.head(10).iterrows():
            html += f"""
                <tr style="border-bottom:1px solid #2e3450">
                    <td style="padding:8px;color:#fff">{str(row['product_name'])[:45]}</td>
                    <td style="padding:8px;text-align:right;color:#f59e0b">{int(row['forecast_units_90_days'])}</td>
                    <td style="padding:8px;text-align:right;color:#00d4aa">£{row['forecast_revenue_90_days']:,.2f}</td>
                </tr>"""
        html += "</table>"

    html += """
        <p style="color:#8b92a5;font-size:11px;margin-top:20px;border-top:1px solid #2e3450;padding-top:12px">
            Seamark Global Innovations — AI Forecasting Platform | Prophet AI + Supabase Cloud
        </p>
    </div></body></html>"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📊 Seamark Weekly Forecast Report — {now}"
        msg['From']    = SENDER_EMAIL
        msg['To']      = RECEIVER_EMAIL
        msg.attach(MIMEText(html, 'html'))

        with open('outputs/stock_risk_report.csv', 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename='seamark_stock_risk_report.csv')
            msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        print(f"  Email sent to {RECEIVER_EMAIL} ✅")
        return True
    except Exception as e:
        print(f"  Email error: {e}")
        print("  Check REPORT_EMAIL and REPORT_PASSWORD in your .env file")
        print("  (Gmail requires an App Password, not your normal account password —")
        print("   generate one at https://myaccount.google.com/apppasswords)")
        return False

# ── MAIN ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SEAMARK GLOBAL INNOVATIONS")
    print("  Weekly Auto Scheduler —", datetime.now().strftime('%d %B %Y %H:%M'))
    print("=" * 60 + "\n")

    forecast_ok = run_forecast()
    email_ok = False

    if forecast_ok:
        run_inventory_risk_check()
        merged, critical, high, has_real_inventory = flag_stockout_risks()
        email_ok = send_email_report(merged, critical, high, has_real_inventory)

    print("\n" + "=" * 60)
    if forecast_ok and email_ok:
        print("  WEEKLY SCHEDULER COMPLETE ✅")
    elif forecast_ok and not email_ok:
        print("  WEEKLY SCHEDULER PARTIALLY COMPLETE — forecast ran, email failed ⚠️")
    else:
        print("  WEEKLY SCHEDULER FAILED — forecast step did not complete ❌")
    print("=" * 60)

# ─────────────────────────────────────────────────────────────────────────
# To actually get this running every Monday at 8am, this script needs to
# be registered with Windows Task Scheduler — running the .py file alone
# does not make it recur on its own:
#
#   1. Open Task Scheduler → Create Basic Task
#   2. Trigger: Weekly, Monday, 8:00 AM
#   3. Action: Start a program
#        Program/script:  C:\Users\sunny\OneDrive\Desktop\Seamark_DataScience_Project\.venv\Scripts\python.exe
#        Arguments:       automation\forecasting\weekly_scheduler.py
#        Start in:        C:\Users\sunny\OneDrive\Desktop\Seamark_DataScience_Project
# ─────────────────────────────────────────────────────────────────────────