"""
navbar.py - Shared Professional Responsive Navigation Bar
Provides unified header, brand banner, and page navigation across AlphaStock.
"""
import streamlit as st
import watchlist_manager as wm

NAV_ITEMS = [
    ("🏠 Home / Dashboard", "dashboard"),
    ("💵 Current Stock Prices", "prices"),
    ("📈 SMA vs EMA", "sma_vs_ema"),
    ("📋 Stock Summary", "summary"),
    ("⭐ Watchlist", "watchlist"),
    ("🎲 Risk & Monte Carlo", "risk")
]


def render_brand_banner(active_ticker="AAPL"):
    """Render top brand header with active ticker chip."""
    quote = wm.fetch_detailed_quote(active_ticker)
    price_str = f"${quote['price']:.2f}" if quote['price'] is not None else "N/A"
    
    if quote['pct_change'] is not None:
        sign = "+" if quote['pct_change'] >= 0 else ""
        delta_str = f"{sign}{quote['pct_change']:.2f}%"
        chip_color = "#15803d" if quote['pct_change'] >= 0 else "#b91c1c"
        chip_bg = "#dcfce7" if quote['pct_change'] >= 0 else "#fee2e2"
    else:
        delta_str = "0.00%"
        chip_color = "#475569"
        chip_bg = "#f1f5f9"

    banner_html = f"""
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        padding: 16px 22px;
        border-radius: 14px;
        margin-bottom: 14px;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.08);
    ">
        <div>
            <h1 style="
                font-size: 1.55rem;
                font-weight: 800;
                letter-spacing: -0.5px;
                background: linear-gradient(90deg, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0;
            ">📈 AlphaStock Terminal</h1>
            <div style="font-size: 0.88rem; color: #94a3b8; margin-top: 2px;">
                Stock Market Technical Analysis, Live Prices & Monte Carlo Forecasting
            </div>
        </div>
        <div style="text-align: right;">
            <span style="
                background: {chip_bg};
                color: {chip_color};
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 0.88rem;
                font-weight: 700;
                display: inline-block;
                border: 1px solid rgba(0,0,0,0.06);
            ">🎯 Active: <strong>{active_ticker}</strong> • {price_str} ({delta_str})</span>
        </div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)


def switch_to_dashboard(target_section="🏠 Home / Dashboard"):
    """Helper to navigate to a specific section on the main dashboard."""
    st.session_state.active_nav = target_section
    try:
        st.switch_page("Stock_Dashboard.py")
    except Exception:
        try:
            st.switch_page("app.py")
        except Exception as e:
            st.error(f"Navigation error: {e}")


def switch_to_sma_vs_ema():
    """Helper to navigate to the separate SMA vs EMA page."""
    try:
        st.switch_page("pages/SMA_vs_EMA.py")
    except Exception as e:
        st.error(f"Navigation error: {e}")


def render_navbar(current_page="dashboard", active_tab=None):
    """
    Render responsive top navigation bar.
    
    current_page: 'dashboard' (homepage) or 'sma_vs_ema' (separate page)
    active_tab: The active tab string on the dashboard, e.g. '🏠 Home / Dashboard'
    """
    st.markdown("""
    <style>
    .navbar-container {
        background: #ffffff;
        border-radius: 14px;
        padding: 8px 12px;
        margin-bottom: 22px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
    }
    .navbar-container div[data-testid="stHorizontalBlock"] button {
        border-radius: 22px;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 6px 12px;
        transition: all 0.2s ease-in-out;
    }
    </style>
    <div class="navbar-container">
    """, unsafe_allow_html=True)

    cols = st.columns(len(NAV_ITEMS))

    for idx, (label, page_id) in enumerate(NAV_ITEMS):
        with cols[idx]:
            # Determine if this button represents the currently active view
            if current_page == "sma_vs_ema":
                is_active = (page_id == "sma_vs_ema")
            else:
                is_active = (label == active_tab) if active_tab else (page_id == "dashboard")

            # Button styling & action
            btn_type = "primary" if is_active else "secondary"
            btn_label = f"● {label}" if is_active else label

            if st.button(btn_label, key=f"nav_btn_{page_id}_{current_page}", type=btn_type, use_container_width=True):
                if page_id == "sma_vs_ema":
                    if current_page != "sma_vs_ema":
                        switch_to_sma_vs_ema()
                else:
                    if current_page == "sma_vs_ema":
                        switch_to_dashboard(label)
                    else:
                        st.session_state.active_nav = label
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
