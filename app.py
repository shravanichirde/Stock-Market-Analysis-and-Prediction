import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import watchlist_manager as wm

st.set_page_config(page_title="Stock Market Analysis & Watchlist", layout="wide")

st.title("📈 Stock Market Analysis & Watchlist App")

# Initialize session state for Watchlist
if "watchlist" not in st.session_state:
    st.session_state.watchlist = wm.load_watchlist()

if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = st.session_state.watchlist[0] if st.session_state.watchlist else "AAPL"

# Sidebar input
st.sidebar.header("Navigation & Settings")

all_options = list(dict.fromkeys([st.session_state.selected_stock] + st.session_state.watchlist + ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "NVDA"]))
def on_sidebar_change():
    st.session_state.selected_stock = st.session_state.sidebar_stock_pick

selected_idx = all_options.index(st.session_state.selected_stock) if st.session_state.selected_stock in all_options else 0
stock = st.sidebar.selectbox("Select Active Stock", all_options, index=selected_idx, key="sidebar_stock_pick", on_change=on_sidebar_change)
st.session_state.selected_stock = stock

start = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# ==========================================
# SECTION: My Watchlist
# ==========================================
st.header("⭐ My Watchlist")

# Add to Watchlist Form
with st.form("add_to_watchlist_form", clear_on_submit=True):
    col_a, col_b, col_c = st.columns([3, 2.5, 1.5])
    with col_a:
        dropdown_options = ["-- Select from popular stocks --"] + [f"{sym} - {name}" for sym, name in wm.POPULAR_STOCKS.items()]
        dropdown_choice = st.selectbox("Select from Popular Stocks", dropdown_options)
    with col_b:
        text_ticker = st.text_input("Or Enter Ticker Symbol", placeholder="e.g. NVDA, AMD, PLTR")
    with col_c:
        st.write("")
        st.write("")
        submit_add = st.form_submit_button("➕ Add Stock", use_container_width=True, type="primary")

if submit_add:
    ticker_to_add = ""
    if text_ticker and text_ticker.strip():
        ticker_to_add = text_ticker.strip().upper()
    elif dropdown_choice and not dropdown_choice.startswith("--"):
        ticker_to_add = dropdown_choice.split(" - ")[0].strip().upper()

    if not ticker_to_add:
        st.warning("⚠️ Please select a stock from the dropdown or enter a ticker symbol.")
    elif ticker_to_add in st.session_state.watchlist:
        st.warning(f"⚠️ '{ticker_to_add}' is already in your watchlist!")
    else:
        with st.spinner(f"Verifying ticker '{ticker_to_add}'..."):
            updated_wl, success, msg, status = wm.add_stock(st.session_state.watchlist, ticker_to_add)
            if success:
                st.session_state.watchlist = updated_wl
                st.session_state.selected_stock = ticker_to_add
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                if status == "warning":
                    st.warning(f"⚠️ {msg}")
                else:
                    st.error(f"❌ {msg}")

# Display Watchlist Table
if not st.session_state.watchlist:
    st.info("Your watchlist is currently empty. Add stocks above to get started!")
else:
    wl_quotes = wm.fetch_watchlist_data(st.session_state.watchlist)
    
    # Table Header
    h1, h2, h3, h4, h5 = st.columns([3.5, 2, 2.2, 2.3, 1.2])
    h1.markdown("**Stock Name & Ticker**")
    h2.markdown("**Latest Price**")
    h3.markdown("**Daily % Change**")
    h4.markdown("**Analysis Action**")
    h5.markdown("**Remove**")
    st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

    for item in wl_quotes:
        s = item["ticker"]
        name = item["name"]
        price = item["price"]
        pct = item["pct_change"]
        is_active = (s == st.session_state.selected_stock)

        price_str = f"${price:.2f}" if price is not None else "N/A"
        if pct is not None:
            sign = "+" if pct >= 0 else ""
            color = "#137333" if pct >= 0 else "#c5221f"
            bg = "#e6f4ea" if pct >= 0 else "#fce8e6"
            arrow = "▲" if pct >= 0 else "▼"
            pct_html = f"<span style='background-color:{bg}; color:{color}; padding:3px 8px; border-radius:12px; font-weight:600;'>{arrow} {sign}{pct:.2f}%</span>"
        else:
            pct_html = "N/A"

        active_badge = " <span style='background-color:#e8f0fe; color:#1a73e8; padding:2px 6px; border-radius:6px; font-size:0.8em;'>Active</span>" if is_active else ""

        c1, c2, c3, c4, c5 = st.columns([3.5, 2, 2.2, 2.3, 1.2])
        c1.markdown(f"**{s}**{active_badge}<br><span style='font-size:0.85em;color:#555;'>{name}</span>", unsafe_allow_html=True)
        c2.markdown(f"**{price_str}**")
        c3.markdown(pct_html, unsafe_allow_html=True)
        
        with c4:
            if is_active:
                st.button("🔍 Active", key=f"app_act_{s}", disabled=True, use_container_width=True)
            else:
                if st.button("📊 View Analysis", key=f"app_view_{s}", use_container_width=True):
                    st.session_state.selected_stock = s
                    st.rerun()

        with c5:
            if st.button("🗑️", key=f"app_del_{s}", help=f"Remove {s} from watchlist", use_container_width=True):
                updated_wl, success, msg = wm.remove_stock(st.session_state.watchlist, s)
                st.session_state.watchlist = updated_wl
                if st.session_state.selected_stock == s:
                    st.session_state.selected_stock = updated_wl[0] if updated_wl else "AAPL"
                st.rerun()

        st.markdown("<hr style='margin: 4px 0 8px 0; border: 0.5px solid #eee;'>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# SECTION: Detailed Analysis of Active Stock
# ==========================================
active_stock = st.session_state.selected_stock
st.header(f"📈 Detailed Analysis for {active_stock} ({wm.get_company_name(active_stock)})")

data = yf.download(active_stock, start=start, end=end)
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

if data.empty or "Close" not in data:
    st.error("Invalid stock symbol or no data found!")
else:
    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
        st.subheader(f"Recent Data for {active_stock}")
        st.write(data.tail())

    with col_metric2:
        close_series = pd.Series(data["Close"]).dropna()
        if len(close_series) >= 2:
            last_p = float(close_series.iloc[-1])
            prev_p = float(close_series.iloc[-2])
            chg = ((last_p - prev_p) / prev_p) * 100
            st.metric("Latest Price", f"${last_p:.2f}", f"{chg:+.2f}%")

    # Plot closing price & Moving average
    st.subheader(f"Closing Price Chart & 50-Day Moving Average ({active_stock})")
    data["MA50"] = data["Close"].rolling(50).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data.index, data["Close"], label="Close Price", color="#1f77b4", linewidth=1.5)
    ax.plot(data.index, data["MA50"], label="50-Day MA", color="#ff7f0e", linestyle="--", linewidth=1.5)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)
    st.pyplot(fig)

st.success("App is running successfully!")