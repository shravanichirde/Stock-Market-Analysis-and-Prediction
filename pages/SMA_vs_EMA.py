import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import watchlist_manager as wm
import navbar

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="AlphaStock - SMA vs EMA Technical Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling matching AlphaStock theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    .main {
        background-color: #f8fafc;
    }
    
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
        font-size: 1.35rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stat-desc {
        font-size: 0.82rem;
        color: #64748b;
        margin-top: 4px;
    }

    .section-title {
        color: #0f172a;
        font-weight: 800;
        letter-spacing: -0.4px;
        margin-bottom: 2px;
    }
    .section-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 16px;
    }

    .signal-box-bullish {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 5px solid #22c55e;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    .signal-box-bearish {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 5px solid #ef4444;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    .signal-box-neutral {
        background: #fefce8;
        border: 1px solid #fef08a;
        border-left: 5px solid #eab308;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "watchlist" not in st.session_state:
    st.session_state.watchlist = wm.load_watchlist()

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = st.session_state.watchlist[0] if st.session_state.watchlist else "AAPL"

current_ticker = st.session_state.selected_ticker

# ==========================================================
# 1. SHARED BRAND BANNER & TOP NAVBAR
# ==========================================================
navbar.render_brand_banner(current_ticker)
navbar.render_navbar(current_page="sma_vs_ema")

# ==========================================================
# 2. PAGE HEADER
# ==========================================================
st.markdown(f"<h2 class='section-title'>📈 SMA vs EMA Technical Analysis: {current_ticker} ({wm.get_company_name(current_ticker)})</h2>", unsafe_allow_html=True)
st.markdown("<p class='section-subtitle'>Dedicated technical comparison between Simple Moving Averages and Exponential Moving Averages, crossover signal detection, and price momentum evaluation.</p>", unsafe_allow_html=True)

# ==========================================================
# 3. STOCK & DATE SELECTORS
# ==========================================================
filter_c1, filter_c2, filter_c3 = st.columns([1.5, 1.5, 1.2])

all_candidates = list(dict.fromkeys(
    [current_ticker] +
    st.session_state.watchlist +
    ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'SPY', 'QQQ', 'JNJ', 'WMT', 'NKE']
))

curr_idx = all_candidates.index(current_ticker) if current_ticker in all_candidates else 0

with filter_c1:
    selected_from_dropdown = st.selectbox(
        "Select Stock for Analysis",
        options=all_candidates,
        index=curr_idx,
        help="Choose from your watchlist or popular equities"
    )
    if selected_from_dropdown != current_ticker:
        st.session_state.selected_ticker = selected_from_dropdown
        current_ticker = selected_from_dropdown
        st.rerun()

with filter_c2:
    custom_sym = st.text_input("Or Enter Custom Ticker", placeholder="e.g. PLTR, COIN, DIS, AMD").strip().upper()
    if custom_sym and custom_sym != current_ticker:
        with st.spinner(f"Verifying ticker '{custom_sym}'..."):
            valid, clean_sym, err = wm.validate_ticker(custom_sym)
            if valid:
                st.session_state.selected_ticker = clean_sym
                current_ticker = clean_sym
                st.success(f"Loaded ticker {clean_sym}")
                st.rerun()
            else:
                st.error(f"⚠️ {err}")

with filter_c3:
    timeframe_preset = st.selectbox(
        "Timeframe Preset",
        ["1 Year", "6 Months", "3 Months", "2 Years", "5 Years", "Custom Date Range"],
        index=0
    )

# Determine date range based on preset
today = datetime.now()
if timeframe_preset == "1 Month":
    start_date = today - timedelta(days=30)
    end_date = today
elif timeframe_preset == "3 Months":
    start_date = today - timedelta(days=90)
    end_date = today
elif timeframe_preset == "6 Months":
    start_date = today - timedelta(days=180)
    end_date = today
elif timeframe_preset == "1 Year":
    start_date = today - timedelta(days=365)
    end_date = today
elif timeframe_preset == "2 Years":
    start_date = today - timedelta(days=730)
    end_date = today
elif timeframe_preset == "5 Years":
    start_date = today - timedelta(days=1825)
    end_date = today
else:
    d_c1, d_c2 = st.columns(2)
    with d_c1:
        start_date = st.date_input("Start Date", today - timedelta(days=365))
    with d_c2:
        end_date = st.date_input("End Date", today)

if start_date >= end_date:
    st.warning("Start Date must precede End Date. Reverting to 1 Year window.")
    start_date = end_date - timedelta(days=365)

# ==========================================================
# 4. CUSTOMIZABLE SMA & EMA PERIODS & CONTROLS
# ==========================================================
st.markdown("##### ⚙️ Moving Average Parameters")
p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns(5)

with p_c1:
    sma_short_period = st.number_input("Short SMA Period", min_value=2, max_value=200, value=20, step=1)
with p_c2:
    sma_long_period = st.number_input("Long SMA Period", min_value=5, max_value=500, value=50, step=5)
with p_c3:
    ema_short_period = st.number_input("Short EMA Period", min_value=2, max_value=200, value=20, step=1)
with p_c4:
    ema_long_period = st.number_input("Long EMA Period", min_value=5, max_value=500, value=50, step=5)
with p_c5:
    chart_view = st.selectbox("Chart Style", ["Candlestick", "Close Price Line"], index=0)

# Toggle checkboxes
t_c1, t_c2, t_c3, t_c4, t_c5 = st.columns(5)
with t_c1:
    show_sma_short = st.checkbox(f"Show SMA ({sma_short_period})", value=True)
with t_c2:
    show_ema_short = st.checkbox(f"Show EMA ({ema_short_period})", value=True)
with t_c3:
    show_sma_long = st.checkbox(f"Show SMA ({sma_long_period})", value=True)
with t_c4:
    show_ema_long = st.checkbox(f"Show EMA ({ema_long_period})", value=True)
with t_c5:
    show_spread_subplot = st.checkbox("Show Momentum Spread", value=True)

# ==========================================================
# 5. DATA FETCHING & ERROR / LOADING HANDLING
# ==========================================================
@st.cache_data(ttl=120)
def fetch_stock_history(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        return pd.DataFrame()

with st.spinner(f"Loading market data and calculating technical moving averages for {current_ticker}..."):
    stock_df = fetch_stock_history(current_ticker, start_date, end_date)

# Handle invalid tickers, empty response, or missing Close data
if stock_df.empty or "Close" not in stock_df or stock_df['Close'].dropna().empty:
    st.error(f"❌ **No market data available for '{current_ticker}'.**")
    st.info("Please verify that the ticker symbol is correct and that the selected date range contains active trading sessions.")
else:
    close_series = stock_df['Close'].dropna()

    # Verify if enough historical data points exist for the chosen periods
    max_requested_period = max(sma_short_period, sma_long_period, ema_short_period, ema_long_period)
    if len(close_series) < max_requested_period:
        st.warning(f"⚠️ The selected date range contains {len(close_series)} trading sessions, which is less than your longest moving average period ({max_requested_period}). Some moving averages may not render fully. Consider selecting a wider timeframe (e.g. 1 Year or 2 Years).")

    # Accurate Technical Calculations
    # 1. Simple Moving Average (SMA): rolling mean
    stock_df[f'SMA_Short'] = close_series.rolling(window=sma_short_period).mean()
    stock_df[f'SMA_Long'] = close_series.rolling(window=sma_long_period).mean()

    # 2. Exponential Moving Average (EMA): exponential weighted mean
    stock_df[f'EMA_Short'] = close_series.ewm(span=ema_short_period, adjust=False).mean()
    stock_df[f'EMA_Long'] = close_series.ewm(span=ema_long_period, adjust=False).mean()

    # 3. Momentum Spread between Short EMA and Short SMA
    stock_df['MA_Spread'] = stock_df['EMA_Short'] - stock_df['SMA_Short']

    # Latest values extraction
    latest_close = float(close_series.iloc[-1])
    prev_close = float(close_series.iloc[-2]) if len(close_series) >= 2 else latest_close
    price_change = latest_close - prev_close
    price_pct_change = (price_change / prev_close) * 100 if prev_close > 0 else 0.0

    curr_sma_s = float(stock_df['SMA_Short'].dropna().iloc[-1]) if not stock_df['SMA_Short'].dropna().empty else None
    curr_sma_l = float(stock_df['SMA_Long'].dropna().iloc[-1]) if not stock_df['SMA_Long'].dropna().empty else None
    curr_ema_s = float(stock_df['EMA_Short'].dropna().iloc[-1]) if not stock_df['EMA_Short'].dropna().empty else None
    curr_ema_l = float(stock_df['EMA_Long'].dropna().iloc[-1]) if not stock_df['EMA_Long'].dropna().empty else None
    curr_spread = float(stock_df['MA_Spread'].dropna().iloc[-1]) if not stock_df['MA_Spread'].dropna().empty else None

    # ==========================================================
    # 6. SIGNAL ANALYSIS & BRIEF COMPARISON
    # ==========================================================
    crossover_type = "neutral"
    crossover_title = "Neutral / Consolidating"
    crossover_details = "Moving averages are oscillating within a neutral consolidation range."

    # Golden Cross / Death Cross detection on Long vs Short EMA
    ema_s_series = stock_df['EMA_Short'].dropna()
    ema_l_series = stock_df['EMA_Long'].dropna()

    if len(ema_s_series) >= 2 and len(ema_l_series) >= 2:
        diff_now = ema_s_series.iloc[-1] - ema_l_series.iloc[-1]
        diff_prev = ema_s_series.iloc[-2] - ema_l_series.iloc[-2]

        if diff_now > 0 and diff_prev <= 0:
            crossover_type = "bullish"
            crossover_title = f"🔥 BULLISH GOLDEN CROSS DETECTED!"
            crossover_details = f"The {ema_short_period}-day EMA has crossed above the {ema_long_period}-day EMA in the latest session. This indicates an emerging bullish upward breakout."
        elif diff_now < 0 and diff_prev >= 0:
            crossover_type = "bearish"
            crossover_title = f"⚠️ BEARISH DEATH CROSS DETECTED!"
            crossover_details = f"The {ema_short_period}-day EMA has crossed below the {ema_long_period}-day EMA in the latest session. This indicates an impending bearish downward breakdown."
        elif curr_ema_s and curr_ema_l and latest_close > curr_ema_s and curr_ema_s > curr_ema_l:
            crossover_type = "bullish"
            crossover_title = "🟢 BULLISH TREND ALIGNMENT"
            crossover_details = f"Price (${latest_close:.2f}) is trading above Short EMA (${curr_ema_s:.2f}) and Long EMA (${curr_ema_l:.2f}). Bulls have control of the momentum."
        elif curr_ema_s and curr_ema_l and latest_close < curr_ema_s and curr_ema_s < curr_ema_l:
            crossover_type = "bearish"
            crossover_title = "🔴 BEARISH TREND ALIGNMENT"
            crossover_details = f"Price (${latest_close:.2f}) is trading below Short EMA (${curr_ema_s:.2f}) and Long EMA (${curr_ema_l:.2f}). Bears have control of the momentum."
        else:
            crossover_type = "neutral"
            crossover_title = "🟡 CONSOLIDATION / COMPRESSION"
            crossover_details = f"Price is fluctuating between moving average bands. Watch for a breakout above ${max(curr_sma_s or 0, curr_ema_s or 0):.2f} or breakdown below ${min(curr_sma_s or 0, curr_ema_s or 0):.2f}."

    # Render Signal Box
    signal_css = f"signal-box-{crossover_type}"
    st.markdown(f"""
    <div class="{signal_css}">
        <div style="font-weight: 700; font-size: 1.05rem; margin-bottom: 4px;">{crossover_title}</div>
        <div style="font-size: 0.92rem; color: #334155;">{crossover_details}</div>
    </div>
    """, unsafe_allow_html=True)

    # Key Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric(
            label="Latest Close Price",
            value=f"${latest_close:.2f}",
            delta=f"{price_pct_change:+.2f}% (${price_change:+.2f})"
        )
    with m2:
        if curr_sma_s is not None:
            dist_sma_s = ((latest_close - curr_sma_s) / curr_sma_s) * 100
            st.metric(label=f"SMA ({sma_short_period}D)", value=f"${curr_sma_s:.2f}", delta=f"{dist_sma_s:+.2f}% vs Price")
        else:
            st.metric(label=f"SMA ({sma_short_period}D)", value="N/A")
    with m3:
        if curr_ema_s is not None:
            dist_ema_s = ((latest_close - curr_ema_s) / curr_ema_s) * 100
            st.metric(label=f"EMA ({ema_short_period}D)", value=f"${curr_ema_s:.2f}", delta=f"{dist_ema_s:+.2f}% vs Price")
        else:
            st.metric(label=f"EMA ({ema_short_period}D)", value="N/A")
    with m4:
        if curr_sma_l is not None:
            dist_sma_l = ((latest_close - curr_sma_l) / curr_sma_l) * 100
            st.metric(label=f"SMA ({sma_long_period}D)", value=f"${curr_sma_l:.2f}", delta=f"{dist_sma_l:+.2f}% vs Price")
        else:
            st.metric(label=f"SMA ({sma_long_period}D)", value="N/A")
    with m5:
        if curr_ema_l is not None:
            dist_ema_l = ((latest_close - curr_ema_l) / curr_ema_l) * 100
            st.metric(label=f"EMA ({ema_long_period}D)", value=f"${curr_ema_l:.2f}", delta=f"{dist_ema_l:+.2f}% vs Price")
        else:
            st.metric(label=f"EMA ({ema_long_period}D)", value="N/A")

    # ==========================================================
    # 7. INTERACTIVE GRAPH WITH DISTINCT COLOURS
    # ==========================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📊 Interactive SMA vs EMA Technical Chart")

    if show_spread_subplot:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.75, 0.25],
            subplot_titles=(f"{current_ticker} Price & Moving Average Overlays", f"Momentum Spread: EMA({ema_short_period}) - SMA({sma_short_period})")
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # 1. Historical Closing Price / Candlestick
    if chart_view == "Candlestick" and all(c in stock_df for c in ["Open", "High", "Low", "Close"]):
        fig.add_trace(
            go.Candlestick(
                x=stock_df.index,
                open=stock_df['Open'],
                high=stock_df['High'],
                low=stock_df['Low'],
                close=stock_df['Close'],
                name=f"{current_ticker} Candlestick",
                increasing_line_color='#10b981',
                decreasing_line_color='#ef4444',
                opacity=0.65
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['Close'],
                name=f"{current_ticker} Close Price",
                line=dict(color='#0f172a', width=2.2)
            ),
            row=1, col=1
        )

    # 2. Short SMA (Solid Royal Blue)
    if show_sma_short and f'SMA_Short' in stock_df:
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['SMA_Short'],
                name=f"SMA ({sma_short_period}D) [Solid Blue]",
                line=dict(color='#2563eb', width=2.4)
            ),
            row=1, col=1
        )

    # 3. Short EMA (Dashed Amber/Orange)
    if show_ema_short and f'EMA_Short' in stock_df:
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['EMA_Short'],
                name=f"EMA ({ema_short_period}D) [Dashed Amber]",
                line=dict(color='#f59e0b', width=2.4, dash='dash')
            ),
            row=1, col=1
        )

    # 4. Long SMA (Solid Emerald Green)
    if show_sma_long and f'SMA_Long' in stock_df:
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['SMA_Long'],
                name=f"SMA ({sma_long_period}D) [Solid Green]",
                line=dict(color='#059669', width=2.4)
            ),
            row=1, col=1
        )

    # 5. Long EMA (Dashed Crimson Red)
    if show_ema_long and f'EMA_Long' in stock_df:
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['EMA_Long'],
                name=f"EMA ({ema_long_period}D) [Dashed Red]",
                line=dict(color='#dc2626', width=2.4, dash='dash')
            ),
            row=1, col=1
        )

    # Subplot: Momentum Spread Bar
    if show_spread_subplot and 'MA_Spread' in stock_df:
        spread_colors = ['#10b981' if val >= 0 else '#ef4444' for val in stock_df['MA_Spread'].fillna(0)]
        fig.add_trace(
            go.Bar(
                x=stock_df.index,
                y=stock_df['MA_Spread'],
                name="EMA - SMA Spread",
                marker_color=spread_colors,
                opacity=0.75
            ),
            row=2, col=1
        )
        fig.update_yaxes(title_text="Spread ($)", row=2, col=1)

    fig.update_layout(
        template="plotly_white",
        height=620,
        margin=dict(l=20, r=20, t=30, b=10),
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # ==========================================================
    # 8. DETAILED BRIEF COMPARISON & METRICS EXPLAINER
    # ==========================================================
    st.markdown("---")
    st.markdown("##### 📝 Comparative Performance & Momentum Breakdown")

    comp_c1, comp_c2 = st.columns(2)

    with comp_c1:
        spread_val = curr_spread if curr_spread is not None else 0.0
        lead_indicator = "EMA is leading SMA" if spread_val >= 0 else "SMA is lagging above EMA"
        lead_sign = "+" if spread_val >= 0 else ""
        lead_color = "#15803d" if spread_val >= 0 else "#b91c1c"

        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Short-Term Momentum Spread (EMA - SMA)</div>
            <div class="stat-value" style="color: {lead_color};">{lead_sign}${spread_val:.2f}</div>
            <div class="stat-desc">
                {lead_indicator}. When the spread is positive, recent price acceleration is pushing the faster EMA above the slower SMA, confirming upward momentum.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with comp_c2:
        if curr_sma_s and curr_ema_s:
            pct_diff_short = ((curr_ema_s - curr_sma_s) / curr_sma_s) * 100
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-title">Short-Term MA Divergence %</div>
                <div class="stat-value">{pct_diff_short:+.2f}%</div>
                <div class="stat-desc">
                    Percentage separation between the {ema_short_period}-day EMA and {sma_short_period}-day SMA. Higher divergence signals sharp trending behavior.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Educational Reference Card
    with st.expander("📚 Technical Reference: Formulas & Practical Trading Strategies", expanded=False):
        st.markdown("""
        ### Mathematical Formulas
        
        #### 1. Simple Moving Average (SMA)
        The Simple Moving Average is the unweighted arithmetic mean of the last $N$ closing prices:
        $$\\text{SMA}_t = \\frac{1}{N} \\sum_{i=0}^{N-1} P_{t-i}$$
        Where $P_t$ is the closing price on day $t$, and $N$ is the period length.
        
        #### 2. Exponential Moving Average (EMA)
        The Exponential Moving Average applies an exponential weighting multiplier $\\alpha$:
        $$\\alpha = \\frac{2}{N + 1}$$
        $$\\text{EMA}_t = (P_t \\times \\alpha) + (\\text{EMA}_{t-1} \\times (1 - \\alpha))$$
        Because $\\alpha > \\frac{1}{N}$, recent price changes exert significantly greater influence on $\\text{EMA}_t$ than older prices.

        ---

        ### Practical Tactical Differences for Traders
        | Feature | Simple Moving Average (SMA) | Exponential Moving Average (EMA) |
        | :--- | :--- | :--- |
        | **Weighting** | Equal weight for all $N$ days | Exponential decay, prioritizes recent days |
        | **Reaction Speed** | Slower, more lagged | Fast, sensitive to recent volatility |
        | **False Signals** | Fewer false breakouts | More sensitive to short-term whipsaws |
        | **Best For** | Major institutional support / resistance levels | Active trend entries and trailing stop-losses |
        """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>AlphaStock Intelligence Platform • Separate SMA vs EMA Technical Suite</p>", unsafe_allow_html=True)
