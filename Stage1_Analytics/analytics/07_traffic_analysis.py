# ==
# 07_traffic_analysis.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ==
#
# WHY I BUILT THIS:
# 03_funnel_analysis.py already told me people drop off before
# reaching checkout, but it did not tell me WHY they never really
# get going in the first place. Shopify Analytics also gives you
# a page-load report and a landing-page report, and I had never
# actually pulled them in — I wanted to see where people land and
# how far they actually browse before leaving.
#
# DATA SOURCES (all Shopify Analytics exports, 365 day window):
# - sessions_by_month_365d.csv     (sessions, visitors, checkout)
# - traffic_sources_365d.csv       (where sessions came from)
# - product_page_views_365d.csv    (page loads per product page)
# - web_performance_page_loads_365d.csv  (page loads, every page)
# - top_landing_pages_365d.csv     (first page of the session)
#
# WHAT I FOUND:
# Almost all of our traffic is direct (no referrer) and almost
# all of it lands on the homepage rather than a product or
# collection page. Combined with how few page loads go to actual
# product pages, that reads as "people are typing in the URL or
# clicking a raw link, landing on the homepage, and not browsing
# very far" — a discovery problem, not just a checkout problem.
# ==

import pandas as pd
import matplotlib.pyplot as plt

sessions   = pd.read_csv('../raw_data/sessions_by_month_365d.csv')
sources    = pd.read_csv('../raw_data/traffic_sources_365d.csv')
page_views = pd.read_csv('../raw_data/product_page_views_365d.csv')
page_loads = pd.read_csv('../raw_data/web_performance_page_loads_365d.csv')
landing    = pd.read_csv('../raw_data/top_landing_pages_365d.csv')

print(f"Loaded {len(sessions)} months of sessions, {len(sources)} traffic sources, "
      f"{len(page_loads)} tracked pages, {len(landing)} landing pages")


# --
# SESSION / CHECKOUT TOTALS
# --
# Summed across the 365 day window rather than averaged month to
# month — averaging four monthly percentages equally would let a
# quiet 16-session month count the same as a 197-session month.
# --

total_sessions = int(sessions['Sessions'].sum())
total_visitors = int(sessions['Online store visitors'].sum())
total_checkout = int(sessions['Sessions that reached checkout'].sum())
checkout_rate  = round(total_checkout / total_sessions * 100, 2) if total_sessions else 0.0

# Shopify's own "Conversion rate" column, not a rate I derived — this is
# the real, completed-purchase conversion rate and it reads 0% every
# single month, which matches the store having taken zero real orders.
real_conversion_rate = round(sessions['Conversion rate'].mean() * 100, 2)

print("\n=== SESSION TOTALS (365 DAYS) ===")
print(f"Total sessions        : {total_sessions}")
print(f"Online store visitors : {total_visitors}")
print(f"Reached checkout      : {total_checkout} ({checkout_rate}% of sessions)")
print(f"Real conversion rate  : {real_conversion_rate}% (Shopify's own figure — nobody has completed a purchase yet)")


# --
# TRAFFIC SOURCE MIX
# --
# I wanted to know how reliant we are on people already knowing
# the URL versus actually being found through search or an
# affiliate link.
# --

sources_sorted = sources.sort_values('Sessions', ascending=False)
direct_sessions = int(sources[sources['Referrer source'] == 'direct']['Sessions'].sum())
direct_pct = round(direct_sessions / sources['Sessions'].sum() * 100, 1)
search_sessions = int(sources[sources['Referrer source'] == 'search']['Sessions'].sum())

print("\n=== TRAFFIC SOURCES ===")
print(sources_sorted.to_string(index=False))
print(f"\n{direct_pct}% of sessions are direct (no referrer at all) — only {search_sessions} came from search.")
if direct_pct > 70:
    print("That's a real weakness: almost nobody is finding the store on their own right now,")
    print("which means growth depends on whoever already has the link, not on search or ads.")


# --
# LANDING PAGE CONCENTRATION
# --
# Where does the session actually start? If almost everyone lands
# on the homepage instead of a product or collection page, none of
# the product-level marketing (ads, affiliate links to a specific
# item) is actually landing people where it should.
# --

home_landing = int(landing[landing['Landing page path'] == '/']['Sessions'].sum())
landing_total = int(landing['Sessions'].sum())
home_landing_pct = round(home_landing / landing_total * 100, 1) if landing_total else 0.0

print("\n=== TOP LANDING PAGES ===")
print(landing.sort_values('Sessions', ascending=False).head(10).to_string(index=False))
print(f"\n{home_landing_pct}% of sessions land on the homepage first.")


# --
# PAGE ENGAGEMENT DEPTH
# --
# web_performance_page_loads_365d.csv logs a load every time any
# page renders, so splitting it by path prefix shows how far
# people actually browse once they're on the site — homepage vs
# collection grid vs an actual product page.
# --

total_loads = int(page_loads['Page loads'].sum())
home_loads = int(page_loads[page_loads['Page path'] == '/']['Page loads'].sum())
product_loads = int(page_loads[page_loads['Page path'].str.startswith('/products/')]['Page loads'].sum())
collection_loads = int(page_loads[page_loads['Page path'].str.startswith('/collections/')]['Page loads'].sum())

home_load_pct = round(home_loads / total_loads * 100, 1) if total_loads else 0.0
product_load_pct = round(product_loads / total_loads * 100, 1) if total_loads else 0.0
collection_load_pct = round(collection_loads / total_loads * 100, 1) if total_loads else 0.0

print("\n=== PAGE ENGAGEMENT DEPTH ===")
print(f"Total page loads tracked : {total_loads}")
print(f"Homepage                 : {home_loads} ({home_load_pct}%)")
print(f"Collection pages         : {collection_loads} ({collection_load_pct}%)")
print(f"Individual product pages : {product_loads} ({product_load_pct}%)")
if product_load_pct < 15:
    print("Only a small slice of page loads ever reach a product page — most visits")
    print("don't get past the homepage or a collection grid, let alone reach checkout.")

top_pages = page_loads.sort_values('Page loads', ascending=False).head(10)


# --
# SAVE A CLEAN SUMMARY FOR THE DASHBOARD
# --
# Everything above is a real, derived number — the dashboard reads
# this file instead of re-typing any of these figures by hand.
# --

summary = pd.DataFrame([{
    'total_sessions': total_sessions,
    'total_visitors': total_visitors,
    'total_checkout': total_checkout,
    'checkout_rate_pct': checkout_rate,
    'real_conversion_rate_pct': real_conversion_rate,
    'direct_traffic_pct': direct_pct,
    'search_sessions': search_sessions,
    'home_landing_pct': home_landing_pct,
    'home_pageload_pct': home_load_pct,
    'collection_pageload_pct': collection_load_pct,
    'product_pageload_pct': product_load_pct,
    'total_pageloads_tracked': total_loads,
}])
summary.to_csv('../../outputs/traffic_analysis_summary.csv', index=False)
top_pages.to_csv('../../outputs/traffic_top_pages.csv', index=False)
print("\nSummary saved to outputs/traffic_analysis_summary.csv")
print("Top pages saved to outputs/traffic_top_pages.csv")


# --
# VISUALISATION
# --
# One chart showing where page loads actually go — homepage,
# collections, products, everything else. Makes the "people don't
# get past the homepage" finding obvious at a glance.
# --

breakdown = pd.Series({
    'Homepage': home_loads,
    'Collections': collection_loads,
    'Products': product_loads,
    'Other pages': total_loads - home_loads - collection_loads - product_loads,
})

fig, ax = plt.subplots(figsize=(9, 6))
breakdown.plot(kind='bar', color='gold', edgecolor='darkgreen', ax=ax)
ax.set_title('Where Page Loads Actually Go — Seamark Global Innovations', fontsize=13)
ax.set_xlabel('Page type')
ax.set_ylabel('Page loads (365 days)')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('../outputs/traffic_analysis.png')

print("\nChart saved to outputs/traffic_analysis.png")
