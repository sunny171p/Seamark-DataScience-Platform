"""
SEAMARK - Weekly Auto Scheduler
Runs every Monday at 8am (once registered with Windows Task Scheduler —
see the note at the bottom of this file for how to set that up; this
script does not schedule itself):
1. Re-runs the store-wide Prophet AI forecast
2. Emails a summary report

== REWRITTEN (September 2026) — read this before re-running ==

WHAT WAS REMOVED AND WHY:
This script used to have a Step 2 that called
automation/forecasting/inventory_stock_risk.py — that script does not
exist anywhere in this project (it was referenced but never built, or was
deleted at some point). Every run of this scheduler would fail that step,
fall back to a placeholder path, AND that placeholder path queried the old
`product_demand_forecast` Supabase table for a `product_name` column. Since
sales_data.csv was rectified down to store-wide monthly totals (see
product_demand_forecast.py's header comment) and that old table has since
been cleared of its stale per-product rows, this fallback would now come
back with nothing useful — another reason this scheduler would look
"broken" even after the forecast script itself was fixed.

Rather than keep dead code pointing at a script that doesn't exist and a
data shape that no longer exists, this rewrite removes the inventory
stock-risk step and the per-product email tables entirely, and sends a
simple, honest store-wide summary instead — pulled straight from
outputs/store_demand_forecast.csv, which the rewritten
product_demand_forecast.py already writes on every run.

If you rebuild real inventory tracking and a real inventory_stock_risk.py
later, that step and its email section can be added back in — this file
just no longer pretends they exist.
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
from datetime import datetime

load_dotenv()

SENDER_EMAIL    = os.getenv("REPORT_EMAIL")
SENDER_PASSWORD = os.getenv("REPORT_PASSWORD")
RECEIVER_EMAIL  = os.getenv("REPORT_EMAIL")

# ── STEP 1: Re-run the store-wide Prophet forecast ─────────────────────────
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

# ── STEP 2: Read the store-wide forecast the script just saved ─────────────
def load_forecast():
    print("=" * 60)
    print("  SEAMARK WEEKLY SCHEDULER — STEP 2: Reading Store-Wide Forecast")
    print("=" * 60)

    csv_path = 'outputs/store_demand_forecast.csv'
    if not os.path.exists(csv_path):
        print(f"  No forecast file found at {csv_path} — Step 1 may not have")
        print("  completed. Skipping email.")
        return None

    forecast = pd.read_csv(csv_path).iloc[0]
    print(f"  Predicted revenue (90d) : £{forecast['predicted_revenue_90_days_gbp']:,.2f}")
    print(f"  Predicted units (90d)   : {int(forecast['predicted_units_90_days'])}")
    return forecast

# ── STEP 3: Send email report ────────────────────────────────────────────
def send_email_report(forecast):
    print("=" * 60)
    print("  SEAMARK WEEKLY SCHEDULER — STEP 3: Sending Email Report")
    print("=" * 60)

    now = datetime.now().strftime('%d %B %Y')

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px">
    <div style="background:#0f1117;border-radius:12px;padding:30px;max-width:700px;margin:auto">
        <h1 style="color:#00d4aa;margin:0">🏢 SEAMARK GLOBAL INNOVATIONS</h1>
        <p style="color:#8b92a5;margin:4px 0 20px">Weekly AI Forecast Report — {now}</p>
        <div style="background:#1e2235;border-radius:6px;padding:10px 14px;margin-bottom:16px;color:#8b92a5;font-size:12px">
            This is a store-wide forecast (not per-product) — sales_data.csv
            no longer has product-level detail, only monthly totals.
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
            <div style="background:#1e2235;border-radius:8px;padding:14px;text-align:center">
                <div style="color:#8b92a5;font-size:11px">FORECAST REVENUE (90d)</div>
                <div style="color:#ffffff;font-size:22px;font-weight:700">£{forecast['predicted_revenue_90_days_gbp']:,.0f}</div>
            </div>
            <div style="background:#1e2235;border-radius:8px;padding:14px;text-align:center">
                <div style="color:#8b92a5;font-size:11px">FORECAST UNITS (90d)</div>
                <div style="color:#ffffff;font-size:22px;font-weight:700">{int(forecast['predicted_units_90_days']):,}</div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
            <div style="background:#1e2235;border-radius:8px;padding:14px;text-align:center">
                <div style="color:#8b92a5;font-size:11px">REVENUE TO DATE</div>
                <div style="color:#ffffff;font-size:18px;font-weight:700">£{forecast['total_revenue_to_date_gbp']:,.0f}</div>
            </div>
            <div style="background:#1e2235;border-radius:8px;padding:14px;text-align:center">
                <div style="color:#8b92a5;font-size:11px">MONTHS OF HISTORY</div>
                <div style="color:#ffffff;font-size:18px;font-weight:700">{int(forecast['months_of_history'])}</div>
            </div>
        </div>
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

        with open('outputs/store_demand_forecast.csv', 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename='seamark_store_demand_forecast.csv')
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
        forecast = load_forecast()
        if forecast is not None:
            email_ok = send_email_report(forecast)

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
