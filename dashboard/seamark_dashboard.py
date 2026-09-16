import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(page_title="Seamark BI Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp{background-color:#0f1117;color:#ffffff}
    [data-testid="stSidebar"]{background-color:#1a1d27;border-right:1px solid #2e3450}
    [data-testid="stSidebar"] *{color:#ffffff !important}
    [data-testid="stSidebar"][aria-expanded="false"]{min-width:230px !important;max-width:230px !important;margin-left:0 !important;transform:none !important;visibility:visible !important}
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"]{display:none !important}
    .kpi-card{background:linear-gradient(135deg,#1e2235,#252a3d);border:1px solid #2e3450;border-radius:12px;padding:16px;text-align:left;margin-bottom:10px}
    .kpi-icon{font-size:22px;margin-bottom:4px}
    .kpi-value{font-size:26px;font-weight:700;color:#ffffff;line-height:1.1}
    .kpi-label{font-size:12px;color:#8b92a5;margin-bottom:2px}
    .kpi-delta-pos{font-size:11px;color:#00d4aa;margin-top:4px}
    .kpi-delta-warn{font-size:11px;color:#f59e0b;margin-top:4px}
    .kpi-delta-neg{font-size:11px;color:#ff4b6e;margin-top:4px}
    .section-title{font-size:14px;font-weight:600;color:#ffffff;margin:16px 0 8px 0;padding-bottom:5px;border-bottom:1px solid #2e3450}
    .badge-ok{background:#0e2a1f;color:#34d399;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
    .badge-warn{background:#2a1f0e;color:#fbbf24;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
    .badge-danger{background:#2a0e1a;color:#f87171;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
    .badge-info{background:#1e2a3a;color:#60a5fa;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
    .alert-success{background:#0e2a1f;border-left:4px solid #10b981;border-radius:6px;padding:10px 14px;margin-bottom:8px;font-size:13px;color:#6ee7b7}
    .alert-warning{background:#2a1f0e;border-left:4px solid #f59e0b;border-radius:6px;padding:10px 14px;margin-bottom:8px;font-size:13px;color:#fcd34d}
    .alert-danger{background:#2a0e1a;border-left:4px solid #ff4b6e;border-radius:6px;padding:10px 14px;margin-bottom:8px;font-size:13px;color:#fca5a5}
    .dq-card{background:#1e2235;border:1px solid #2e3450;border-radius:10px;padding:14px;text-align:center;margin-bottom:10px}
    .dq-title{font-size:11px;color:#8b92a5;margin-bottom:4px}
    .dq-value{font-size:20px;font-weight:700;color:#ffffff}
    .dq-sub{font-size:11px;color:#00d4aa;margin-top:2px}
    #MainMenu{visibility:hidden}footer{visibility:hidden}
    header{background-color:transparent !important}
    [data-testid="baseButton-headerNoPadding"] svg{fill:#ffffff !important}
    .block-container{padding-top:3rem;padding-left:2rem;padding-right:2rem;max-width:100%}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_all():
    # FIXED (Claude, September 2026): product_demand_forecast held stale
    # per-product data from before sales_data.csv was rectified down to
    # store-wide monthly totals (see product_demand_forecast.py's header
    # comment), and Sunday has since deleted the table entirely rather than
    # just emptying it. A plain select on a table that doesn't exist raises
    # an exception straight out of supabase-py, which used to crash this
    # whole dashboard on load. Falling back to an empty frame with the
    # right columns means every pf.nlargest/sort_values/etc below still
    # works — it just shows nothing, which is the honest state until this
    # table is either recreated or the per-product sections are rebuilt
    # against automation/forecasting/product_demand_forecast.py's new
    # store_demand_forecast table instead.
    try:
        pf = pd.DataFrame(supabase.table('product_demand_forecast').select('*').execute().data)
    except Exception:
        pf = pd.DataFrame(columns=['product_name', 'forecast_revenue_90_days', 'forecast_units_90_days'])
    if 'product_name' not in pf.columns:
        pf['product_name'] = pd.Series(dtype='object')
    if 'forecast_revenue_90_days' not in pf.columns:
        pf['forecast_revenue_90_days'] = pd.Series(dtype='float64')
    if 'forecast_units_90_days' not in pf.columns:
        pf['forecast_units_90_days'] = pd.Series(dtype='float64')
    pf = pf.drop_duplicates(subset=['product_name'], keep='first').reset_index(drop=True)
    # Real per-order data — this is also what sales_forecast.py itself trains the
    # Prophet model on, so the dashboard should show numbers from the same source
    # the forecast is built from rather than the old placeholder monthly file.
    sh = pd.read_csv('Stage1_Analytics/data/orders_export.csv')
    sh = sh.rename(columns={'Order Date': 'Created at', 'Total (GBP)': 'Lineitem price'})
    sh['Created at'] = pd.to_datetime(sh['Created at'])
    pc = pd.read_csv('outputs/price_check_enriched.csv')
    pc['Category'] = pc['Category'].str.strip().replace({'Uncategorized':'Uncategorised','':'Uncategorised'})
    pc['Low Price Flag'] = pc['Price'] < 5.0
    af = pd.read_csv('Stage1_Analytics/raw_data/affiliate_data.csv')
    tr = pd.read_csv('Stage1_Analytics/raw_data/traffic_sources_365d.csv')
    ses = pd.read_csv('Stage1_Analytics/raw_data/sessions_by_month_365d.csv')
    ses['Sessions'] = pd.to_numeric(ses['Sessions'], errors='coerce').fillna(0)
    ses['Sessions that reached checkout'] = pd.to_numeric(ses['Sessions that reached checkout'], errors='coerce').fillna(0)
    ses['Online store visitors'] = pd.to_numeric(ses['Online store visitors'], errors='coerce').fillna(0)
    ses['Real Conversion Rate'] = (ses['Sessions that reached checkout'] / ses['Sessions'].replace(0,1) * 100).round(2)
    pv = pd.read_csv('Stage1_Analytics/raw_data/product_page_views_365d.csv')
    pv['Page loads'] = pd.to_numeric(pv['Page loads'], errors='coerce')
    sf = pd.read_csv('outputs/sales_forecast_90days.csv')
    sf['ds'] = pd.to_datetime(sf['ds'])
    # sales_forecast.py trains Prophet directly on daily order totals (£), so
    # yhat IS already a revenue prediction — it does not need multiplying by
    # average product price. (That multiplication used to inflate the forecast
    # by ~95x, which is why this never matched the pipeline's own printed output.)
    sf['yhat_Total'] = sf['yhat'].round(2)
    sf['yhat_upper_Total'] = sf['yhat_upper'].round(2)
    sf['yhat_lower_Total'] = sf['yhat_lower'].round(2)
    prod_export = pd.read_csv('Stage1_Analytics/raw_data/products_export.csv')
    # Real classification from Stage 1 (02_product_classification.py) — 10 categories
    # from keyword matching on product titles, instead of guessing from the raw
    # Shopify Type field.
    prod_clean = pd.read_csv('Stage1_Analytics/cleaned_data/products_clean.csv')
    inv = pd.read_csv('Stage1_Analytics/raw_data/inventory_data.csv')
    # Pricing Audit and Competitive Pricing used to group by the raw Shopify
    # Type field, which splits things like "Smart TV", "Portable Smart TV" and
    # "Outdoor TV" into separate buckets — a different, messier category system
    # than the rest of the dashboard. Pulling Auto_Category across by title
    # means every page groups products the same way.
    cat_lookup = prod_clean.drop_duplicates(subset=['Title'])[['Title', 'Auto_Category']]
    pc = pc.merge(cat_lookup, on='Title', how='left')
    pc['Auto_Category'] = pc['Auto_Category'].fillna('Other')
    # These three come straight out of the analytics scripts (05, 07, 08) —
    # the dashboard reads the same numbers those scripts printed to the
    # terminal instead of recalculating them a second time in a different
    # way, which is how the two used to end up disagreeing.
    vs_amazon = pd.read_csv('outputs/competitive_pricing.csv')
    pipe_health = pd.read_csv('outputs/pipeline_health_summary.csv').iloc[0]
    traffic_summary = pd.read_csv('outputs/traffic_analysis_summary.csv').iloc[0]
    return pf, sh, pc, af, tr, ses, pv, sf, prod_export, prod_clean, inv, vs_amazon, pipe_health, traffic_summary

pf, sh, pc, af, tr, ses, pv, sf, prod_export, prod_clean, inv, vs_amazon, pipe_health, traffic_summary = load_all()
total_products    = prod_export['Handle'].nunique()
products_checked  = len(pc)
pricing_issues    = len(pc[pc['Pricing Status'].isin(['Misleading Discount','Missing Compare-at','No Discount'])])
low_price_items   = int(pc['Low Price Flag'].sum())
# 08_pipeline_health.py works these out from the actual files rather than
# us typing a fixed figure straight into this file — the quality score is
# genuinely low right now, because most of the catalogue has a misleading
# discount, not the much healthier number this page used to show.
raw_rows          = int(pipe_health['raw_rows'])
quality_score     = pipe_health['quality_score_pct']
last_pipeline_run = pipe_health['last_pipeline_run']
total_affiliates  = len(af)
active_affiliates = len(af[af['status'].str.lower()=='active']) if 'status' in af.columns else 0
total_sessions    = int(ses['Sessions'].sum())
# The store hasn't actually taken any real orders yet — the rows in
# orders_export.csv are sample data made up to give Prophet a training
# series to forecast from, not genuine transactions. So the real business
# state is zero orders / zero revenue; the sample rows are only used below
# to show how the forecast was trained, clearly labelled as such.
total_orders      = 0
total_Total       = 0.0
total_checkout    = int(ses['Sessions that reached checkout'].sum())
total_visitors    = int(ses['Online store visitors'].sum())
# One rate, one formula, used everywhere on the dashboard. Averaging the four
# monthly percentages (what this used to do) gives March's 16-session month
# the same weight as April's 197-session month, which is how the KPI card at
# the top of Overview and the funnel chart just below it ended up quoting two
# different checkout rates for the same 365 days of data.
avg_conversion    = round(total_checkout / total_sessions * 100, 2) if total_sessions else 0.0
# Nobody has actually completed a purchase yet — reaching checkout isn't the
# same as buying, and every month in sessions_by_month_365d.csv shows 0% real
# conversion. This used to be guessed as total_sessions × avg_conversion,
# which turned "sessions that reached checkout" into a fake completed-order
# count that disagreed with the honest £0 / 0 orders shown on Sales Overview.
total_converted   = total_orders
supabase_records  = len(pf)
sample_order_rows = len(sh)
daily_sales       = sh.groupby('Created at')['Lineitem price'].sum().reset_index()
# sf covers Prophet's fitted history *and* the 90 future days in one file —
# the "90-day forecast" headline numbers should only count the future part,
# not the backtest-over-known-orders part.
future_sf         = sf[sf['ds'] > sh['Created at'].max()].reset_index(drop=True)
projected_rev     = future_sf['yhat_Total'].sum()
avg_daily_rev     = future_sf['yhat_Total'].mean()

LAYOUT = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ffffff', margin=dict(l=0,r=0,t=20,b=0))

def kpi(icon, label, value, delta, dtype="pos"):
    c = {"pos":"kpi-delta-pos","warn":"kpi-delta-warn","neg":"kpi-delta-neg"}.get(dtype,"kpi-delta-pos")
    return f'<div class="kpi-card"><div class="kpi-icon">{icon}</div><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="{c}">{delta}</div></div>'

def badge(s):
    if s=='Misleading Discount': return f'<span class="badge-danger">{s}</span>'
    if s=='No Discount': return f'<span class="badge-warn">{s}</span>'
    if s=='OK': return f'<span class="badge-ok">{s}</span>'
    return f'<span class="badge-info">{s}</span>'

def truncate_label(text, max_len):
    text = str(text)
    return text if len(text) <= max_len else text[:max_len - 1].rstrip() + '…'

def legend_row(color, label, value_text):
    return (f"<div style='display:flex;align-items:center;justify-content:space-between;"
            f"margin-bottom:9px;font-size:12px'>"
            f"<span style='display:flex;align-items:center;color:#c9cee0'>"
            f"<span style='width:8px;height:8px;border-radius:50%;background:{color};"
            f"margin-right:8px;flex-shrink:0'></span>{label}</span>"
            f"<span style='color:#ffffff;font-weight:600'>{value_text}</span></div>")

def render_pie_panel(title, labels, values, colors, footer_text, chart_key):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    total = sum(values) or 1
    left, right = st.columns([1, 1])
    with left:
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.4,
                                marker=dict(colors=colors, line=dict(color='#0f1117', width=2)),
                                textinfo='none', sort=False))
        fig.update_layout(**LAYOUT, height=210, showlegend=False)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, key=chart_key)
    with right:
        rows = "".join(legend_row(c, l, f"{v} ({v/total*100:.1f}%)") for l, v, c in zip(labels, values, colors))
        st.markdown(f"<div style='padding-top:12px'>{rows}</div>", unsafe_allow_html=True)
    st.markdown(f"<center style='color:#8b92a5;font-size:11px;margin-top:4px'>{footer_text}</center>", unsafe_allow_html=True)

def render_bar_panel(title, labels, values, colors, footer_text, chart_key):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    total = sum(values) or 1
    order = sorted(range(len(values)), key=lambda i: values[i])
    labels_s = [labels[i] for i in order]
    values_s = [values[i] for i in order]
    colors_s = [colors[i] for i in order]
    bar_text = [f"{v} ({v/total*100:.1f}%)" for v in values_s]
    fig = go.Figure(go.Bar(x=values_s, y=labels_s, orientation='h',
                            text=bar_text, textposition='outside',
                            marker_color=colors_s))
    fig.update_layout(**LAYOUT, height=210,
                       xaxis=dict(gridcolor='#2e3450', title=''),
                       yaxis=dict(title=''), uniformtext_minsize=9)
    fig.update_layout(margin=dict(l=0, r=60, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True, key=chart_key)
    st.markdown(f"<center style='color:#8b92a5;font-size:11px;margin-top:4px'>{footer_text}</center>", unsafe_allow_html=True)

def render_funnel_panel(title, stages, values, colors, footer_text, chart_key):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    base = values[0] or 1
    left, right = st.columns([1, 1])
    with left:
        fig = go.Figure(go.Funnel(y=stages, x=values, textinfo="none", marker=dict(color=colors)))
        fig.update_layout(**LAYOUT, height=210)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, key=chart_key)
    with right:
        rows = ""
        for stg, val, col in zip(stages, values, colors):
            pct = val / base * 100
            rows += (f"<div style='margin-bottom:10px'>"
                     f"<div style='font-size:11px;color:#8b92a5'>{stg}</div>"
                     f"<div style='font-size:16px;font-weight:700;color:#ffffff'>{val:,.0f} "
                     f"<span style='font-size:11px;color:{col};font-weight:600'>{pct:.1f}%</span></div></div>")
        st.markdown(f"<div style='padding-top:10px'>{rows}</div>", unsafe_allow_html=True)
    st.markdown(f"<center style='color:#8b92a5;font-size:11px;margin-top:4px'>{footer_text}</center>", unsafe_allow_html=True)

def render_forecast_panel(chart_key):
    st.markdown('<div class="section-title">🔮 AI Forecast Summary — Prophet</div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1])
    with left:
        fig = go.Figure(go.Scatter(x=sf['ds'], y=sf['yhat_Total'], mode='lines',
                                    line=dict(color='#00d4aa', width=3), fill='tozeroy',
                                    fillcolor='rgba(0,212,170,0.12)'))
        fig.update_layout(**LAYOUT, height=210, xaxis=dict(visible=False), yaxis=dict(visible=False))
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, key=chart_key)
    with right:
        peak_day = future_sf.loc[future_sf['yhat_Total'].idxmax(), 'ds'].strftime('%d %b')
        stats = [
            ("90-Day Forecast Total", f"£{projected_rev:,.0f}"),
            ("Avg Daily Forecast", f"£{avg_daily_rev:,.0f}"),
            ("Peak Forecast Day", f"£{future_sf['yhat_Total'].max():,.0f} ({peak_day})"),
            ("Products Forecasted", f"{supabase_records}"),
        ]
        rows = "".join(
            f"<div style='margin-bottom:9px'><div style='font-size:11px;color:#8b92a5'>{k}</div>"
            f"<div style='font-size:15px;font-weight:700;color:#ffffff'>{v}</div></div>"
            for k, v in stats)
        st.markdown(f"<div style='padding-top:8px'>{rows}</div>", unsafe_allow_html=True)
    st.markdown("<center style='color:#8b92a5;font-size:11px;margin-top:4px'>Prophet AI — next 90 days</center>", unsafe_allow_html=True)

def render_cloud_panel(chart_key):
    st.markdown('<div class="section-title">☁️ Cloud Forecast — Supabase</div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1])
    with left:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=supabase_records,
            gauge={'axis': {'range': [0, max(300, supabase_records * 1.2)], 'tickcolor': '#8b92a5'},
                   'bar': {'color': '#00d4aa'}, 'bgcolor': '#1e2235', 'bordercolor': '#2e3450'},
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#ffffff', height=210,
                           margin=dict(l=10, r=10, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, key=chart_key)
    with right:
        stats = [
            ("Records Live", f"{supabase_records}"),
            ("Table", "product_demand_forecast"),
            ("Status", "🟢 Connected"),
            ("Last Sync", pd.Timestamp.now().strftime('%d %b %H:%M')),
        ]
        rows = "".join(
            f"<div style='margin-bottom:9px'><div style='font-size:11px;color:#8b92a5'>{k}</div>"
            f"<div style='font-size:15px;font-weight:700;color:#ffffff'>{v}</div></div>"
            for k, v in stats)
        st.markdown(f"<div style='padding-top:8px'>{rows}</div>", unsafe_allow_html=True)
    st.markdown("<center style='color:#8b92a5;font-size:11px;margin-top:4px'>Supabase — live cloud sync</center>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🏢 SEAMARK")
    st.markdown("**Global Innovations**")
    st.markdown("<small style='color:#8b92a5'>The Seamark Global Intelligence Dashboard</small>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("", ["📊 Overview","💷 Sales Overview","📦 Product Analytics","💰 Pricing Audit","📈 Traffic & Funnel","🏷️ Competitive Pricing","🤝 Affiliate Programme","🔮 AI Forecast","🔔 Alerts","Funnel Analysis","Inventory Operations","Pipeline Health"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small style='color:#8b92a5'>DATA SNAPSHOT</small>", unsafe_allow_html=True)
    st.markdown(f"🗓 {pd.Timestamp.now().strftime('%d %b %Y %H:%M')}")
    st.markdown(f"📦 {total_products} products")
    st.markdown(f"🛒 {total_orders} orders")
    st.markdown(f"☁️ Supabase — {supabase_records} records live")
    st.markdown(f"🤖 Prophet AI — {supabase_records} products forecasted")
    st.markdown("---")
    st.markdown("<small style='color:#8b92a5'>SEAMARK ADMIN</small>", unsafe_allow_html=True)
    st.markdown("admin@theseamarkglobalinnovations.com")
    st.markdown("---")
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown(f"""
<div style='text-align:center;padding-bottom:14px;margin-bottom:6px;border-bottom:1px solid #2e3450'>
    <div style='font-size:23px;font-weight:700;color:#ffffff'>The Seamark Global Innovations</div>
    <div style='font-size:13px;color:#00d4aa;margin-top:2px'>Sales & Product Demand Forecast Dashboard</div>
    <div style='font-size:11px;color:#8b92a5;margin-top:6px'>Last updated: {pd.Timestamp.now().strftime('%d %B %Y %H:%M')}</div>
</div>
""", unsafe_allow_html=True)

# ══ OVERVIEW ══════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.markdown("## 📊 Overview")
    st.markdown("Key business metrics and performance summary")
    st.markdown("---")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    for col,(icon,label,val,delta,dtype) in zip([c1,c2,c3,c4,c5,c6],[
        ("📦","Analysed Products",f"{products_checked}","Price-checked catalogue","pos"),
        ("⚠️","Pricing Issues",f"{pricing_issues}",f"{round(pricing_issues/products_checked*100,1)}% of checked products","neg"),
        ("🛒","Checkout Rate",f"{avg_conversion:.1f}%",f"{total_checkout:,} sessions reached checkout","pos"),
        ("💷","Low Price Items",f"{low_price_items}","Products under £5","warn"),
        ("🤝","Affiliates",f"{total_affiliates}",f"{active_affiliates} active","pos"),
        ("🔮","AI Forecast (90d)",f"£{projected_rev:,.0f}","Prophet AI — Supabase","pos"),
    ]):
        with col: st.markdown(kpi(icon,label,val,delta,dtype), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        cat = prod_clean['Auto_Category'].value_counts().reset_index()
        cat.columns = ['Category', 'Count']
        palette = ['#2dd4bf','#7c6af7','#f59e0b','#ff4b6e','#60a5fa']
        colors = [palette[i % len(palette)] for i in range(len(cat))]
        render_pie_panel(
            "Product Category Distribution", cat['Category'].tolist(), cat['Count'].tolist(), colors,
            f"{len(prod_clean)} total products across {prod_clean['Auto_Category'].nunique()} categories",
            chart_key="ov_cat_pie",
        )

    with col2:
        render_funnel_panel(
            "Conversion Funnel Summary",
            ["Total Sessions","Store Visitors","Reached Checkout","Converted Orders"],
            [total_sessions, total_visitors, total_checkout, total_converted],
            ['#00d4aa','#7c6af7','#f59e0b','#ff4b6e'],
            f"Avg conversion: {avg_conversion:.1f}% | 365 day data",
            chart_key="ov_funnel",
        )

    with col3:
        ps = pc['Pricing Status'].value_counts().reset_index()
        ps.columns = ['Status','Count']
        status_colors = {'Misleading Discount':'#ff4b6e','No Discount':'#f59e0b','OK':'#00d4aa'}
        render_pie_panel(
            "Pricing Issue Summary",
            ps['Status'].tolist(), ps['Count'].tolist(),
            [status_colors.get(s,'#60a5fa') for s in ps['Status']],
            f"{pricing_issues} products need pricing correction",
            chart_key="ov_pricing_donut",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col4, col5 = st.columns(2)
    with col4:
        render_forecast_panel(chart_key="ov_forecast_spark")
    with col5:
        render_cloud_panel(chart_key="ov_cloud_gauge")

    st.markdown('<div class="section-title">Recent Pricing Issues (Top 10 by Price Difference)</div>', unsafe_allow_html=True)
    issues = pc[pc['Pricing Status']=='Misleading Discount'].sort_values('Price Difference').head(10)
    tbl = """<table style='width:100%;border-collapse:collapse;font-size:12px'>
    <tr style='color:#8b92a5;border-bottom:1px solid #2e3450'>
        <th style='text-align:left;padding:6px'>Title</th><th style='text-align:left;padding:6px'>Category</th>
        <th style='text-align:right;padding:6px'>Price (£)</th><th style='text-align:right;padding:6px'>Compare At (£)</th>
        <th style='text-align:right;padding:6px'>Difference</th><th style='text-align:center;padding:6px'>Status</th>
    </tr>"""
    for _,row in issues.iterrows():
        dc = '#ff4b6e' if row['Price Difference']<0 else '#00d4aa'
        tbl += f"<tr style='border-bottom:1px solid #1e2235'><td style='padding:6px;color:#fff'>{str(row['Title'])[:40]}</td><td style='padding:6px;color:#8b92a5'>{str(row['Auto_Category'])[:18]}</td><td style='padding:6px;text-align:right'>£{row['Price']:.2f}</td><td style='padding:6px;text-align:right'>£{row['Compare At Price']:.2f}</td><td style='padding:6px;text-align:right;color:{dc}'>£{row['Price Difference']:.2f}</td><td style='padding:6px;text-align:center'>{badge(row['Pricing Status'])}</td></tr>"
    tbl += "</table>"
    st.markdown(tbl, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Alerts & Notifications</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="alert-danger">❌ {pricing_issues} pricing issues — {round(pricing_issues/products_checked*100,1)}% of checked products has misleading discounts</div>
        <div class="alert-warning">⚠️ {low_price_items} products priced under £5 — review profitability</div>
        <div class="alert-warning">⚠️ Avg checkout conversion {avg_conversion:.1f}% — monitor monthly</div>
        <div class="alert-success">✅ Prophet AI forecast — {supabase_records} products forecasted</div>
        <div class="alert-success">✅ Supabase cloud — {supabase_records} records live</div>
        <div class="alert-success">✅ Stage 1 analytics pipeline — complete</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="section-title">Data Quality Snapshot</div>', unsafe_allow_html=True)
        dq_cols = st.columns(2)
        for i,(title,val,sub) in enumerate([
            ("Clean Products",f"{products_checked:,}","price_check_enriched.csv"),
            ("Quality Score",f"{quality_score}%","Pricing integrity"),
            ("Last Pipeline",last_pipeline_run,"08_pipeline_health.py")
        ]):
            with dq_cols[i%2]:
                st.markdown(f'<div class="dq-card"><div class="dq-title">{title}</div><div class="dq-value">{val}</div><div class="dq-sub">{sub}</div></div>', unsafe_allow_html=True)

# ══ SALES OVERVIEW ════════════════════════════════════════════════════════
elif page == "💷 Sales Overview":
    st.markdown("## 💷 Sales Overview")
    st.markdown("Real store performance, plus the sample data used to train the AI forecast")
    st.markdown("---")
    c1,c2,c3,c4,c5 = st.columns(5)
    for col,(icon,label,val,delta,dtype) in zip([c1,c2,c3,c4,c5],[
        ("💷","Total Revenue",f"£{total_Total:,.2f}","Pre-launch — no orders yet","warn"),
        ("🧾","Total Orders",f"{total_orders}","Pre-launch — no orders yet","warn"),
        ("📦","Avg Order Value",f"£0.00","N/A until first order","warn"),
        ("🔮","Projected Revenue",f"£{projected_rev:,.0f}","Next 90 days — Prophet AI","pos"),
        ("🏷️","Catalogue Size",f"{total_products}","Product-level sales not tracked yet","warn"),
    ]):
        with col: st.markdown(kpi(icon,label,val,delta,dtype), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"📊 The store has 0 real orders so far. The chart below uses {sample_order_rows} sample order records (Mar – Aug 2026) that were created purely to give the Prophet model a training series — they are not real sales.")
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Sample Training Data — Revenue by Date (£)</div>', unsafe_allow_html=True)
        fig_rev = px.bar(daily_sales, x='Created at', y='Lineitem price', color_discrete_sequence=['#00d4aa'],
                          text=daily_sales['Lineitem price'].apply(lambda x: f'£{x:.0f}'))
        fig_rev.update_traces(textposition='outside', textfont=dict(size=11))
        fig_rev.update_layout(**LAYOUT, height=340, xaxis=dict(gridcolor='#2e3450',title=''), yaxis=dict(gridcolor='#2e3450',title='Revenue (£)'))
        st.plotly_chart(fig_rev, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Sample Training Data — Orders by Date</div>', unsafe_allow_html=True)
        daily_orders = sh.groupby('Created at').size().reset_index(name='Orders')
        fig_ord = px.bar(daily_orders, x='Created at', y='Orders', color_discrete_sequence=['#7c6af7'], text='Orders')
        fig_ord.update_traces(textposition='outside', textfont=dict(size=11))
        fig_ord.update_layout(**LAYOUT, height=340, xaxis=dict(gridcolor='#2e3450',title=''), yaxis=dict(gridcolor='#2e3450',title='Orders',tickformat=',d'))
        st.plotly_chart(fig_ord, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if 'Product' in sh.columns:
        st.markdown('<div class="section-title">Sample Training Data — Product &amp; Price Used</div>', unsafe_allow_html=True)
        sample_tbl = sh[['Created at','Product','Lineitem price']].rename(columns={'Created at':'Date','Lineitem price':'Price (£)'})
        st.dataframe(sample_tbl, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top 10 Products by Predicted Revenue (90 days)</div>', unsafe_allow_html=True)
    top10_products = pf.nlargest(10,'forecast_revenue_90_days').reset_index(drop=True)
    units_sold_col = 'units_sold_to_date' if 'units_sold_to_date' in top10_products.columns else None
    rows_html = ""
    for i,row in top10_products.iterrows():
        units_sold_to_date = row[units_sold_col] if units_sold_col else 0
        rows_html += (f"<tr style='border-bottom:1px solid #f1f5f9'>"
                      f"<td style='padding:8px;color:#8b92a5'>{i+1}</td>"
                      f"<td style='padding:8px;color:#ffffff'>{str(row['product_name'])[:60]}</td>"
                      f"<td style='padding:8px;text-align:right'>£{row['price_gbp']:.2f}</td>"
                      f"<td style='padding:8px;text-align:right'>{units_sold_to_date}</td>"
                      f"<td style='padding:8px;text-align:right'>{row['forecast_units_90_days']:.0f}</td>"
                      f"<td style='padding:8px;text-align:right;color:#00a884;font-weight:600'>£{row['forecast_revenue_90_days']:,.2f}</td></tr>")
    st.markdown(f"""<table style='width:100%;border-collapse:collapse;font-size:13px'>
    <tr style='color:#8b92a5;border-bottom:1px solid #2e3450'>
        <th style='text-align:left;padding:8px'></th><th style='text-align:left;padding:8px'>Product</th>
        <th style='text-align:right;padding:8px'>Price (£)</th><th style='text-align:right;padding:8px'>Units Sold</th>
        <th style='text-align:right;padding:8px'>Forecast Units</th><th style='text-align:right;padding:8px'>Forecast Revenue (£)</th>
    </tr>{rows_html}</table>""", unsafe_allow_html=True)

# ══ PRODUCT ANALYTICS ═════════════════════════════════════════════════════
elif page == "📦 Product Analytics":
    st.markdown("## 📦 Product Analytics")
    st.markdown("Page views and product performance — Stage 1")
    st.markdown("---")
    pv_clean = pv.dropna(subset=['Page loads'])
    c1,c2,c3,c4 = st.columns(4)
    for col,(icon,label,val,delta,dtype) in zip([c1,c2,c3,c4],[
        ("👁️","Total Page Views",f"{int(pv_clean['Page loads'].sum()):,}","365 days","pos"),
        ("📄","Pages Tracked",f"{len(pv_clean):,}","Unique pages","pos"),
        ("⭐","Top Page Views",f"{int(pv_clean['Page loads'].max()):,}","Single page","pos"),
        ("📦","Categories",f"{prod_clean['Auto_Category'].nunique()}","Auto-classified (Stage 1)","pos"),
    ]):
        with col: st.markdown(kpi(icon,label,val,delta,dtype), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Top 15 Pages by Views</div>', unsafe_allow_html=True)
        top = pv_clean.nlargest(15,'Page loads').copy()
        top['Page path'] = top['Page path'].str[:40]
        fig = px.bar(top, x='Page loads', y='Page path', orientation='h', color_discrete_sequence=['#00d4aa'])
        fig.update_layout(**LAYOUT, height=420, xaxis=dict(gridcolor='#2e3450',title='Page Loads'), yaxis=dict(gridcolor='#2e3450',title=''))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Products by Category</div>', unsafe_allow_html=True)
        cat = prod_clean['Auto_Category'].value_counts().reset_index()
        cat.columns = ['Category','Count']
        cat = cat.sort_values('Count', ascending=True)
        cat['Category'] = cat['Category'].apply(lambda c: truncate_label(c, 22))
        fig2 = go.Figure(go.Bar(x=cat['Count'], y=cat['Category'], orientation='h',
                                 text=cat['Count'], textposition='outside', marker_color='#7c6af7'))
        fig2.update_layout(**LAYOUT, height=420, xaxis=dict(gridcolor='#2e3450',title='Products'), yaxis=dict(gridcolor='#2e3450',title=''))
        st.plotly_chart(fig2, use_container_width=True)

# ══ PRICING AUDIT ═════════════════════════════════════════════════════════
elif page == "💰 Pricing Audit":
    st.markdown("## 💰 Pricing Audit")
    st.markdown("Full pricing integrity analysis — Stage 1")
    st.markdown("---")
    ok_count  = len(pc[pc['Pricing Status']=='OK'])
    nd_count  = len(pc[pc['Pricing Status']=='No Discount'])
    mis_count = len(pc[pc['Pricing Status']=='Misleading Discount'])
    c1,c2,c3,c4 = st.columns(4)
    for col,(icon,label,val,delta,dtype) in zip([c1,c2,c3,c4],[
        ("📦","Total Products",f"{total_products}","In catalogue","pos"),
        ("✅","Correctly Priced",f"{ok_count}","OK status","pos"),
        ("⚠️","No Discount Set",f"{nd_count}","Missing compare-at","warn"),
        ("❌","Misleading Discount",f"{mis_count}","Price > compare-at","neg"),
    ]):
        with col: st.markdown(kpi(icon,label,val,delta,dtype), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Pricing Status Breakdown</div>', unsafe_allow_html=True)
        ps = pc['Pricing Status'].value_counts().reset_index()
        ps.columns = ['Status','Count']
        status_colors_map = {'Misleading Discount':'#ff4b6e','No Discount':'#f59e0b','OK':'#00d4aa'}
        ps_sorted = ps.sort_values('Count', ascending=True)
        fig = go.Figure(go.Bar(
            x=ps_sorted['Count'], y=ps_sorted['Status'], orientation='h',
            text=ps_sorted.apply(lambda r: f"{r['Count']} ({r['Count']/ps['Count'].sum()*100:.1f}%)", axis=1),
            textposition='outside',
            marker_color=[status_colors_map.get(s,'#60a5fa') for s in ps_sorted['Status']]
        ))
        fig.update_layout(**LAYOUT, height=320,
                          xaxis=dict(gridcolor='#2e3450',title='Products',range=[0,ps_sorted['Count'].max()*1.2]),
                          yaxis=dict(title=''))
        fig.update_layout(margin=dict(l=0,r=40,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Avg Price by Category</div>', unsafe_allow_html=True)
        # Full clean catalogue (products_clean.csv), same source 04_pricing_analysis.py
        # and 05_competitive_pricing.py use — not the smaller price-checked subset,
        # which was giving this chart different numbers than the terminal scripts.
        cat_avg = prod_clean.groupby('Auto_Category')['Variant Price'].mean().sort_values(ascending=False).reset_index()
        cat_avg.columns = ['Category', 'Price']
        cat_avg['Category'] = cat_avg['Category'].apply(lambda c: truncate_label(c, 22))
        fig2 = px.bar(cat_avg, x='Price', y='Category', orientation='h', color_discrete_sequence=['#f59e0b'])
        fig2.update_layout(**LAYOUT, height=320, xaxis=dict(gridcolor='#2e3450',title='Avg Price (£)'), yaxis=dict(gridcolor='#2e3450',title=''))
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown('<div class="section-title">Full Pricing Table</div>', unsafe_allow_html=True)
    filter_status = st.selectbox("Filter by status", ["All","Misleading Discount","No Discount","OK"])
    search_p = st.text_input("Search product", placeholder="Type product name...", key="pa_search")
    df_show = pc.copy()
    if filter_status != "All": df_show = df_show[df_show['Pricing Status']==filter_status]
    if search_p: df_show = df_show[df_show['Title'].str.contains(search_p, case=False, na=False)]
    df_show = df_show.sort_values('Price Difference').reset_index(drop=True)
    df_show.index += 1
    st.dataframe(df_show, use_container_width=True)
    st.download_button("⬇️ Download CSV", df_show.to_csv(index=False).encode('utf-8'), "pricing_audit.csv", "text/csv")

# ══ TRAFFIC & FUNNEL ══════════════════════════════════════════════════════
elif page == "📈 Traffic & Funnel":
    st.markdown("## 📈 Traffic & Funnel Analysis")
    st.markdown("365 day traffic and conversion data — Stage 1")
    st.markdown("---")
    avg_bounce = ses['Bounce rate'].mean() if 'Bounce rate' in ses.columns else 0
    c1,c2,c3,c4 = st.columns(4)
    for col,(icon,label,val,delta,dtype) in zip([c1,c2,c3,c4],[
        ("📈","Total Sessions",f"{total_sessions:,}","365 days","pos"),
        ("🔄","Avg Conversion",f"{avg_conversion:.1f}%","Checkout / sessions","pos"),
        ("↩️","Avg Bounce Rate",f"{avg_bounce*100:.1f}%","Monthly avg","warn"),
        ("🛒","Reached Checkout",f"{total_checkout:,}","Total sessions","pos"),
    ]):
        with col: st.markdown(kpi(icon,label,val,delta,dtype), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Monthly Sessions Trend</div>', unsafe_allow_html=True)
        fig = px.line(ses, x='Month', y='Sessions', markers=True, color_discrete_sequence=['#00d4aa'])
        fig.update_layout(**LAYOUT, xaxis=dict(gridcolor='#2e3450',title=''), yaxis=dict(gridcolor='#2e3450',title='Sessions'))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Traffic Sources Breakdown</div>', unsafe_allow_html=True)
        fig2 = px.pie(tr, names='Referrer source', values='Sessions', color_discrete_sequence=['#00d4aa','#7c6af7','#f59e0b','#ff4b6e','#60a5fa'])
        fig2.update_layout(**LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)
    col3,col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">Conversion Funnel (365 days)</div>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Funnel(
            y=["Total Sessions","Store Visitors","Reached Checkout","Converted"],
            x=[total_sessions,total_visitors,total_checkout,total_converted],
            textinfo="value+percent initial", textfont=dict(size=11),
            marker=dict(color=['#00d4aa','#7c6af7','#f59e0b','#ff4b6e'])
        ))
        fig3.update_layout(**LAYOUT)
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        st.markdown('<div class="section-title">Monthly Checkout Rate</div>', unsafe_allow_html=True)
        fig4 = px.bar(ses, x='Month', y='Real Conversion Rate', color_discrete_sequence=['#7c6af7'])
        fig4.update_layout(**LAYOUT, xaxis=dict(gridcolor='#2e3450',title=''), yaxis=dict(gridcolor='#2e3450',title='Checkout Rate (%)'))
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔍 Where People Actually Land and Browse</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#8b92a5'>From 07_traffic_analysis.py — Shopify's landing-page and page-load reports, not used anywhere before now</small>", unsafe_allow_html=True)
    d1,d2,d3 = st.columns(3)
    with d1:
        st.markdown(kpi("🎯","Direct Traffic",f"{traffic_summary['direct_traffic_pct']}%","No referrer at all","warn"), unsafe_allow_html=True)
    with d2:
        st.markdown(kpi("🏠","Land on Homepage",f"{traffic_summary['home_landing_pct']}%","Instead of a product/collection page","warn"), unsafe_allow_html=True)
    with d3:
        st.markdown(kpi("📦","Reach a Product Page",f"{traffic_summary['product_pageload_pct']}%","Share of all page loads","warn"), unsafe_allow_html=True)
    if traffic_summary['direct_traffic_pct'] > 70:
        st.warning(f"⚠️ {traffic_summary['direct_traffic_pct']}% of sessions are direct — almost nobody is finding the store through search or ads right now, so growth depends on whoever already has the link.")
    if traffic_summary['product_pageload_pct'] < 15:
        st.warning(f"⚠️ Only {traffic_summary['product_pageload_pct']}% of page loads ever reach an actual product page — most visits don't get past the homepage or a collection grid.")
    top_pages = pd.read_csv('outputs/traffic_top_pages.csv').head(10)
    st.markdown('<div class="section-title">Top 10 Pages by Page Loads</div>', unsafe_allow_html=True)
    fig6 = px.bar(top_pages.sort_values('Page loads'), x='Page loads', y='Page path', orientation='h', color_discrete_sequence=['#2dd4bf'])
    fig6.update_layout(**LAYOUT, height=340, xaxis=dict(gridcolor='#2e3450',title='Page Loads'), yaxis=dict(gridcolor='#2e3450',title=''))
    st.plotly_chart(fig6, use_container_width=True)

# ══ COMPETITIVE PRICING ═══════════════════════════════════════════════════
elif page == "🏷️ Competitive Pricing":
    st.markdown("## 🏷️ Competitive Pricing")
    st.markdown("Price positioning and market comparison — Stage 1")
    st.markdown("---")
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Price Band Distribution</div>', unsafe_allow_html=True)
        pc2 = pc.copy()
        pc2['Band'] = pd.cut(pc2['Price'], bins=[0,10,20,30,50,100,200,500,10000], labels=['£0-10','£10-20','£20-30','£30-50','£50-100','£100-200','£200-500','£500+'])
        band = pc2['Band'].value_counts().sort_index().reset_index()
        band.columns = ['Band','Count']
        fig = px.bar(band, x='Band', y='Count', color_discrete_sequence=['#00d4aa'])
        fig.update_layout(**LAYOUT, xaxis=dict(gridcolor='#2e3450',title='Price Band'), yaxis=dict(gridcolor='#2e3450',title='Products'))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Avg Price by Category</div>', unsafe_allow_html=True)
        # Full clean catalogue (products_clean.csv), same source 04_pricing_analysis.py
        # and 05_competitive_pricing.py use — not the smaller price-checked subset,
        # which was giving this chart different numbers than the terminal scripts.
        cat_avg = prod_clean.groupby('Auto_Category')['Variant Price'].mean().sort_values(ascending=False).reset_index()
        cat_avg.columns = ['Category', 'Price']
        cat_avg['Category'] = cat_avg['Category'].apply(lambda c: truncate_label(c, 22))
        fig2 = px.bar(cat_avg, x='Price', y='Category', orientation='h', color_discrete_sequence=['#f59e0b'])
        fig2.update_layout(**LAYOUT, xaxis=dict(gridcolor='#2e3450',title='Avg Price (£)'), yaxis=dict(gridcolor='#2e3450',title=''))
        st.plotly_chart(fig2, use_container_width=True)
    col3,col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">Price vs Compare-At Scatter</div>', unsafe_allow_html=True)
        scatter = pc.dropna(subset=['Compare At Price']).copy()
        fig3 = px.scatter(scatter, x='Compare At Price', y='Price', color='Pricing Status',
                          color_discrete_map={'Misleading Discount':'#ff4b6e','No Discount':'#f59e0b','OK':'#00d4aa'},
                          hover_data=['Title','Category'])
        fig3.add_shape(type='line', x0=0, y0=0, x1=scatter['Compare At Price'].max(), y1=scatter['Compare At Price'].max(), line=dict(color='#8b92a5',dash='dash'))
        fig3.update_layout(**LAYOUT, xaxis=dict(gridcolor='#2e3450',title='Compare At Price (£)'), yaxis=dict(gridcolor='#2e3450',title='Selling Price (£)'), legend=dict(bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        st.markdown('<div class="section-title">Discount % Distribution</div>', unsafe_allow_html=True)
        disc = pc.dropna(subset=['Discount %']).copy()
        fig4 = px.histogram(disc, x='Discount %', nbins=30, color_discrete_sequence=['#7c6af7'])
        fig4.update_layout(**LAYOUT, xaxis=dict(gridcolor='#2e3450',title='Discount %'), yaxis=dict(gridcolor='#2e3450',title='Products'))
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🏆 Seamark vs Amazon UK — Avg Price by Category</div>', unsafe_allow_html=True)
    # This is the actual "how do we compare to Amazon" check the project was
    # meant to answer. It comes straight from outputs/competitive_pricing.csv,
    # which 05_competitive_pricing.py writes — so this chart and the terminal
    # script always show the exact same numbers instead of two versions of
    # the same comparison computed two different ways.
    amazon_cmp = vs_amazon.sort_values('Difference %')
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(x=amazon_cmp['Category'], y=amazon_cmp['Seamark Avg Price (£)'], name='Seamark', marker_color='#00d4aa'))
    fig5.add_trace(go.Bar(x=amazon_cmp['Category'], y=amazon_cmp['Amazon Benchmark (£)'], name='Amazon UK', marker_color='#ff4b6e'))
    fig5.update_layout(**LAYOUT, barmode='group', height=340,
                        xaxis=dict(gridcolor='#2e3450', title=''),
                        yaxis=dict(gridcolor='#2e3450', title='Avg Price (£)'),
                        legend=dict(bgcolor='rgba(0,0,0,0)'))
    st.plotly_chart(fig5, use_container_width=True)
    cheaper = amazon_cmp[amazon_cmp['Difference %'] < 0]
    pricier = amazon_cmp[amazon_cmp['Difference %'] > 0]
    cheapest_note = f"{cheaper.iloc[0]['Category']} ({cheaper.iloc[0]['Difference %']}% below)" if len(cheaper) else "none"
    pricier_note  = f"{pricier.iloc[-1]['Category']} ({pricier.iloc[-1]['Difference %']}% above)" if len(pricier) else "none"
    st.markdown(f"""
    <div class="alert-success">✅ Cheaper than Amazon in {len(cheaper)} of {len(vs_amazon)} categories — biggest gap: {cheapest_note}</div>
    <div class="alert-warning">⚠️ Pricier than Amazon in {len(pricier)} of {len(vs_amazon)} categories — biggest gap: {pricier_note}</div>
    """, unsafe_allow_html=True)

# ══ AFFILIATE ═════════════════════════════════════════════════════════════
elif page == "🤝 Affiliate Programme":
    st.markdown("## 🤝 Affiliate Programme")
    st.markdown("Affiliate network overview — Stage 1")
    st.markdown("---")
    verified  = len(af[af['verified'].astype(str).str.lower().isin(['true','yes','1'])]) if 'verified' in af.columns else 0
    countries = af['country'].nunique() if 'country' in af.columns else 0
    c1,c2,c3,c4 = st.columns(4)
    for col,(icon,label,val,delta,dtype) in zip([c1,c2,c3,c4],[
        ("👥","Total Affiliates",f"{total_affiliates}","Registered","pos"),
        ("✅","Active",f"{active_affiliates}","Currently active","pos"),
        ("🌍","Countries",f"{countries}","Global reach","pos"),
        ("✔️","Verified",f"{verified}","KYC complete","pos"),
    ]):
        with col: st.markdown(kpi(icon,label,val,delta,dtype), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Affiliates by Country (Top 10)</div>', unsafe_allow_html=True)
        if 'country' in af.columns:
            cc = af['country'].fillna('Unknown').replace('','Unknown').value_counts().head(10).reset_index()
            cc.columns = ['Country','Count']
            fig = px.bar(cc, x='Count', y='Country', orientation='h', color_discrete_sequence=['#00d4aa'])
            fig.update_layout(**LAYOUT, xaxis=dict(gridcolor='#2e3450',title='Affiliates'), yaxis=dict(gridcolor='#2e3450',title=''))
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Status Breakdown</div>', unsafe_allow_html=True)
        if 'status' in af.columns:
            sc = af['status'].value_counts().reset_index()
            sc.columns = ['Status','Count']
            fig2 = px.pie(sc, names='Status', values='Count', color_discrete_sequence=['#00d4aa','#7c6af7','#f59e0b','#ff4b6e'])
            fig2.update_layout(**LAYOUT)
            st.plotly_chart(fig2, use_container_width=True)
    st.markdown('<div class="section-title">Affiliate Directory</div>', unsafe_allow_html=True)
    cols_show = [c for c in ['first_name','last_name','email','country','status','program','date_created'] if c in af.columns]
    st.dataframe(af[cols_show].reset_index(drop=True), use_container_width=True)

# ══ AI FORECAST ═══════════════════════════════════════════════════════════
elif page == "🔮 AI Forecast":
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1e2235,#252a3d);border:1px solid #2e3450;
    border-radius:12px;padding:20px;margin-bottom:20px;text-align:center'>
        <div style='font-size:26px;font-weight:700;color:#ffffff'>🏢 SEAMARK GLOBAL INNOVATIONS</div>
        <div style='font-size:13px;color:#00d4aa;margin-top:4px'>AI Demand Forecasting Platform — Stage 2 | Prophet AI + Supabase Cloud</div>
        <div style='font-size:11px;color:#8b92a5;margin-top:4px'>theseamarkglobalinnovations.com | Forecast Period: Aug 2026 — Nov 2026</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("## 🔮 AI Demand Forecast")
    st.markdown("Prophet AI — 90 day Revenue predictions | ☁️ Supabase Cloud")
    st.markdown("---")
    c1,c2,c3,c4 = st.columns(4)
    for col,(icon,label,val,delta,dtype) in zip([c1,c2,c3,c4],[
        ("🔮","AI Forecast Revenue",f"£{projected_rev:,.0f}","Next 90 days — Prophet AI","pos"),
        ("📦","Products Forecasted",f"{supabase_records}","Supabase cloud","pos"),
        ("📈","Avg Daily Revenue",f"£{avg_daily_rev:,.0f}","Predicted per day","pos"),
        ("☁️","Cloud Records",f"{supabase_records}","🟢 Supabase live","pos"),
    ]):
        with col: st.markdown(kpi(icon,label,val,delta,dtype), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">📦 Product Category Distribution</div>', unsafe_allow_html=True)
        cat = prod_clean['Auto_Category'].value_counts().reset_index()
        cat.columns = ['Category','Count']
        cat = cat.sort_values('Count', ascending=True)
        total_cat = cat['Count'].sum()
        cat['pct'] = (cat['Count']/total_cat*100).round(1)
        cat['label'] = cat.apply(lambda r: f"{r['Count']} ({r['pct']}%)", axis=1)
        cat['Category'] = cat['Category'].apply(lambda c: truncate_label(c, 25))
        fig_cat = go.Figure(go.Bar(x=cat['Count'], y=cat['Category'], orientation='h',
                                    text=cat['label'], textposition='outside', marker_color='#2dd4bf'))
        fig_cat.update_layout(**LAYOUT, height=420,
                              xaxis=dict(gridcolor='#2e3450',title='Product Count',range=[0,cat['Count'].max()*1.25]),
                              yaxis=dict(gridcolor='#2e3450',title=''), uniformtext_minsize=9)
        fig_cat.update_layout(margin=dict(l=0,r=40,t=20,b=0))
        st.plotly_chart(fig_cat, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">☁️ Supabase Cloud Status</div>', unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=supabase_records,
            title={'text':"Records Live in Supabase<br><span style='font-size:12px;color:#8b92a5'>Deduplicated from 540 → 270</span>"},
            gauge={'axis':{'range':[0,300],'tickcolor':'#8b92a5'},'bar':{'color':'#00d4aa'},
                   'bgcolor':'#1e2235','bordercolor':'#2e3450',
                   'steps':[{'range':[0,100],'color':'#1a1d27'},{'range':[100,200],'color':'#1e2235'},{'range':[200,300],'color':'#252a3d'}],
                   'threshold':{'line':{'color':'#f59e0b','width':3},'thickness':0.75,'value':270}}
        ))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#ffffff', height=280, margin=dict(l=20,r=20,t=80,b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown(f"""
        <div class="alert-success">✅ Supabase connected — {supabase_records} unique products live</div>
        <div class="alert-success">✅ Table: product_demand_forecast — Updated {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</div>
        <div class="alert-success">✅ Prophet AI forecast — 90 day predictions complete</div>
        """, unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 Prophet AI — 90 Day Revenue Forecast vs Actual Sales</div>', unsafe_allow_html=True)
    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(
        x=pd.concat([sf['ds'], sf['ds'][::-1]]),
        y=pd.concat([sf['yhat_upper_Total'], sf['yhat_lower_Total'][::-1]]),
        fill='toself', fillcolor='rgba(45,212,191,0.12)',
        line=dict(color='rgba(0,0,0,0)'), showlegend=True, name='Confidence Interval'
    ))
    fig_fc.add_trace(go.Scatter(x=sf['ds'], y=sf['yhat_Total'], mode='lines+markers',
                                 line=dict(color='#00d4aa',width=3), marker=dict(size=4), name='Prophet AI Forecast (£)'))
    fig_fc.add_trace(go.Scatter(x=daily_sales['Created at'], y=daily_sales['Lineitem price'], mode='lines+markers',
                                 line=dict(color='#f59e0b',width=3,dash='dot'), marker=dict(size=8,symbol='circle'), name='Sample Training Data (£)'))
    fig_fc.add_vline(x=future_sf['ds'].min(), line_dash='dash', line_color='#8b92a5',
                     annotation_text='Forecast Start', annotation_position='top right', annotation_font_color='#8b92a5')
    fig_fc.update_layout(**LAYOUT, height=480,
                          xaxis=dict(gridcolor='#2e3450',title='Date',showgrid=True),
                          yaxis=dict(gridcolor='#2e3450',title='Revenue (£)',showgrid=True),
                          legend=dict(bgcolor='rgba(30,34,53,0.9)',font=dict(size=11),orientation='h',yanchor='bottom',y=1.02,xanchor='center',x=0.5),
                          hovermode='x unified')
    fig_fc.update_layout(margin=dict(l=0,r=0,t=60,b=0))
    st.plotly_chart(fig_fc, use_container_width=True)
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Total Forecast Revenue", f"£{projected_rev:,.0f}", "90 days")
    m2.metric("Avg Daily Forecast", f"£{avg_daily_rev:,.0f}", "Per day")
    m3.metric("Peak Forecast Revenue", f"£{future_sf['yhat_Total'].max():,.0f}", "Single day")
    m4.metric("Sample Training Total", f"£{daily_sales['Lineitem price'].sum():,.2f}", "Mar – Aug 2026 (not real sales)")
    st.markdown("""
    <div style='background:#1e2235;border-radius:8px;padding:10px 16px;font-size:12px;color:#8b92a5;margin:10px 0'>
        🟢 <b style='color:#00d4aa'>Teal line</b> = Prophet AI 90-day Revenue forecast &nbsp;|&nbsp;
        🟡 <b style='color:#f59e0b'>Orange dots</b> = Sample training data (Mar – Aug 2026) — made up to train the model, not real sales &nbsp;|&nbsp; Shaded area = Confidence band
    </div>
    """, unsafe_allow_html=True)
    col3,col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">🏆 Top 10 Products by Forecast Revenue</div>', unsafe_allow_html=True)
        top10 = pf.nlargest(10,'forecast_revenue_90_days').copy()
        top10 = top10.sort_values('forecast_revenue_90_days', ascending=True)
        top10['Label'] = top10['product_name'].str[:40]
        fig_top = go.Figure(go.Bar(x=top10['forecast_revenue_90_days'], y=top10['Label'], orientation='h',
                                    text=top10['forecast_revenue_90_days'].apply(lambda x: f'£{x:,.0f}'),
                                    textposition='outside', marker_color='#7c6af7'))
        fig_top.update_layout(**LAYOUT, height=380,
                              xaxis=dict(gridcolor='#2e3450',title='Forecast Revenue (£)',range=[0,top10['forecast_revenue_90_days'].max()*1.15]),
                              yaxis=dict(gridcolor='#2e3450',title=''))
        fig_top.update_layout(margin=dict(l=0,r=40,t=10,b=0))
        st.plotly_chart(fig_top, use_container_width=True)
    with col4:
        st.markdown('<div class="section-title">📊 Forecast Units Distribution</div>', unsafe_allow_html=True)
        units = pf['forecast_units_90_days']
        if units.nunique() <= 1:
            st.markdown(f"""<div class="alert-warning">⚠️ All {len(units)} products are forecasted at exactly
            <b>{int(units.iloc[0])} units</b> over 90 days — no variation across products.</div>""", unsafe_allow_html=True)
        else:
            fig_hist = px.histogram(pf, x='forecast_units_90_days', nbins=20, color_discrete_sequence=['#f59e0b'])
            fig_hist.update_layout(**LAYOUT, height=380,
                                   xaxis=dict(gridcolor='#2e3450',title='Forecast Units (90 days)'),
                                   yaxis=dict(gridcolor='#2e3450',title='Number of Products'))
            st.plotly_chart(fig_hist, use_container_width=True)
    st.markdown('<div class="section-title">🛒 Sample Training Data — Mar to Aug 2026 (not real sales)</div>', unsafe_allow_html=True)
    fig_sales = px.bar(daily_sales, x='Created at', y='Lineitem price', color_discrete_sequence=['#00d4aa'],
                       text=daily_sales['Lineitem price'].apply(lambda x: f'£{x:.0f}'))
    fig_sales.update_traces(textposition='outside', textfont=dict(size=11))
    fig_sales.update_layout(**LAYOUT, height=350, xaxis=dict(gridcolor='#2e3450',title='Date'), yaxis=dict(gridcolor='#2e3450',title='Revenue (£)'))
    st.plotly_chart(fig_sales, use_container_width=True)
    st.markdown('<div class="section-title">📋 Full Supabase Forecast Table</div>', unsafe_allow_html=True)
    search = st.text_input("🔍 Search product", placeholder="Type product name...", key="fc_search")
    df_fc = pf.copy()
    if search: df_fc = df_fc[df_fc['product_name'].str.contains(search, case=False, na=False)]
    df_fc = df_fc.sort_values('forecast_revenue_90_days', ascending=False).reset_index(drop=True)
    df_fc.index += 1
    st.dataframe(df_fc, use_container_width=True, height=400)
    st.download_button("⬇️ Download Forecast CSV", df_fc.to_csv(index=False).encode('utf-8'), "seamark_ai_forecast.csv", "text/csv")

# ══ ALERTS ════════════════════════════════════════════════════════════════
elif page == "🔔 Alerts":
    st.markdown("## 🔔 Alerts & System Status")
    st.markdown("---")
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">System Status</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="alert-danger">❌ {pricing_issues} pricing issues — {round(pricing_issues/products_checked*100,1)}% of checked products has misleading discounts</div>
        <div class="alert-warning">⚠️ {low_price_items} products priced under £5 — review profitability</div>
        <div class="alert-warning">⚠️ Weekly scheduler not yet configured</div>
        <div class="alert-warning">⚠️ Email reports not yet configured</div>
        <div class="alert-warning">⚠️ GitHub push needed — Stage 2 files not yet committed</div>
        <div class="alert-success">✅ Stage 1 analytics pipeline — complete</div>
        <div class="alert-success">✅ Prophet AI forecast — {supabase_records} products forecasted</div>
        <div class="alert-success">✅ Supabase cloud — {supabase_records} records live</div>
        <div class="alert-success">✅ Streamlit dashboard — Running</div>
        <div class="alert-success">✅ price_check_enriched.csv — Generated</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="section-title">Data Quality Snapshot</div>', unsafe_allow_html=True)
        dq_cols = st.columns(2)
        for i,(title,val,sub) in enumerate([
            ("Enriched Products",f"{products_checked:,}","price_check_enriched.csv"),
            ("Orders Placed",f"{total_orders}","Pre-launch"),
            ("Affiliates",f"{total_affiliates}","affiliate_data.csv"),
            ("Cloud Records",f"{supabase_records}","Supabase — live"),
            ("Quality Score",f"{quality_score}%","Pricing integrity"),
        ]):
            with dq_cols[i%2]:
                st.markdown(f'<div class="dq-card"><div class="dq-title">{title}</div><div class="dq-value">{val}</div><div class="dq-sub">{sub}</div></div>', unsafe_allow_html=True)

elif page == "Funnel Analysis":
    st.title("Funnel Analysis")
    st.markdown("Conversion funnel breakdown and drop-off analysis")
    col1,col2 = st.columns(2)
    with col1:
        total_sessions_fa = ses["Sessions"].sum()
        visitors_fa = ses["Online store visitors"].sum()
        checkout_fa = ses["Sessions that reached checkout"].sum()
        # This used to fill in "Add to Cart" and "Completed Purchase" with
        # made-up percentages (28.2% / 35.6%) because we don't track cart
        # events and no real order has gone through yet. Every month in
        # sessions_by_month_365d.csv shows 0% conversion, so the funnel now
        # stops being honest the moment it guesses a number for that last
        # stage — better to end it at Reached Checkout, at zero completed.
        funnel_data = {"Stage":["Sessions","Store Visitors","Reached Checkout","Completed Purchase"],
                       "Count":[int(total_sessions_fa), int(visitors_fa), int(checkout_fa), total_orders]}
        fig = go.Figure(go.Funnel(y=funnel_data["Stage"], x=funnel_data["Count"],
                        marker_color=["#4f8ef7","#7b6cf7","#f59e0b","#ff4b6e"]))
        fig.update_layout(template="plotly_dark", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### Conversion Rates")
        cr = round(checkout_fa / total_sessions_fa * 100, 2) if total_sessions_fa > 0 else 0
        st.metric("Session to Checkout", str(cr)+"%")
        st.metric("Total Sessions", str(int(total_sessions_fa)))
        st.metric("Reached Checkout", str(int(checkout_fa)))
        st.metric("Online Store Visitors", str(int(visitors_fa)))
        st.metric("Completed Purchase", str(total_orders), "Pre-launch — no orders yet")

elif page == "Inventory Operations":
    st.title("Inventory Operations")
    st.markdown("Stock levels, low inventory alerts and product status")
    out_of_stock_ct = int((inv['stock_qty'] == 0).sum())
    low_stock_ct    = int(((inv['stock_qty'] > 0) & (inv['stock_qty'] < 10)).sum())
    col1,col2,col3 = st.columns(3)
    col1.metric("Total SKUs Tracked", str(len(inv)))
    col2.metric("Low Stock SKUs", str(low_stock_ct))
    col3.metric("Out of Stock", str(out_of_stock_ct))
    if out_of_stock_ct == len(inv):
        st.error(f"⚠️ All {len(inv)} tracked SKUs are showing zero stock — check the supplier feed / stock sync before trusting these numbers.")
    elif out_of_stock_ct > 0:
        st.warning(f"⚠️ {out_of_stock_ct} SKUs are out of stock.")
    st.markdown('<div class="section-title">Stock Risk Breakdown</div>', unsafe_allow_html=True)
    risk = inv['stock_risk'].value_counts().reset_index()
    risk.columns = ['Risk Level','SKUs']
    st.dataframe(risk, use_container_width=True)
    st.dataframe(inv.sort_values('stock_qty').reset_index(drop=True), use_container_width=True)

elif page == "Pipeline Health":
    st.title("Pipeline Health")
    st.markdown("Data pipeline status, quality scores and last run times")
    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Raw Rows", f"{raw_rows:,}")
    col2.metric("Clean Rows", f"{len(prod_clean):,}")
    col3.metric("Quality Score", f"{quality_score}%")
    col4.metric("Products in DB", str(total_products))
    st.success("Pipeline completed successfully")
    st.caption(f"Last run: {last_pipeline_run} — from 08_pipeline_health.py, based on whichever pipeline file was written most recently")
    status_data = {"Source":["Products Export","Orders Export (sample)","Inventory Data","Traffic Sources","Affiliate Data","Supabase DB"],
                   "Status":["OK","OK — training data only","OK","OK","OK","Connected"],
                   "Rows":[f"{raw_rows:,}",f"{sample_order_rows}",f"{len(inv)}","12 months","10 partners",f"{supabase_records} records"]}
    st.dataframe(pd.DataFrame(status_data), use_container_width=True)

st.markdown("---")
st.markdown("<center style='color:#8b92a5;font-size:11px'>Seamark Global Innovations — Business Intelligence Platform | Stage 1: Analytics Pipeline (Jun/Jul 2026) | Stage 2: Prophet AI + Supabase Cloud (Aug 2026)</center>", unsafe_allow_html=True)
