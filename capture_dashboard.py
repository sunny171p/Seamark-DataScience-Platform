# save as: capture_dashboard.py

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

os.makedirs("assets", exist_ok=True)

options = Options()
options.add_argument("--window-size=1400,900")
# Remove headless so Streamlit sidebar loads properly
driver = webdriver.Chrome(options=options)

driver.get("http://localhost:8501")
time.sleep(5)  # wait for full load

pages = [
    "Overview",
    "Sales Overview",
    "Product Analytics",
    "Pricing Audit",
    "Traffic & Funnel",
    "Competitive Pricing",
    "Affiliate Programme",
    "AI Forecast",
    "Alerts",
]

filenames = [
    "assets/01_overview.png",
    "assets/02_sales_overview.png",
    "assets/03_product_analytics.png",
    "assets/04_pricing_audit.png",
    "assets/05_traffic_funnel.png",
    "assets/06_competitive_pricing.png",
    "assets/07_affiliate_programme.png",
    "assets/08_ai_forecast.png",
    "assets/09_alerts.png",
]

for page_name, filename in zip(pages, filenames):
    try:
        # Find and click the sidebar radio button by label text
        elements = driver.find_elements(By.XPATH, 
            f"//label[contains(., '{page_name}')]")
        if elements:
            elements[0].click()
            time.sleep(4)  # wait for page to render
            driver.save_screenshot(filename)
            print(f"✅ Saved: {filename}")
        else:
            print(f"❌ Could not find: {page_name}")
    except Exception as e:
        print(f"❌ Error on {page_name}: {e}")

driver.quit()
print("\nAll screenshots captured. Check your assets/ folder.")
