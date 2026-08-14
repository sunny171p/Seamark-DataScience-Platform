# save as: capture_dashboard.py

import time
import os
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

try:
    from PIL import Image
except ImportError:
    raise SystemExit(
        "This script needs Pillow to stitch screenshots together.\n"
        "Install it with:  pip install Pillow"
    )

os.makedirs("assets", exist_ok=True)

options = Options()
options.add_argument("--window-size=1400,2000")
# Remove headless so Streamlit sidebar loads properly
driver = webdriver.Chrome(options=options)


def full_page_screenshot(driver, filename):
    """
    Earlier attempts tried to make the WHOLE page fit in one shot by
    either emulating a taller viewport (unreliable outside headless
    mode) or resizing the window to the page's "real" height (which
    depended on correctly detecting which element does the actual
    scrolling — that detection was wrong, so the window never grew).

    This takes a different, more robust approach: it directly tests
    what actually moves when you try to scroll it (rather than reading
    CSS properties and guessing), scrolls through the page in steps
    equal to one viewport's height, takes a normal screenshot at each
    step, and stitches them into one tall image with Pillow. This works
    no matter what mechanism the page uses internally to scroll,
    because it's driven by observed behavior, not assumptions about
    Streamlit's DOM/CSS structure.
    """
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    scroll_info = driver.execute_script("""
        function findScrollTarget() {
            var startY = window.scrollY;
            window.scrollBy(0, 50);
            var windowMoved = window.scrollY !== startY;
            window.scrollTo(0, startY);
            if (windowMoved) {
                return {type: 'window'};
            }
            var all = document.querySelectorAll('*');
            var best = null;
            var bestScrollable = 0;
            for (var i = 0; i < all.length; i++) {
                var el = all[i];
                var scrollable = el.scrollHeight - el.clientHeight;
                if (scrollable > 50) {
                    var prevTop = el.scrollTop;
                    el.scrollTop = prevTop + 50;
                    var didMove = el.scrollTop !== prevTop;
                    el.scrollTop = prevTop;
                    if (didMove && scrollable > bestScrollable) {
                        bestScrollable = scrollable;
                        best = el;
                    }
                }
            }
            if (best) {
                best.setAttribute('data-capture-scroll-target', 'true');
                return {type: 'element', scrollHeight: best.scrollHeight, clientHeight: best.clientHeight};
            }
            return {type: 'none'};
        }
        return findScrollTarget();
    """)

    if scroll_info["type"] == "none":
        # Nothing on the page actually scrolls — it already fits in
        # one screenshot.
        driver.save_screenshot(filename)
        return

    if scroll_info["type"] == "window":
        total_height = driver.execute_script(
            "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
        )
        viewport_height = driver.execute_script("return window.innerHeight")
        scroll_js = "window.scrollTo(0, {y});"
        reset_js = "window.scrollTo(0, 0);"
    else:
        total_height = scroll_info["scrollHeight"]
        viewport_height = scroll_info["clientHeight"]
        scroll_js = "document.querySelector('[data-capture-scroll-target]').scrollTop = {y};"
        reset_js = "document.querySelector('[data-capture-scroll-target]').scrollTop = 0;"

    driver.execute_script(reset_js)
    time.sleep(0.5)

    shots = []
    y = 0
    while y < total_height:
        driver.execute_script(scroll_js.format(y=y))
        time.sleep(0.4)
        png_bytes = driver.get_screenshot_as_png()
        shots.append(Image.open(io.BytesIO(png_bytes)))
        y += viewport_height

    combined_width = shots[0].width
    combined_height = sum(shot.height for shot in shots)
    combined = Image.new("RGB", (combined_width, combined_height), "white")

    offset = 0
    for shot in shots:
        combined.paste(shot, (0, offset))
        offset += shot.height

    combined.save(filename)
    driver.execute_script(reset_js)


def find_sidebar_label(driver, page_name):
    """
    FIX: the old approach used XPath contains(., page_name), which does
    a substring match — "Overview" matches both "📊 Overview" AND
    "💷 Sales Overview" since the word "Overview" is contained inside
    both. It happened to pick the right one purely by DOM order luck.

    This instead strips the leading emoji from each label's text and
    compares the REMAINING text exactly against page_name, so "Overview"
    can only ever match the label that says exactly "Overview".
    """
    labels = driver.find_elements(By.TAG_NAME, "label")
    for label in labels:
        text = label.text.strip()
        parts = text.split(" ", 1)
        remainder = parts[1].strip() if len(parts) > 1 else text
        if remainder == page_name:
            return label
    return None


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
        label = find_sidebar_label(driver, page_name)
        if label:
            label.click()
            time.sleep(4)  # wait for page to render
            full_page_screenshot(driver, filename)
            print(f"✅ Saved: {filename}")
        else:
            print(f"❌ Could not find: {page_name}")
    except Exception as e:
        print(f"❌ Error on {page_name}: {e}")

driver.quit()
print("\nAll screenshots captured. Check your assets/ folder.")