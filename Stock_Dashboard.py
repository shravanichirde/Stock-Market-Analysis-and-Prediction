import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import watchlist_manager as wm

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="AlphaStock - Market Analysis & Prediction",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# CUSTOM CSS FOR MODERN & RESPONSIVE UI
# ==========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    .main {
        background-color: #f8fafc;
    }
    
    /* Top Brand Banner */
    .brand-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        padding: 18px 24px;
        border-radius: 16px;
        margin-bottom: 14px;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .brand-title {
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .brand-sub {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-top: 2px;
    }
    .brand-chip {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.88rem;
        font-weight: 600;
        color: #f1f5f9;
    }

    /* Navbar Container */
    .navbar-wrapper {
        background: #ffffff;
        border-radius: 14px;
        padding: 8px 12px;
        margin-bottom: 22px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* Metric & Stat Cards */
    .stMetric {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
    }
    .stat-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
    }
    .stat-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .stat-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stat-desc {
        font-size: 0.82rem;
        color: #64748b;
        margin-top: 4px;
    }

    /* Badges */
    .stock-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .stock-badge-pos {
        background-color: #dcfce7;
        color: #15803d;
    }
    .stock-badge-neg {
        background-color: #fee2e2;
        color: #b91c1c;
    }
    .active-tag {
        background-color: #e0f2fe;
        color: #0369a1;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        margin-left: 6px;
        display: inline-block;
    }

    /* Table & Headers */
    .table-header {
        font-weight: 700;
        color: #334155;
        font-size: 0.92rem;
    }
    .section-title {
        color: #0f172a;
        font-weight: 700;
        letter-spacing: -0.3px;
        margin-bottom: 4px;
    }
    .section-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 16px;
    }
    
    /* Signal Boxes */
    .signal-box-bullish {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 5px solid #22c55e;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 14px;
    }
    .signal-box-bearish {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 5px solid #ef4444;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 14px;
    }
    .signal-box-neutral {
        background: #fefce8;
        border: 1px solid #fef08a;
        border-left: 5px solid #eab308;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# SESSION STATE INITIALIZATION
# ==========================================================
if "watchlist" not in st.session_state:
    st.session_state.watchlist = wm.load_watchlist()

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = st.session_state.watchlist[0] if st.session_state.watchlist else "AAPL"

NAV_OPTIONS = [
    "🏠 Home / Dashboard",
    "💵 Current Stock Prices",
    "📈 SMA vs EMA",
    "📋 Stock Summary",
    "⭐ Watchlist",
    "🎲 Risk & Monte Carlo"
]

if "active_nav" not in st.session_state:
    st.session_state.active_nav = NAV_OPTIONS[0]

# Baseline stock lists
tech_list = ['AAPL', 'GOOG', 'MSFT', 'AMZN']
nyse_list = ['JNJ', 'NKE', 'WMT']

all_available_stocks = list(dict.fromkeys(
    ([st.session_state.selected_ticker] if st.session_state.selected_ticker else []) +
    st.session_state.watchlist +
    tech_list +
    nyse_list +
    ['NVDA', 'TSLA', 'META', 'NFLX', 'AMD', 'SPY', 'QQQ']
))

if st.session_state.selected_ticker not in all_available_stocks:
    all_available_stocks.insert(0, st.session_state.selected_ticker)

# ==========================================================
# SIDEBAR CONTROLS
# ==========================================================
st.sidebar.markdown("### ⚙️ Control Panel")

def on_sidebar_stock_select():
    st.session_state.selected_ticker = st.session_state.sidebar_ticker_picker

curr_idx = all_available_stocks.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in all_available_stocks else 0

selected_stock = st.sidebar.selectbox(
    "Active Target Stock",
    options=all_available_stocks,
    index=curr_idx,
    key="sidebar_ticker_picker",
    on_change=on_sidebar_stock_select,
    help="Select the equity to inspect across technical and fundamental views"
)
st.session_state.selected_ticker = selected_stock

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Historical Date Range")
start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("End Date", datetime.now())

if start_date >= end_date:
    st.sidebar.error("Start date must precede end date. Defaulting to 1 year window.")
    start_date = end_date - timedelta(days=365)

# Sidebar Quick Navigation
st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navigation Menu")
for nav_item in NAV_OPTIONS:
    is_active = (nav_item == st.session_state.active_nav)
    btn_label = f"👉 {nav_item}" if is_active else nav_item
    if st.sidebar.button(btn_label, key=f"sidebar_nav_{nav_item}", use_container_width=True, disabled=is_active):
        st.session_state.active_nav = nav_item
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⭐ Quick Watchlist")
st.sidebar.caption(f"{len(st.session_state.watchlist)} stocks tracked")
for wl_sym in st.session_state.watchlist:
    is_active = (wl_sym == st.session_state.selected_ticker)
    btn_text = f"👉 {wl_sym} (Active)" if is_active else f"📈 {wl_sym}"
    if st.sidebar.button(btn_text, key=f"sidebar_wl_{wl_sym}", use_container_width=True, disabled=is_active):
        st.session_state.selected_ticker = wl_sym
        st.rerun()

# ==========================================================
# DATA FETCHING HELPERS WITH CACHING
# ==========================================================
@st.cache_data(ttl=180)
def get_historical_data(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=120)
def get_multi_historical_data(tickers_tuple, start, end):
    try:
        df = yf.download(list(tickers_tuple), start=start, end=end, progress=False)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_detailed_quote_cached(ticker):
    return wm.fetch_detailed_quote(ticker)

@st.cache_data(ttl=60)
def get_detailed_quotes_cached(tickers_tuple):
    return wm.fetch_detailed_quotes(list(tickers_tuple))

@st.cache_data(ttl=300)
def get_stock_summary_cached(ticker):
    return wm.fetch_stock_summary(ticker)

# Fetch current quote for top brand chip
active_quote = get_detailed_quote_cached(selected_stock)
active_price_str = f"${active_quote['price']:.2f}" if active_quote['price'] is not None else "N/A"
if active_quote['pct_change'] is not None:
    sign = "+" if active_quote['pct_change'] >= 0 else ""
    active_delta_str = f"{sign}{active_quote['pct_change']:.2f}%"
else:
    active_delta_str = "0.00%"

# ==========================================================
# 1. TOP BRAND HEADER & RESPONSIVE NAVBAR
# ==========================================================
brand_html = f"""
<div class="brand-banner">
    <div>
        <h1 class="brand-title">📈 AlphaStock Terminal</h1>
        <div class="brand-sub">Stock Market Technical Analysis, Live Prices & Monte Carlo Forecasting</div>
    </div>
    <div style="text-align: right;">
        <span class="brand-chip">🎯 Active: <strong>{selected_stock}</strong> • {active_price_str} ({active_delta_str})</span>
    </div>
</div>
"""
st.markdown(brand_html, unsafe_allow_html=True)

# Top Navigation Bar using st.segmented_control
st.markdown('<div class="navbar-wrapper">', unsafe_allow_html=True)

# Determine default index
current_nav_idx = NAV_OPTIONS.index(st.session_state.active_nav) if st.session_state.active_nav in NAV_OPTIONS else 0

def on_navbar_change():
    if st.session_state.navbar_selector:
        st.session_state.active_nav = st.session_state.navbar_selector

nav_selection = st.segmented_control(
    "Navigation Bar",
    options=NAV_OPTIONS,
    default=st.session_state.active_nav,
    key="navbar_selector",
    on_change=on_navbar_change,
    label_visibility="collapsed"
)

# Sync state
if nav_selection and nav_selection != st.session_state.active_nav:
    st.session_state.active_nav = nav_selection

st.markdown('</div>', unsafe_allow_html=True)

current_tab = st.session_state.active_nav


# ==========================================================
# VIEW 1: 🏠 HOME / DASHBOARD
# ==========================================================
if current_tab == "🏠 Home / Dashboard":
    st.markdown(f"<h2 class='section-title'>🏠 Market Dashboard: {selected_stock} ({wm.get_company_name(selected_stock)})</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>Interactive price trajectory, trend moving averages, volume metrics, and returns distribution.</p>", unsafe_allow_html=True)

    # Market Benchmark Quick Overview Cards
    benchmarks = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]
    bench_quotes = get_detailed_quotes_cached(tuple(benchmarks))
    
    b_cols = st.columns(len(benchmarks))
    for idx, b_item in enumerate(bench_quotes):
        with b_cols[idx]:
            p_val = f"${b_item['price']:.2f}" if b_item['price'] is not None else "N/A"
            if b_item['pct_change'] is not None:
                d_val = f"{b_item['pct_change']:+.2f}%"
            else:
                d_val = "0.00%"
            st.metric(label=f"{b_item['ticker']} ({b_item['name'].split()[0]})", value=p_val, delta=d_val)

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch historical data
    stock_data = get_historical_data(selected_stock, start_date, end_date)

    if stock_data.empty or "Close" not in stock_data:
        st.error(f"⚠️ No historical trading data available for {selected_stock} in the selected range. Please expand the date range in the sidebar.")
    else:
        dash_col1, dash_col2 = st.columns([2.8, 1.2])

        with dash_col1:
            st.markdown("##### 📊 Interactive Price Action & Moving Averages")
            
            # Chart controls
            c_ctrl1, c_ctrl2 = st.columns([1.5, 2.5])
            with c_ctrl1:
                chart_type = st.radio("Chart Style", ["Candlestick", "Line Chart"], horizontal=True, key="home_chart_style")
            with c_ctrl2:
                ma_choices = st.multiselect("Overlay Moving Averages", [10, 20, 50, 100, 200], default=[20, 50], key="home_ma_choices")

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25])

            if chart_type == "Candlestick" and all(k in stock_data for k in ["Open", "High", "Low", "Close"]):
                fig.add_trace(
                    go.Candlestick(
                        x=stock_data.index,
                        open=stock_data['Open'],
                        high=stock_data['High'],
                        low=stock_data['Low'],
                        close=stock_data['Close'],
                        name=f"{selected_stock} Candlestick"
                    ),
                    row=1, col=1
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=stock_data['Close'],
                        name=f"{selected_stock} Close",
                        line=dict(color='#2563eb', width=2.5)
                    ),
                    row=1, col=1
                )

            ma_palette = {10: '#f59e0b', 20: '#10b981', 50: '#ec4899', 100: '#8b5cf6', 200: '#ef4444'}
            for ma in ma_choices:
                ma_series = stock_data['Close'].rolling(window=ma).mean()
                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=ma_series,
                        name=f"SMA ({ma})",
                        line=dict(color=ma_palette.get(ma, '#64748b'), width=1.8, dash='dash')
                    ),
                    row=1, col=1
                )

            # Volume Subplot
            if "Volume" in stock_data:
                vol_colors = ['#10b981' if c >= o else '#ef4444' for c, o in zip(stock_data['Close'], stock_data.get('Open', stock_data['Close']))]
                fig.add_trace(
                    go.Bar(
                        x=stock_data.index,
                        y=stock_data['Volume'],
                        name="Volume",
                        marker_color=vol_colors,
                        opacity=0.7
                    ),
                    row=2, col=1
                )

            fig.update_layout(
                template="plotly_white",
                height=520,
                margin=dict(l=20, r=20, t=10, b=10),
                hovermode="x unified",
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        with dash_col2:
            st.markdown("##### 📋 Key Market Stats")
            
            close_s = stock_data['Close'].dropna()
            latest_price = float(close_s.iloc[-1]) if not close_s.empty else 0.0
            prev_price = float(close_s.iloc[-2]) if len(close_s) >= 2 else latest_price
            price_delta = latest_price - prev_price
            price_delta_pct = (price_delta / prev_price) * 100 if prev_price > 0 else 0.0

            st.metric(
                label=f"{selected_stock} Current Price",
                value=f"${latest_price:.2f}",
                delta=f"{price_delta_pct:+.2f}% (${price_delta:+.2f})"
            )

            # High / Low / Volume stats
            high_val = float(stock_data['High'].max()) if "High" in stock_data else 0.0
            low_val = float(stock_data['Low'].min()) if "Low" in stock_data else 0.0
            vol_mean = float(stock_data['Volume'].mean()) if "Volume" in stock_data else 0.0

            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-title">Period Range (Low - High)</div>
                <div class="stat-value" style="font-size: 1.15rem;">${low_val:.2f} — ${high_val:.2f}</div>
                <div class="stat-desc">Range over chosen timeframe</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Avg Daily Volume</div>
                <div class="stat-value" style="font-size: 1.15rem;">{vol_mean:,.0f}</div>
                <div class="stat-desc">Average shares traded per session</div>
            </div>
            """, unsafe_allow_html=True)

            # Quick Navigation actions
            st.markdown("##### ⚡ Quick Analysis Links")
            q_col1, q_col2 = st.columns(2)
            with q_col1:
                if st.button("📈 SMA vs EMA", use_container_width=True):
                    st.session_state.active_nav = "📈 SMA vs EMA"
                    st.rerun()
            with q_col2:
                if st.button("📋 Stock Summary", use_container_width=True):
                    st.session_state.active_nav = "📋 Stock Summary"
                    st.rerun()

        # Daily Return Distribution
        st.markdown("---")
        dist_col1, dist_col2 = st.columns([1.5, 1.5])
        
        with dist_col1:
            st.markdown("##### 📉 Daily Return Distribution & Volatility")
            stock_data['Daily Return'] = stock_data['Close'].pct_change()
            returns_clean = stock_data['Daily Return'].dropna()
            
            fig_hist = px.histogram(
                returns_clean,
                nbins=50,
                title=f"{selected_stock} Daily Return Frequency",
                color_discrete_sequence=['#2563eb']
            )
            fig_hist.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=35, b=20), xaxis_title="Daily % Return", yaxis_title="Count")
            st.plotly_chart(fig_hist, use_container_width=True)

        with dist_col2:
            st.markdown("##### 📌 Daily Return Statistics")
            if not returns_clean.empty:
                ret_mean = returns_clean.mean() * 100
                ret_std = returns_clean.std() * 100
                q05 = returns_clean.quantile(0.05) * 100
                q95 = returns_clean.quantile(0.95) * 100

                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-title">Expected Daily Return (Mean)</div>
                    <div class="stat-value">{ret_mean:+.3f}%</div>
                    <div class="stat-desc">Average expected daily price change</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Daily Volatility (Std Dev)</div>
                    <div class="stat-value">{ret_std:.3f}%</div>
                    <div class="stat-desc">Standard deviation of daily returns</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">95% Daily VaR Threshold</div>
                    <div class="stat-value" style="color: #ef4444;">{q05:.2f}%</div>
                    <div class="stat-desc">Worst single-day expected loss with 95% confidence</div>
                </div>
                """, unsafe_allow_html=True)


# ==========================================================
# VIEW 2: 💵 CURRENT STOCK PRICES
# ==========================================================
elif current_tab == "💵 Current Stock Prices":
    st.markdown("<h2 class='section-title'>💵 Current Stock Prices & Market Board</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>Live streaming prices, daily changes, day range, volume, and valuation metrics for all tracked equities.</p>", unsafe_allow_html=True)

    top_c1, top_c2 = st.columns([3, 1])
    with top_c2:
        if st.button("🔄 Refresh Live Quotes", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.toast("Updated market quotes successfully!")
            st.rerun()

    # Showcase cards for Popular Tech Equities
    featured_tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA"]
    featured_quotes = get_detailed_quotes_cached(tuple(featured_tickers))

    st.markdown("##### 🌟 Mega-Cap Leaders")
    f_cols = st.columns(len(featured_tickers))

    for idx, fq in enumerate(featured_quotes):
        with f_cols[idx]:
            p_val = f"${fq['price']:.2f}" if fq['price'] is not None else "N/A"
            if fq['pct_change'] is not None:
                d_val = f"{fq['pct_change']:+.2f}%"
                delta_color = "normal" if fq['pct_change'] >= 0 else "inverse"
            else:
                d_val = "0.00%"
                delta_color = "off"
            
            st.metric(label=f"{fq['ticker']}", value=p_val, delta=d_val, delta_color=delta_color)
            if st.button("🔍 Analyze", key=f"feat_btn_{fq['ticker']}", use_container_width=True):
                st.session_state.selected_ticker = fq['ticker']
                st.session_state.active_nav = "🏠 Home / Dashboard"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Master Board of all tracked stocks
    st.markdown("##### 📋 Complete Real-Time Market Table")
    
    table_tickers = list(dict.fromkeys(st.session_state.watchlist + tech_list + nyse_list + ['NVDA', 'TSLA', 'META', 'NFLX', 'AMD', 'SPY']))
    detailed_quotes = get_detailed_quotes_cached(tuple(table_tickers))

    # Search filter
    search_q = st.text_input("🔍 Search stock by symbol or company name", placeholder="e.g. AAPL, Microsoft, Tesla...").strip().lower()
    if search_q:
        detailed_quotes = [q for q in detailed_quotes if search_q in q['ticker'].lower() or search_q in q['name'].lower()]

    # Table Header
    col_w = [2.2, 1.4, 1.6, 1.8, 1.6, 1.6, 2.0]
    th1, th2, th3, th4, th5, th6, th7 = st.columns(col_w)
    th1.markdown("<span class='table-header'>Stock & Name</span>", unsafe_allow_html=True)
    th2.markdown("<span class='table-header'>Current Price</span>", unsafe_allow_html=True)
    th3.markdown("<span class='table-header'>Daily Change</span>", unsafe_allow_html=True)
    th4.markdown("<span class='table-header'>Day Range (L - H)</span>", unsafe_allow_html=True)
    th5.markdown("<span class='table-header'>52-Wk Range</span>", unsafe_allow_html=True)
    th6.markdown("<span class='table-header'>Market Cap</span>", unsafe_allow_html=True)
    th7.markdown("<span class='table-header'>Actions</span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 4px 0 12px 0; border: 1px solid #cbd5e1;'>", unsafe_allow_html=True)

    for item in detailed_quotes:
        s = item["ticker"]
        name = item["name"]
        price = item["price"]
        pct = item["pct_change"]
        change = item["change"]
        dh = item["day_high"]
        dl = item["day_low"]
        yh = item["year_high"]
        yl = item["year_low"]
        mcap = item["market_cap_str"]
        is_active = (s == selected_stock)

        price_str = f"${price:.2f}" if price is not None else "N/A"
        
        if pct is not None:
            sign = "+" if pct >= 0 else ""
            b_class = "stock-badge-pos" if pct >= 0 else "stock-badge-neg"
            arrow = "▲" if pct >= 0 else "▼"
            change_dollar_str = f" ({sign}${change:.2f})" if change is not None else ""
            badge_html = f"<span class='stock-badge {b_class}'>{arrow} {sign}{pct:.2f}%{change_dollar_str}</span>"
        else:
            badge_html = "<span style='color: #64748b;'>N/A</span>"

        day_range_str = f"${dl:.2f} — ${dh:.2f}" if (dl and dh) else "N/A"
        year_range_str = f"${yl:.2f} — ${yh:.2f}" if (yl and yh) else "N/A"
        active_chip = "<span class='active-tag'>Active</span>" if is_active else ""

        r1, r2, r3, r4, r5, r6, r7 = st.columns(col_w)
        r1.markdown(f"<div><strong>{s}</strong> {active_chip}<br><span style='font-size:0.82rem; color:#64748b;'>{name}</span></div>", unsafe_allow_html=True)
        r2.markdown(f"<div style='font-size:1.05rem; font-weight:700; margin-top:2px;'>{price_str}</div>", unsafe_allow_html=True)
        r3.markdown(f"<div style='margin-top:4px;'>{badge_html}</div>", unsafe_allow_html=True)
        r4.markdown(f"<div style='font-size:0.88rem; color:#334155; margin-top:4px;'>{day_range_str}</div>", unsafe_allow_html=True)
        r5.markdown(f"<div style='font-size:0.88rem; color:#334155; margin-top:4px;'>{year_range_str}</div>", unsafe_allow_html=True)
        r6.markdown(f"<div style='font-size:0.88rem; font-weight:600; color:#0f172a; margin-top:4px;'>{mcap}</div>", unsafe_allow_html=True)

        with r7:
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                if is_active:
                    st.button("Active", key=f"act_tbl_{s}", disabled=True, use_container_width=True)
                else:
                    if st.button("Select", key=f"sel_tbl_{s}", use_container_width=True):
                        st.session_state.selected_ticker = s
                        st.session_state.active_nav = "🏠 Home / Dashboard"
                        st.rerun()
            with act_col2:
                if st.button("SMA/EMA", key=f"sma_tbl_{s}", use_container_width=True):
                    st.session_state.selected_ticker = s
                    st.session_state.active_nav = "📈 SMA vs EMA"
                    st.rerun()

        st.markdown("<hr style='margin: 4px 0 6px 0; border: 0.5px solid #edf2f7;'>", unsafe_allow_html=True)


# ==========================================================
# VIEW 3: 📈 SMA VS EMA
# ==========================================================
elif current_tab == "📈 SMA vs EMA":
    st.markdown(f"<h2 class='section-title'>📈 SMA vs EMA Technical Analysis: {selected_stock}</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>Compare Simple Moving Averages against Exponential Moving Averages, evaluate momentum lags, and detect Golden/Death Cross trading signals.</p>", unsafe_allow_html=True)

    # Educational Card
    with st.expander("ℹ️ Understanding the Difference: SMA vs EMA", expanded=False):
        st.markdown("""
        * **Simple Moving Average (SMA)**: Calculates the arithmetic average price over a chosen window $N$. Every single day in the window carries equal weight ($1/N$). It provides a smooth baseline and acts as strong institutional support/resistance, but responds with a noticeable lag.
        * **Exponential Moving Average (EMA)**: Applies a weighted multiplier $\\alpha = \\frac{2}{N + 1}$ that gives significantly more weight to the most recent price action. It turns faster than SMA and alerts traders to emerging momentum breakouts or trend reversals earlier.
        * **Golden Cross**: Occurs when a shorter moving average (e.g. 20-day or 50-day) crosses **above** a longer moving average (e.g. 50-day or 200-day), signaling a bullish regime change.
        * **Death Cross**: Occurs when a shorter moving average crosses **below** a longer moving average, signaling an impending bearish downtrend.
        """)

    # Interactive Controls
    ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4 = st.columns(4)
    with ctrl_c1:
        short_window = st.slider("Short-Term Period (Days)", min_value=5, max_value=50, value=20, step=5)
    with ctrl_c2:
        long_window = st.slider("Long-Term Period (Days)", min_value=30, max_value=200, value=50, step=10)
    with ctrl_c3:
        chart_mode = st.selectbox("Price Plot Style", ["Candlestick", "Close Line"], index=0)
    with ctrl_c4:
        st.write("")
        st.write("")
        show_spread = st.checkbox("Show Momentum Spread (EMA - SMA)", value=True)

    # Fetch data
    stock_df = get_historical_data(selected_stock, start_date, end_date)

    if stock_df.empty or "Close" not in stock_df:
        st.error(f"No trading data available for {selected_stock} in the given date range.")
    else:
        close_series = stock_df['Close'].dropna()

        # Compute MAs
        stock_df[f'SMA_{short_window}'] = close_series.rolling(window=short_window).mean()
        stock_df[f'SMA_{long_window}'] = close_series.rolling(window=long_window).mean()
        stock_df[f'EMA_{short_window}'] = close_series.ewm(span=short_window, adjust=False).mean()
        stock_df[f'EMA_{long_window}'] = close_series.ewm(span=long_window, adjust=False).mean()
        stock_df['MA_Spread'] = stock_df[f'EMA_{short_window}'] - stock_df[f'SMA_{short_window}']

        latest_close = float(close_series.iloc[-1])
        curr_sma_s = float(stock_df[f'SMA_{short_window}'].dropna().iloc[-1])
        curr_ema_s = float(stock_df[f'EMA_{short_window}'].dropna().iloc[-1])
        curr_sma_l = float(stock_df[f'SMA_{long_window}'].dropna().iloc[-1])
        curr_ema_l = float(stock_df[f'EMA_{long_window}'].dropna().iloc[-1])
        curr_spread = float(stock_df['MA_Spread'].dropna().iloc[-1])

        # Signal Detection Logic
        ema_s_series = stock_df[f'EMA_{short_window}'].dropna()
        ema_l_series = stock_df[f'EMA_{long_window}'].dropna()

        crossover_msg = "No recent crossover event within current window."
        signal_type = "neutral"

        if len(ema_s_series) >= 2 and len(ema_l_series) >= 2:
            now_diff = ema_s_series.iloc[-1] - ema_l_series.iloc[-1]
            prev_diff = ema_s_series.iloc[-2] - ema_l_series.iloc[-2]

            if now_diff > 0 and prev_diff <= 0:
                crossover_msg = f"🔥 **BULLISH GOLDEN CROSS**: {short_window}-day EMA crossed above {long_window}-day EMA!"
                signal_type = "bullish"
            elif now_diff < 0 and prev_diff >= 0:
                crossover_msg = f"⚠️ **BEARISH DEATH CROSS**: {short_window}-day EMA crossed below {long_window}-day EMA!"
                signal_type = "bearish"
            elif latest_close > curr_ema_s and curr_ema_s > curr_ema_l:
                crossover_msg = f"🟢 **BULLISH ALIGNMENT**: Price (${latest_close:.2f}) > {short_window}D EMA (${curr_ema_s:.2f}) > {long_window}D EMA (${curr_ema_l:.2f}). Upward trend in progress."
                signal_type = "bullish"
            elif latest_close < curr_ema_s and curr_ema_s < curr_ema_l:
                crossover_msg = f"🔴 **BEARISH ALIGNMENT**: Price (${latest_close:.2f}) < {short_window}D EMA (${curr_ema_s:.2f}) < {long_window}D EMA (${curr_ema_l:.2f}). Downward pressure active."
                signal_type = "bearish"
            else:
                crossover_msg = f"🟡 **NEUTRAL / CONSOLIDATION**: Price is fluctuating between moving average bands."
                signal_type = "neutral"

        # Signal Banner
        box_class = f"signal-box-{signal_type}"
        st.markdown(f"<div class='{box_class}'>{crossover_msg}</div>", unsafe_allow_html=True)

        # Plotly Technical Chart
        if show_spread:
            fig_ma = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.75, 0.25])
        else:
            fig_ma = go.Figure()

        main_row = 1 if show_spread else None

        # Add price
        if chart_mode == "Candlestick" and all(k in stock_df for k in ["Open", "High", "Low", "Close"]):
            fig_ma.add_trace(
                go.Candlestick(
                    x=stock_df.index,
                    open=stock_df['Open'], high=stock_df['High'], low=stock_df['Low'], close=stock_df['Close'],
                    name="Candlestick", opacity=0.7
                ),
                row=main_row, col=1 if show_spread else None
            )
        else:
            fig_ma.add_trace(
                go.Scatter(x=stock_df.index, y=stock_df['Close'], name=f"{selected_stock} Price", line=dict(color='#0f172a', width=2)),
                row=main_row, col=1 if show_spread else None
            )

        # Add Moving Averages
        fig_ma.add_trace(
            go.Scatter(x=stock_df.index, y=stock_df[f'SMA_{short_window}'], name=f'SMA ({short_window})', line=dict(color='#2563eb', width=2.2)),
            row=main_row, col=1 if show_spread else None
        )
        fig_ma.add_trace(
            go.Scatter(x=stock_df.index, y=stock_df[f'EMA_{short_window}'], name=f'EMA ({short_window})', line=dict(color='#f97316', width=2.2, dash='dash')),
            row=main_row, col=1 if show_spread else None
        )
        fig_ma.add_trace(
            go.Scatter(x=stock_df.index, y=stock_df[f'SMA_{long_window}'], name=f'SMA ({long_window})', line=dict(color='#059669', width=2.2)),
            row=main_row, col=1 if show_spread else None
        )
        fig_ma.add_trace(
            go.Scatter(x=stock_df.index, y=stock_df[f'EMA_{long_window}'], name=f'EMA ({long_window})', line=dict(color='#dc2626', width=2.2, dash='dash')),
            row=main_row, col=1 if show_spread else None
        )

        # Spread Subplot
        if show_spread:
            spread_colors = ['#10b981' if v >= 0 else '#ef4444' for v in stock_df['MA_Spread']]
            fig_ma.add_trace(
                go.Bar(x=stock_df.index, y=stock_df['MA_Spread'], name=f"EMA({short_window}) - SMA({short_window}) Spread", marker_color=spread_colors),
                row=2, col=1
            )
            fig_ma.update_yaxes(title_text="Spread ($)", row=2, col=1)

        fig_ma.update_layout(
            template="plotly_white",
            height=580,
            margin=dict(l=20, r=20, t=10, b=10),
            hovermode="x unified",
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_ma, use_container_width=True)

        # Metric Comparison Grid
        m_c1, m_c2, m_c3, m_c4, m_c5 = st.columns(5)
        with m_c1:
            st.metric(f"Current Price", f"${latest_close:.2f}")
        with m_c2:
            st.metric(f"SMA ({short_window})", f"${curr_sma_s:.2f}", delta=f"{((latest_close - curr_sma_s) / curr_sma_s) * 100:+.2f}% vs Price")
        with m_c3:
            st.metric(f"EMA ({short_window})", f"${curr_ema_s:.2f}", delta=f"{((latest_close - curr_ema_s) / curr_ema_s) * 100:+.2f}% vs Price")
        with m_c4:
            st.metric(f"SMA ({long_window})", f"${curr_sma_l:.2f}", delta=f"{((latest_close - curr_sma_l) / curr_sma_l) * 100:+.2f}% vs Price")
        with m_c5:
            st.metric(f"EMA ({long_window})", f"${curr_ema_l:.2f}", delta=f"{((latest_close - curr_ema_l) / curr_ema_l) * 100:+.2f}% vs Price")


# ==========================================================
# VIEW 4: 📋 STOCK SUMMARY
# ==========================================================
elif current_tab == "📋 Stock Summary":
    st.markdown(f"<h2 class='section-title'>📋 Stock Summary & Fundamentals: {selected_stock}</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>Company profile, business description, valuation multiples, dividend profile, and financial health.</p>", unsafe_allow_html=True)

    with st.spinner(f"Retrieving corporate profile and fundamentals for {selected_stock}..."):
        summary_data = get_stock_summary_cached(selected_stock)

    # Header Card
    hdr_c1, hdr_c2 = st.columns([3, 1])
    with hdr_c1:
        st.markdown(f"""
        <div style="background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <div style="display: flex; align-items: baseline; gap: 12px;">
                <h2 style="margin: 0; color: #0f172a; font-weight: 800;">{summary_data['name']}</h2>
                <span style="font-size: 1.2rem; font-weight: 700; color: #2563eb;">({summary_data['ticker']})</span>
            </div>
            <div style="margin-top: 8px; color: #64748b; font-size: 0.95rem;">
                <strong>Sector:</strong> {summary_data['sector']} &nbsp;|&nbsp;
                <strong>Industry:</strong> {summary_data['industry']} &nbsp;|&nbsp;
                <strong>Headquarters:</strong> {summary_data['city']}, {summary_data['country']} &nbsp;|&nbsp;
                <strong>Employees:</strong> {summary_data['employees']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with hdr_c2:
        if summary_data['website']:
            st.link_button("🌐 Visit Official Website", summary_data['website'], use_container_width=True)
        if st.button("📈 View Price Chart", use_container_width=True):
            st.session_state.active_nav = "🏠 Home / Dashboard"
            st.rerun()

    # 52-Week Range Visual Gauge
    if summary_data['fifty_two_week_high'] and summary_data['fifty_two_week_low'] and active_quote['price']:
        yh = float(summary_data['fifty_two_week_high'])
        yl = float(summary_data['fifty_two_week_low'])
        cp = float(active_quote['price'])
        
        pct_range = max(0.0, min(100.0, ((cp - yl) / (yh - yl)) * 100)) if yh > yl else 50.0

        st.markdown(f"""
        <div class="stat-card">
            <div style="display: flex; justify-content: space-between; font-weight: 600; color: #475569; font-size: 0.88rem;">
                <span>52-Week Low: ${yl:.2f}</span>
                <span style="color: #0f172a; font-weight: 700;">Current: ${cp:.2f} ({pct_range:.1f}% of Range)</span>
                <span>52-Week High: ${yh:.2f}</span>
            </div>
            <div style="background: #e2e8f0; height: 10px; border-radius: 5px; margin-top: 8px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #3b82f6, #10b981); width: {pct_range:.1f}%; height: 100%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Business Overview
    with st.expander("📖 Business Profile & Operations Description", expanded=True):
        st.write(summary_data['description'])

    # Valuation & Key Metrics Tabs
    tab_val, tab_fin, tab_div = st.tabs(["📊 Valuation & Multiples", "💰 Financial Performance", "💵 Dividends & Trading Stats"])

    with tab_val:
        v1, v2, v3, v4 = st.columns(4)
        with v1:
            st.metric("Market Capitalization", summary_data['market_cap'])
            st.metric("Enterprise Value", summary_data['enterprise_value'])
        with v2:
            st.metric("Trailing P/E", summary_data['pe_trailing'])
            st.metric("Forward P/E", summary_data['pe_forward'])
        with v3:
            st.metric("PEG Ratio", summary_data['peg_ratio'])
            st.metric("Price to Book (P/B)", summary_data['price_to_book'])
        with v4:
            st.metric("Price to Sales (P/S)", summary_data['price_to_sales'])
            st.metric("Beta (Volatility)", summary_data['beta'])

    with tab_fin:
        f1, f2, f3 = st.columns(3)
        with f1:
            st.metric("Total Revenue (TTM)", summary_data['total_revenue'])
            st.metric("Gross Profit", summary_data['gross_profit'])
        with f2:
            st.metric("Profit Margin", summary_data['profit_margin'])
            st.metric("Operating Margin", summary_data['operating_margin'])
        with f3:
            st.metric("Return on Assets (ROA)", summary_data['return_on_assets'])
            st.metric("Return on Equity (ROE)", summary_data['return_on_equity'])

    with tab_div:
        d1, d2, d3 = st.columns(3)
        with d1:
            st.metric("Dividend Rate", summary_data['dividend_rate'])
            st.metric("Dividend Yield", summary_data['dividend_yield'])
        with d2:
            st.metric("Payout Ratio", summary_data['payout_ratio'])
            st.metric("52-Week Price Change", summary_data['fifty_two_week_change'])
        with d3:
            st.metric("50-Day Moving Average", summary_data['fifty_day_average'])
            st.metric("200-Day Moving Average", summary_data['two_hundred_day_average'])


# ==========================================================
# VIEW 5: ⭐ WATCHLIST
# ==========================================================
elif current_tab == "⭐ Watchlist":
    st.markdown("<h2 class='section-title'>⭐ My Stock Watchlist</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>Add stocks to your custom watchlist, monitor live market movements, and launch one-click technical investigations.</p>", unsafe_allow_html=True)

    # Add Stock Form
    with st.form(key="add_stock_to_watchlist_form", clear_on_submit=True):
        st.markdown("##### ➕ Add Stock to Watchlist")
        add_c1, add_c2, add_c3 = st.columns([3, 2.5, 1.5])
        with add_c1:
            dropdown_opts = ["-- Select from popular stocks --"] + [f"{sym} - {name}" for sym, name in wm.POPULAR_STOCKS.items()]
            dropdown_choice = st.selectbox("Select Popular Equities", options=dropdown_opts, index=0)
        with add_c2:
            ticker_input = st.text_input("Or Enter Any Ticker Symbol", placeholder="e.g. PLTR, AMD, DIS, COIN")
        with add_c3:
            st.write("")
            st.write("")
            add_submit = st.form_submit_button("➕ Add Stock", use_container_width=True, type="primary")

    if add_submit:
        target_add = ""
        if ticker_input and ticker_input.strip():
            target_add = ticker_input.strip().upper()
        elif dropdown_choice and not dropdown_choice.startswith("--"):
            target_add = dropdown_choice.split(" - ")[0].strip().upper()

        if not target_add:
            st.warning("⚠️ Please choose a stock from the dropdown or type a valid symbol.")
        elif target_add in st.session_state.watchlist:
            st.warning(f"⚠️ '{target_add}' is already present in your watchlist.")
        else:
            with st.spinner(f"Verifying market data for '{target_add}'..."):
                updated_wl, success, msg, status_t = wm.add_stock(st.session_state.watchlist, target_add)
                if success:
                    st.session_state.watchlist = updated_wl
                    st.session_state.selected_ticker = target_add
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    # Watchlist Display
    if not st.session_state.watchlist:
        st.info("ℹ️ Your watchlist is currently empty. Add stocks above to get started!")
        if st.button("🔄 Restore Default Watchlist (AAPL, GOOG, MSFT, AMZN, TSLA)"):
            st.session_state.watchlist = wm.load_watchlist()
            st.session_state.selected_ticker = st.session_state.watchlist[0]
            st.rerun()
    else:
        wl_quotes = get_detailed_quotes_cached(tuple(st.session_state.watchlist))

        # Metrics
        gainers = [d for d in wl_quotes if d['pct_change'] is not None and d['pct_change'] > 0]
        top_gainer = max(wl_quotes, key=lambda x: x['pct_change'] if x['pct_change'] is not None else -999) if wl_quotes else None

        wm_c1, wm_c2, wm_c3, wm_c4 = st.columns(4)
        with wm_c1:
            st.metric("Total Saved Stocks", f"{len(st.session_state.watchlist)}")
        with wm_c2:
            st.metric("Currently Active", f"{selected_stock}")
        with wm_c3:
            st.metric("Advancing Stocks", f"{len(gainers)} 📈")
        with wm_c4:
            if top_gainer and top_gainer['pct_change'] is not None:
                st.metric("Top Watchlist Mover", f"{top_gainer['ticker']}", f"{top_gainer['pct_change']:+.2f}%")
            else:
                st.metric("Top Watchlist Mover", "N/A")

        st.markdown("<br>", unsafe_allow_html=True)

        # Table Header
        w_col_w = [3.2, 1.8, 1.8, 1.8, 1.8, 1.0]
        wh1, wh2, wh3, wh4, wh5, wh6 = st.columns(w_col_w)
        wh1.markdown("<span class='table-header'>Stock & Name</span>", unsafe_allow_html=True)
        wh2.markdown("<span class='table-header'>Latest Price</span>", unsafe_allow_html=True)
        wh3.markdown("<span class='table-header'>Daily % Change</span>", unsafe_allow_html=True)
        wh4.markdown("<span class='table-header'>Day Range</span>", unsafe_allow_html=True)
        wh5.markdown("<span class='table-header'>Analyze</span>", unsafe_allow_html=True)
        wh6.markdown("<span class='table-header'>Remove</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 4px 0 12px 0; border: 1px solid #cbd5e1;'>", unsafe_allow_html=True)

        for item in wl_quotes:
            sym = item["ticker"]
            name = item["name"]
            price = item["price"]
            pct = item["pct_change"]
            change = item["change"]
            dh = item["day_high"]
            dl = item["day_low"]
            is_active = (sym == selected_stock)

            price_str = f"${price:.2f}" if price is not None else "N/A"
            if pct is not None:
                sign = "+" if pct >= 0 else ""
                b_class = "stock-badge-pos" if pct >= 0 else "stock-badge-neg"
                arrow = "▲" if pct >= 0 else "▼"
                change_dollar_str = f" ({sign}${change:.2f})" if change is not None else ""
                badge_html = f"<span class='stock-badge {b_class}'>{arrow} {sign}{pct:.2f}%{change_dollar_str}</span>"
            else:
                badge_html = "<span style='color: #64748b;'>N/A</span>"

            day_range_str = f"${dl:.2f} — ${dh:.2f}" if (dl and dh) else "N/A"
            active_chip = "<span class='active-tag'>Active</span>" if is_active else ""

            r1, r2, r3, r4, r5, r6 = st.columns(w_col_w)
            r1.markdown(f"<div><strong>{sym}</strong> {active_chip}<br><span style='font-size:0.82rem; color:#64748b;'>{name}</span></div>", unsafe_allow_html=True)
            r2.markdown(f"<div style='font-size:1.05rem; font-weight:700; margin-top:2px;'>{price_str}</div>", unsafe_allow_html=True)
            r3.markdown(f"<div style='margin-top:4px;'>{badge_html}</div>", unsafe_allow_html=True)
            r4.markdown(f"<div style='font-size:0.88rem; color:#334155; margin-top:4px;'>{day_range_str}</div>", unsafe_allow_html=True)

            with r5:
                if is_active:
                    st.button("Active", key=f"wl_act_{sym}", disabled=True, use_container_width=True)
                else:
                    if st.button("📊 Inspect", key=f"wl_view_{sym}", use_container_width=True):
                        st.session_state.selected_ticker = sym
                        st.session_state.active_nav = "🏠 Home / Dashboard"
                        st.rerun()

            with r6:
                if st.button("🗑️", key=f"wl_del_{sym}", help=f"Remove {sym} from watchlist", use_container_width=True):
                    updated_wl, success, msg = wm.remove_stock(st.session_state.watchlist, sym)
                    st.session_state.watchlist = updated_wl
                    if st.session_state.selected_ticker == sym:
                        st.session_state.selected_ticker = updated_wl[0] if updated_wl else "AAPL"
                    st.toast(msg)
                    st.rerun()

            st.markdown("<hr style='margin: 4px 0 6px 0; border: 0.5px solid #edf2f7;'>", unsafe_allow_html=True)


# ==========================================================
# VIEW 6: 🎲 RISK & MONTE CARLO
# ==========================================================
elif current_tab == "🎲 Risk & Monte Carlo":
    st.markdown(f"<h2 class='section-title'>🎲 Risk Analysis & Monte Carlo Simulation: {selected_stock}</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>Multi-asset correlation heatmap, risk vs return trade-off, and Geometric Brownian Motion simulations to project future outcomes.</p>", unsafe_allow_html=True)

    # Multi-stock basket data for correlation & risk
    basket_stocks = list(dict.fromkeys(([selected_stock] if selected_stock else []) + st.session_state.watchlist + tech_list + nyse_list))
    basket_df = get_multi_historical_data(tuple(basket_stocks), start_date, end_date)

    if not basket_df.empty and "Close" in basket_df:
        closing_prices = basket_df['Close']
        
        c_c1, c_c2 = st.columns(2)

        with c_c1:
            st.markdown("##### 🔍 Cross-Asset Correlation Heatmap")
            corr_candidates = [s for s in list(dict.fromkeys([selected_stock] + st.session_state.watchlist)) if s in closing_prices.columns]
            if len(corr_candidates) < 3:
                corr_candidates = [s for s in list(dict.fromkeys(corr_candidates + tech_list)) if s in closing_prices.columns]

            if len(corr_candidates) >= 2:
                corr_matrix = closing_prices[corr_candidates].pct_change().dropna().corr()
                fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale='YlGnBu')
                fig_corr.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=10, b=10))
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("Need at least 2 stocks with historical data to calculate correlation.")

        with c_c2:
            st.markdown(f"##### ⚖️ Risk vs Expected Return (Focus: {selected_stock})")
            avail_cols = [s for s in basket_stocks if s in closing_prices.columns]
            if len(avail_cols) >= 2:
                rets_df = closing_prices[avail_cols].pct_change().dropna()
                risk_summary = pd.DataFrame({
                    'Expected Return': rets_df.mean(),
                    'Risk (Std Dev)': rets_df.std()
                })
                
                m_colors = ['#dc2626' if idx == selected_stock else '#2563eb' for idx in risk_summary.index]
                m_sizes = [22 if idx == selected_stock else 14 for idx in risk_summary.index]

                fig_risk = px.scatter(risk_summary, x='Expected Return', y='Risk (Std Dev)', text=risk_summary.index)
                fig_risk.update_traces(marker=dict(size=m_sizes, color=m_colors, line=dict(width=1.5, color='#0f172a')))
                fig_risk.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=10, b=10))
                st.plotly_chart(fig_risk, use_container_width=True)

    # Monte Carlo Section
    st.markdown("---")
    st.markdown(f"##### 🎲 Geometric Brownian Motion (GBM) Monte Carlo Simulation: {selected_stock}")

    target_data = get_historical_data(selected_stock, start_date, end_date)

    if target_data.empty or "Close" not in target_data:
        st.error(f"Cannot run simulation: no historical data for {selected_stock}.")
    else:
        sim_ctrl1, sim_ctrl2, sim_ctrl3 = st.columns([1, 1, 1.5])
        with sim_ctrl1:
            sim_runs = st.slider("Simulation Trials", min_value=1000, max_value=5000, value=2000, step=500)
        with sim_ctrl2:
            sim_days = st.number_input("Forecast Horizon (Trading Days)", min_value=30, max_value=365, value=252, step=30)
        with sim_ctrl3:
            st.write("")
            st.write("")
            launch_sim = st.button(f"🚀 Launch Simulation for {selected_stock}", type="primary", use_container_width=True)

        if launch_sim:
            t_rets = target_data['Close'].pct_change().dropna()
            
            if t_rets.empty:
                st.error("Insufficient returns data to estimate drift and volatility.")
            else:
                mu = t_rets.mean()
                sigma = t_rets.std()
                start_price_sim = float(target_data['Close'].dropna().iloc[-1])

                with st.spinner(f"Computing {sim_runs:,} randomized stochastic trajectories..."):
                    # Vectorized simulation for high performance
                    daily_shocks = np.random.normal(loc=mu, scale=sigma, size=(sim_days, sim_runs))
                    price_trajectories = np.zeros((sim_days, sim_runs))
                    price_trajectories[0, :] = start_price_sim

                    for t in range(1, sim_days):
                        price_trajectories[t, :] = price_trajectories[t-1, :] * (1 + daily_shocks[t, :])

                    final_prices = price_trajectories[-1, :]
                    mean_trajectory = price_trajectories.mean(axis=1)
                    q99 = float(np.percentile(final_prices, 1))
                    q95 = float(np.percentile(final_prices, 5))
                    mean_final = float(mean_trajectory[-1])
                    potential_gain = ((mean_final - start_price_sim) / start_price_sim) * 100

                mc_col1, mc_col2 = st.columns([2, 1.2])

                with mc_col1:
                    fig_fan = go.Figure()
                    
                    # Plot historical tail
                    tail_df = target_data['Close'].tail(90)
                    fig_fan.add_trace(go.Scatter(x=tail_df.index, y=tail_df.values, name="Recent History", line=dict(color="#0f172a", width=3)))

                    # Future dates
                    last_dt = target_data.index[-1]
                    future_dates = [last_dt + timedelta(days=i) for i in range(sim_days)]

                    # Plot sample trajectories
                    for i in range(min(40, sim_runs)):
                        fig_fan.add_trace(go.Scatter(
                            x=future_dates, y=price_trajectories[:, i],
                            mode='lines', line=dict(width=0.6, color='rgba(59, 130, 246, 0.15)'),
                            showlegend=False
                        ))

                    # Plot mean path
                    fig_fan.add_trace(go.Scatter(x=future_dates, y=mean_trajectory, name="Mean Projection", line=dict(color="#dc2626", width=2.8, dash='dash')))
                    fig_fan.update_layout(title=f"{selected_stock} Forecast Fan Chart ({sim_days} Trading Days)", template="plotly_white", margin=dict(l=20, r=20, t=35, b=20))
                    st.plotly_chart(fig_fan, use_container_width=True)

                with mc_col2:
                    st.markdown("##### 📊 Projected Risk Metrics")
                    st.success(f"**Mean Final Price:** ${mean_final:.2f} ({potential_gain:+.2f}%)")
                    st.warning(f"**95% Confidence Base:** ${q95:.2f}")
                    st.error(f"**99% Value at Risk (VaR):** ${start_price_sim - q99:.2f} per share")
                    st.info(f"Across {sim_runs:,} randomized market paths, there is a 1% statistical chance the price will settle below **${q99:.2f}** at the end of {sim_days} trading days.")

                # Final Price Distribution
                fig_final_dist = px.histogram(final_prices, nbins=80, title=f"Final Price Probability Distribution ({selected_stock})", color_discrete_sequence=['#475569'])
                fig_final_dist.add_vline(x=q99, line_width=3, line_dash="dash", line_color="red", annotation_text="1% VaR Level")
                fig_final_dist.add_vline(x=mean_final, line_width=2, line_dash="dot", line_color="green", annotation_text="Mean Forecast")
                fig_final_dist.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=35, b=20), xaxis_title="Simulated Final Price ($)", yaxis_title="Trials")
                st.plotly_chart(fig_final_dist, use_container_width=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>AlphaStock Intelligence Platform • Built with Streamlit, Plotly & yFinance</p>", unsafe_allow_html=True)
