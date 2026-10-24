import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import watchlist_manager as wm

# Page configuration
st.set_page_config(page_title="Stock Market Insight & Watchlist", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Premium Look & Modern Typography
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    .main {
        background-color: #f4f6fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #eef2f6;
    }
    h1 {
        color: #1f77b4;
        font-family: 'Outfit', sans-serif;
        text-align: center;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .watchlist-form-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .stock-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .stock-badge-pos {
        background-color: #e6f4ea;
        color: #137333;
    }
    .stock-badge-neg {
        background-color: #fce8e6;
        color: #c5221f;
    }
    .active-tag {
        background-color: #e8f0fe;
        color: #1a73e8;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        margin-left: 6px;
        display: inline-block;
    }
    .table-header {
        font-weight: 700;
        color: #4a5568;
        font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Stock Market Analysis & Watchlist Dashboard")
st.markdown("<p style='text-align: center; color: #555; margin-top: -10px; font-size: 1.05rem;'>Real-time Market Insights, Custom Watchlist Tracking & Monte Carlo Projections</p>", unsafe_allow_html=True)
st.markdown("---")

# Initialize session state for Watchlist and Selected Ticker
if "watchlist" not in st.session_state:
    st.session_state.watchlist = wm.load_watchlist()

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = st.session_state.watchlist[0] if st.session_state.watchlist else "AAPL"

# Configuration Baseline Stocks
tech_list = ['AAPL', 'GOOG', 'MSFT', 'AMZN']
nyse_list = ['JNJ', 'NKE', 'WMT']

# Combine all available stocks
all_available_stocks = list(dict.fromkeys(
    ([st.session_state.selected_ticker] if st.session_state.selected_ticker else []) +
    st.session_state.watchlist +
    tech_list +
    nyse_list +
    ['NVDA', 'TSLA', 'META', 'NFLX', 'AMD', 'SPY']
))

if st.session_state.selected_ticker not in all_available_stocks:
    all_available_stocks.insert(0, st.session_state.selected_ticker)

# Sidebar
st.sidebar.header("Configuration")

def on_sidebar_stock_select():
    st.session_state.selected_ticker = st.session_state.sidebar_ticker_picker

curr_idx = all_available_stocks.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in all_available_stocks else 0

selected_stock = st.sidebar.selectbox(
    "Select Ticker for Detailed Analysis",
    options=all_available_stocks,
    index=curr_idx,
    key="sidebar_ticker_picker",
    on_change=on_sidebar_stock_select
)
st.session_state.selected_ticker = selected_stock

start_date = st.sidebar.date_input("Start Date", datetime(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())

# Sidebar quick watchlist navigation
st.sidebar.markdown("---")
st.sidebar.markdown("### ⭐ Quick Watchlist Navigation")
st.sidebar.caption(f"{len(st.session_state.watchlist)} stocks in your watchlist")
for wl_sym in st.session_state.watchlist:
    is_active = (wl_sym == st.session_state.selected_ticker)
    btn_text = f"👉 {wl_sym} (Active)" if is_active else f"📈 {wl_sym}"
    if st.sidebar.button(btn_text, key=f"sidebar_btn_{wl_sym}", use_container_width=True, disabled=is_active):
        st.session_state.selected_ticker = wl_sym
        st.rerun()

# Data Fetching Helpers with Caching
@st.cache_data(ttl=120)
def get_historical_data(tickers_tuple, start, end):
    return yf.download(list(tickers_tuple), start=start, end=end)

@st.cache_data(ttl=60)
def get_watchlist_quotes(tickers_tuple):
    return wm.fetch_watchlist_data(list(tickers_tuple))

# ==========================================================
# SECTION: ⭐ My Watchlist
# ==========================================================
st.header("⭐ My Watchlist")
st.caption("Save your favourite stocks for quick access, track real-time price movements, and launch one-click in-depth analysis.")

# Add Stock Controls in a Form
with st.form(key="add_stock_form", clear_on_submit=True):
    st.markdown("##### ➕ Add Stock to Watchlist")
    add_c1, add_c2, add_c3 = st.columns([3, 2.5, 1.5])
    with add_c1:
        dropdown_options = ["-- Select from popular stocks --"] + [f"{sym} - {name}" for sym, name in wm.POPULAR_STOCKS.items()]
        dropdown_selection = st.selectbox(
            "Select Stock from Dropdown",
            options=dropdown_options,
            index=0,
            help="Choose from widely traded popular stocks"
        )
    with add_c2:
        custom_ticker_input = st.text_input(
            "Or Enter Ticker Symbol",
            placeholder="e.g. NVDA, PLTR, AMD, DIS",
            help="Type any valid US stock ticker symbol"
        )
    with add_c3:
        st.write("")
        st.write("")
        add_btn = st.form_submit_button("➕ Add Stock", use_container_width=True, type="primary")

# Handle Add Stock Submission
if add_btn:
    ticker_to_add = ""
    if custom_ticker_input and custom_ticker_input.strip():
        ticker_to_add = custom_ticker_input.strip().upper()
    elif dropdown_selection and not dropdown_selection.startswith("--"):
        ticker_to_add = dropdown_selection.split(" - ")[0].strip().upper()

    if not ticker_to_add:
        st.warning("⚠️ Please select a stock from the dropdown or enter a ticker symbol.")
    elif ticker_to_add in st.session_state.watchlist:
        # Requirement 6: If already in watchlist, do not add again. Display a suitable message.
        st.warning(f"⚠️ '{ticker_to_add}' is already in your watchlist!")
    else:
        with st.spinner(f"Verifying market data for '{ticker_to_add}'..."):
            updated_wl, success, msg, status_type = wm.add_stock(st.session_state.watchlist, ticker_to_add)
            if success:
                st.session_state.watchlist = updated_wl
                st.session_state.selected_ticker = ticker_to_add
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                if status_type == "warning":
                    st.warning(f"⚠️ {msg}")
                else:
                    st.error(f"❌ {msg}")

# Display Saved Stocks Table
if not st.session_state.watchlist:
    st.info("ℹ️ Your watchlist is currently empty. Use the section above to add favourite stocks!")
    if st.button("🔄 Restore Default Watchlist (AAPL, GOOG, MSFT, AMZN, TSLA)"):
        st.session_state.watchlist = wm.load_watchlist()
        st.session_state.selected_ticker = st.session_state.watchlist[0]
        st.rerun()
else:
    watchlist_quotes = get_watchlist_quotes(tuple(st.session_state.watchlist))
    
    # Watchlist Summary Metrics
    gainers = [d for d in watchlist_quotes if d['pct_change'] is not None and d['pct_change'] > 0]
    top_gainer = max(watchlist_quotes, key=lambda x: x['pct_change'] if x['pct_change'] is not None else -999) if watchlist_quotes else None

    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    with m_c1:
        st.metric("Total Saved Stocks", f"{len(st.session_state.watchlist)}")
    with m_c2:
        st.metric("Currently Analyzing", f"{st.session_state.selected_ticker}")
    with m_c3:
        st.metric("Stocks Advancing", f"{len(gainers)} 📈")
    with m_c4:
        if top_gainer and top_gainer['pct_change'] is not None:
            st.metric("Top Watchlist Mover", f"{top_gainer['ticker']}", f"{top_gainer['pct_change']:+.2f}%")
        else:
            st.metric("Top Watchlist Mover", "N/A")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Table Header
    th1, th2, th3, th4, th5 = st.columns([3.5, 2, 2.2, 2.3, 1.2])
    th1.markdown("<span class='table-header'>Stock Name & Ticker</span>", unsafe_allow_html=True)
    th2.markdown("<span class='table-header'>Latest Price</span>", unsafe_allow_html=True)
    th3.markdown("<span class='table-header'>Daily % Change</span>", unsafe_allow_html=True)
    th4.markdown("<span class='table-header'>Analysis Action</span>", unsafe_allow_html=True)
    th5.markdown("<span class='table-header'>Remove</span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: -5px; margin-bottom: 12px; border: 1px solid #cbd5e1;'>", unsafe_allow_html=True)

    # Table Rows
    for item in watchlist_quotes:
        sym = item["ticker"]
        name = item["name"]
        price = item["price"]
        pct_change = item["pct_change"]
        change = item["change"]
        is_active = (sym == st.session_state.selected_ticker)

        # Formatted Price
        price_str = f"${price:.2f}" if price is not None else "N/A"

        # Formatted Daily % Change
        if pct_change is not None:
            sign = "+" if pct_change >= 0 else ""
            badge_class = "stock-badge-pos" if pct_change >= 0 else "stock-badge-neg"
            arrow = "▲" if pct_change >= 0 else "▼"
            change_dollar_str = f" ({sign}${change:.2f})" if change is not None else ""
            change_html = f"<span class='stock-badge {badge_class}'>{arrow} {sign}{pct_change:.2f}%{change_dollar_str}</span>"
        else:
            change_html = "<span style='color: #666;'>N/A</span>"

        active_tag = "<span class='active-tag'>Active</span>" if is_active else ""
        name_html = f"<div><strong>{sym}</strong> {active_tag}<br><span style='font-size:0.85rem;color:#555;'>{name}</span></div>"

        r1, r2, r3, r4, r5 = st.columns([3.5, 2, 2.2, 2.3, 1.2])
        r1.markdown(name_html, unsafe_allow_html=True)
        r2.markdown(f"<div style='font-size: 1.1rem; font-weight: 600; margin-top: 4px;'>{price_str}</div>", unsafe_allow_html=True)
        r3.markdown(f"<div style='margin-top: 6px;'>{change_html}</div>", unsafe_allow_html=True)

        with r4:
            if is_active:
                st.button("🔍 Active", key=f"btn_act_{sym}", disabled=True, use_container_width=True)
            else:
                if st.button("📊 View Analysis", key=f"btn_ana_{sym}", use_container_width=True):
                    st.session_state.selected_ticker = sym
                    st.rerun()

        with r5:
            if st.button("🗑️", key=f"btn_del_{sym}", help=f"Remove {sym} from watchlist", use_container_width=True):
                updated_wl, success, msg = wm.remove_stock(st.session_state.watchlist, sym)
                st.session_state.watchlist = updated_wl
                if st.session_state.selected_ticker == sym:
                    st.session_state.selected_ticker = updated_wl[0] if updated_wl else "AAPL"
                st.toast(msg)
                st.rerun()

        st.markdown("<hr style='margin-top: 4px; margin-bottom: 6px; border: 0.5px solid #edf2f7;'>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================================
# SECTION: Detailed Analysis of Selected Stock
# ==========================================================
st.header(f"📈 Detailed Analysis: {selected_stock} ({wm.get_company_name(selected_stock)})")

col1, col2 = st.columns([2, 1])

# Fetch data for selected stock
stock_data = yf.download(selected_stock, start=start_date, end=end_date)
if isinstance(stock_data.columns, pd.MultiIndex):
    stock_data.columns = stock_data.columns.get_level_values(0)

if stock_data.empty or "Close" not in stock_data:
    st.error(f"⚠️ No trading data found for {selected_stock} between {start_date} and {end_date}. Try a wider date range.")
else:
    with col1:
        st.subheader("Price History & Moving Averages")
        y_values = stock_data['Close']
        if isinstance(y_values, pd.DataFrame):
            y_values = y_values.iloc[:, 0]

        # Interactive Chart with Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=stock_data.index, y=y_values, name=f'{selected_stock} Close Price', line=dict(color='#1f77b4', width=2.5)))
        
        ma_options = st.multiselect("Select Moving Averages", [10, 20, 50, 100], default=[20, 50])
        colors = {'10': '#ff7f0e', '20': '#2ca02c', '50': '#d62728', '100': '#9467bd'}
        
        for ma in ma_options:
            stock_data[f'MA_{ma}'] = stock_data['Close'].rolling(window=ma).mean()
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA_{ma}'], name=f'{ma}-Day MA', line=dict(dash='dash', color=colors[str(ma)])))
        
        fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📋 Key Metrics")
        close_series = pd.Series(stock_data['Close']).dropna()
        if len(close_series) >= 2:
            last_close = float(close_series.iloc[-1])
            prev_close = float(close_series.iloc[-2])
            delta = ((last_close - prev_close) / prev_close) * 100
            st.metric(label=f"{selected_stock} Current Price", value=f"${last_close:.2f}", delta=f"{delta:+.2f}%")
        elif len(close_series) == 1:
            st.metric(label=f"{selected_stock} Current Price", value=f"${float(close_series.iloc[-1]):.2f}")

        vol_series = pd.Series(stock_data['Volume']).dropna()
        if not vol_series.empty:
            vol_mean = float(vol_series.mean())
            st.metric(label="Average Volume", value=f"{vol_mean:,.0f}")
        
        st.markdown("---")
        st.write(f"**{selected_stock} Daily Return Distribution**")
        stock_data['Daily Return'] = stock_data['Close'].pct_change()
        fig_dist = px.histogram(stock_data.dropna(), x="Daily Return", nbins=50, title=f"Daily Return Distribution ({selected_stock})", color_discrete_sequence=['#1f77b4'])
        fig_dist.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_dist, use_container_width=True)

# ==========================================================
# SECTION: Risk & Correlation Insights
# ==========================================================
st.markdown("---")
st.header("🔍 Risk & Correlation Insights")

# Fetch basket data for multi-stock comparison
basket_stocks = list(dict.fromkeys(
    ([selected_stock] if selected_stock else []) + 
    st.session_state.watchlist + 
    tech_list + 
    nyse_list
))

basket_data = get_historical_data(tuple(basket_stocks), start_date, end_date)
if isinstance(basket_data.columns, pd.MultiIndex):
    closing_price = basket_data['Close']
else:
    closing_price = basket_data[['Close']]

c1, c2 = st.columns(2)

with c1:
    st.subheader("Correlation Heatmap")
    # Priority for correlation: selected stock + watchlist stocks + tech list
    corr_candidates = [s for s in list(dict.fromkeys([selected_stock] + st.session_state.watchlist)) if s in closing_price.columns]
    if len(corr_candidates) < 3:
        corr_candidates = [s for s in list(dict.fromkeys(corr_candidates + tech_list)) if s in closing_price.columns]
    
    if len(corr_candidates) >= 2:
        corr_rets = closing_price[corr_candidates].pct_change().dropna()
        fig_corr = px.imshow(corr_rets.corr(), text_auto=".2f", color_continuous_scale='YlGnBu')
        fig_corr.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Not enough stock data available to construct correlation heatmap.")

with c2:
    st.subheader(f"Risk vs Expected Return (Target: {selected_stock})")
    avail_cols = [s for s in basket_stocks if s in closing_price.columns]
    if len(avail_cols) >= 2:
        all_rets = closing_price[avail_cols].pct_change().dropna()
        risk_df = pd.DataFrame({
            'Expected Return': all_rets.mean(),
            'Risk (Std Dev)': all_rets.std()
        })
        # Distinct color and size for the selected stock
        marker_colors = ['#d62728' if idx == selected_stock else '#1f77b4' for idx in risk_df.index]
        marker_sizes = [20 if idx == selected_stock else 14 for idx in risk_df.index]
        
        fig_risk = px.scatter(risk_df, x='Expected Return', y='Risk (Std Dev)', text=risk_df.index)
        fig_risk.update_traces(marker=dict(size=marker_sizes, color=marker_colors, line=dict(width=2, color='DarkSlateGrey')))
        fig_risk.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_risk, use_container_width=True)
    else:
        st.info("Not enough stock data available to calculate risk metrics.")

# ==========================================================
# SECTION: Monte Carlo Simulation
# ==========================================================
st.markdown("---")
st.header(f"🎲 Monte Carlo Projection & Future Path: {selected_stock}")

sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    sim_runs = st.slider("Number of Simulations", 1000, 5000, 2000)
    sim_days = st.number_input("Prediction Horizon (Days)", value=252)
    run_sim = st.button(f"🚀 Run Simulation for {selected_stock}", type="primary", use_container_width=True)

if run_sim and not stock_data.empty and "Close" in stock_data:
    specific_rets = stock_data['Close'].pct_change().dropna()
    
    if specific_rets.empty:
        st.error(f"Not enough data to run simulation for {selected_stock}. Please try a wider date range.")
    else:
        mu = specific_rets.mean()
        sigma = specific_rets.std()
        start_p = float(pd.Series(stock_data['Close']).dropna().iloc[-1])
        
        # Daily simulation (dt = 1 day)
        sim_results = np.zeros((sim_days, sim_runs))
        
        for i in range(sim_runs):
            prices = [start_p]
            for _ in range(1, sim_days):
                shock = np.random.normal(loc=mu, scale=sigma)
                next_price = prices[-1] * (1 + shock)
                prices.append(next_price)
            sim_results[:, i] = prices
    
        mean_path = sim_results.mean(axis=1)
        q99 = np.percentile(sim_results[-1, :], 1)
        q95 = np.percentile(sim_results[-1, :], 5)
        
        with sim_col2:
            fig_pred = go.Figure()
            hist_data = stock_data['Close'].tail(100).squeeze()
            fig_pred.add_trace(go.Scatter(x=hist_data.index, y=hist_data.values, name="Historical", line=dict(color="#1f77b4", width=3)))
            
            last_date = stock_data.index[-1]
            future_dates = [last_date + pd.Timedelta(days=i) for i in range(sim_days)]
            
            for i in range(min(50, sim_runs)):
                fig_pred.add_trace(go.Scatter(x=future_dates, y=sim_results[:, i], 
                                            mode='lines', line=dict(width=0.5, color='rgba(158, 202, 225, 0.2)'),
                                            showlegend=False))
            
            fig_pred.add_trace(go.Scatter(x=future_dates, y=mean_path, name="Mean Forecast", line=dict(color="#d62728", width=3, dash='dash')))
            fig_pred.update_layout(title=f"Price Trajectory Forecast - {selected_stock}", template="plotly_white", xaxis_title="Date", yaxis_title="Price ($)")
            st.plotly_chart(fig_pred, use_container_width=True)
            
        st.markdown("### 📊 Distribution of Outcomes")
        dist_c1, dist_c2 = st.columns(2)
        
        with dist_c1:
            fig_dist = px.histogram(sim_results[-1, :], nbins=100, title=f"Probability Distribution of Final Price ({selected_stock})", color_discrete_sequence=['#7f7f7f'])
            fig_dist.add_vline(x=q99, line_width=4, line_dash="dash", line_color="red", annotation_text="1% Quantile")
            st.plotly_chart(fig_dist, use_container_width=True)
            
        with dist_c2:
            st.markdown(f"#### Simulation Insights for {selected_stock}")
            final_mean = mean_path[-1]
            potential_chg = ((final_mean - start_p) / start_p) * 100
            
            st.success(f"**Mean Predicted Price:** ${final_mean:.2f} ({potential_chg:+.2f}%)\n")
            st.warning(f"**95% Confidence Base:** ${q95:.2f}\n")
            st.error(f"**99% Value at Risk (VaR):** ${start_p - q99:.2f}\n")
            
            st.info(f"Based on {sim_runs} simulations over {sim_days} days, the model suggests a mean final price of ${final_mean:.2f}. There is a 1% probability the price could fall below ${q99:.2f}.")

st.markdown("---")
st.caption("Developed with ❤️ for Modern Stock Market Analysis & Watchlist Tracking")
