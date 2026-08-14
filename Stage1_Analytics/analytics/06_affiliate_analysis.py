# ===
# 06_affiliate_analysis.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# Created: June 2026
# ===
#
# WHY I BUILT THIS:
# We are actively recruiting affiliates across multiple countries
# as part of our growth strategy. I needed a clear picture of
# where our affiliates are coming from, which programmes they
# are joining, and which signup channels are working best.
#
# This helps me decide where to focus recruitment efforts —
# for example if most affiliates are coming from one country
# but we want coverage in another, that tells me where to
# spend time on outreach.
#
# DATA SOURCE:
# Exported from UpPromote affiliate dashboard — June 2026.
# Contains all active and pending affiliates on the programme.
#
# WHAT I PLAN TO ADD NEXT:
# - Revenue generated per affiliate
# - Conversion rate per affiliate
# - Time from signup to first referral
# ==

import pandas as pd
import matplotlib.pyplot as plt

# Load affiliate export from UpPromote
affiliate_data = pd.read_csv('../raw_data/affiliate_data.csv')

print(f"Loaded {len(affiliate_data)} affiliates for analysis")


# --
# AFFILIATE OVERVIEW
# --
# Printing the full list first to sense-check the data before
# running any aggregations — caught a duplicate entry this way
# in an earlier run which I removed from the CSV manually
# ---

print("\n=== FULL AFFILIATE LIST ===")
print(affiliate_data[[
    'first_name',
    'last_name',
    'country',
    'program',
    'signup_source'
]].to_string())


# ----
# BREAKDOWN BY KEY DIMENSIONS
# ---

print("\n=== AFFILIATES BY COUNTRY ===")
country_breakdown = affiliate_data['country'].value_counts()
print(country_breakdown)

print("\n=== AFFILIATES BY SIGNUP SOURCE ===")
source_breakdown = affiliate_data['signup_source'].value_counts()
print(source_breakdown)
# This tells me which recruitment channel is most effective
# so I know where to focus outreach going forward

print("\n=== AFFILIATES BY PROGRAMME ===")
program_breakdown = affiliate_data['program'].value_counts()
print(program_breakdown)


# -----
# QUICK INSIGHTS
# ----
# Pulling out the top values automatically so I do not have
# to read through the tables every time I run this
# ---

top_country = country_breakdown.index[0]
top_source = source_breakdown.index[0]
top_program = program_breakdown.index[0]

print(f"\n=== KEY INSIGHTS ===")
print(f"Largest affiliate country: {top_country} ({country_breakdown.iloc[0]} affiliates)")
print(f"Most effective signup source: {top_source} ({source_breakdown.iloc[0]} affiliates)")
print(f"Most popular programme: {top_program} ({program_breakdown.iloc[0]} affiliates)")
print(f"\nTotal affiliates on programme: {len(affiliate_data)}")


# ---
# VISUALISATION
# -
# Two charts side by side — country distribution and signup
# source. These go into the monthly affiliate recruitment
# review to track whether outreach efforts are working.
#
# Steelblue for country (geographic/neutral)
# Gold/green for signup source (matches Seamark brand)
# -

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Chart 1 — Country distribution
country_breakdown.plot(
    kind='bar',
    ax=axes[0],
    color='steelblue',
    edgecolor='navy'
)
axes[0].set_title('Affiliates by Country', fontsize=12)
axes[0].set_xlabel('Country')
axes[0].set_ylabel('Number of Affiliates')
axes[0].tick_params(axis='x', rotation=45)

# Chart 2 — Signup source
source_breakdown.plot(
    kind='bar',
    ax=axes[1],
    color='gold',
    edgecolor='darkgreen'
)
axes[1].set_title('Affiliates by Signup Source', fontsize=12)
axes[1].set_xlabel('Signup Channel')
axes[1].set_ylabel('Number of Affiliates')
axes[1].tick_params(axis='x', rotation=45)

plt.suptitle('Seamark Global Innovations — Affiliate Programme Analysis', fontsize=13)
plt.tight_layout()
plt.savefig('../outputs/affiliate_analysis.png')

print("\nChart saved to outputs/affiliate_analysis.png")
print("Run this monthly to track recruitment progress across countries and channels")
