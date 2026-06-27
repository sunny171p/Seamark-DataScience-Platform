# ==
# 03_funnel_analysis.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ==
#
# WHY I BUILT THIS:
# I noticed our traffic numbers looked decent but sales were not
# reflecting that. I wanted to understand exactly where in the
# journey customers were dropping off — were they not reaching
# checkout at all, or reaching it and not completing?
#
# DATA SOURCE:
# Exported directly from Shopify Analytics > Sessions by month
# covering the last 365 days. Downloaded as CSV manually.
#
# WHAT I FOUND:
# The biggest drop-off is between landing and reaching checkout.
# Very few people who reach checkout actually abandon it —
# which tells me the problem is earlier in the funnel (product
# pages, trust signals, pricing) not the checkout itself.
# ==

import pandas as pd
import matplotlib.pyplot as plt

# Load 12 months of session data exported from Shopify Analytics
sessions = pd.read_csv('../raw_data/sessions_by_month_365d.csv')

print(f"Loaded {len(sessions)} months of session data")
print("\n=== RAW FUNNEL DATA ===")
print(sessions.to_string())


# --
# DROP-OFF CALCULATIONS
# --
# I added Checkout Rate myself — Shopify does not show this
# directly. It tells me what percentage of all visitors
# actually made it to the checkout page each month.
# --

sessions['Checkout Rate %'] = (
    sessions['Sessions that reached checkout'] /
    sessions['Sessions'] * 100
).round(1)

# Also calculating how many sessions were lost before checkout
# This is the number I want to reduce through CRO work
sessions['Lost Before Checkout'] = (
    sessions['Sessions'] - sessions['Sessions that reached checkout']
)

print("\n=== DROP-OFF ANALYSIS BY MONTH ===")
print(sessions[[
    'Month',
    'Sessions',
    'Sessions that reached checkout',
    'Checkout Rate %',
    'Lost Before Checkout',
    'Conversion rate'
]].to_string())

# Quick summary — which month had the best checkout rate?
best_month = sessions.loc[sessions['Checkout Rate %'].idxmax(), 'Month']
worst_month = sessions.loc[sessions['Checkout Rate %'].idxmin(), 'Month']
print(f"\nBest checkout rate month: {best_month}")
print(f"Worst checkout rate month: {worst_month}")


# --
# VISUALISATION
# --
# Overlapping bars show the funnel visually — the gap between
# blue and orange is the drop-off I am trying to close.
# Steelblue and orange chosen for clear contrast on reports.
# --

fig, ax = plt.subplots(figsize=(10, 6))

x = sessions['Month']

ax.bar(x, sessions['Sessions'],
       label='Total Sessions',
       color='steelblue',
       alpha=0.9)

ax.bar(x, sessions['Sessions that reached checkout'],
       label='Reached Checkout',
       color='orange',
       alpha=0.9)

ax.set_title('Seamark Conversion Funnel — 12 Month View', fontsize=14)
ax.set_xlabel('Month')
ax.set_ylabel('Number of Sessions')
ax.legend()

# Rotate month labels so they do not overlap
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('../outputs/funnel_analysis.png')

print("\nChart saved to outputs/funnel_analysis.png")
print("Review the chart to identify which months had the largest drop-off gaps")
