
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# page config
st.set_page_config(page_title="Stock Market Insight", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1 {
        color: #1f77b4;
        font-family: 'Outfit', sans-serif;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Stock Market Analysis & Prediction")
st.markdown("---")

# Sidebar
st.sidebar.header("Configuration")
tech_list = ['AAPL', 'GOOG', 'MSFT', 'AMZN']
nyse_list = ['JNJ', 'NKE', 'WMT']
all_stocks = tech_list + nyse_list

selected_stock = st.sidebar.selectbox("Select Ticker for Detailed Analysis", all_stocks)
start_date = st.sidebar.date_input("Start Date", datetime(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())

# Data Fetching
@st.cache_data
def get_data(tickers, start, end):
    return yf.download(tickers, start=start, end=end)

data = get_data(all_stocks, start_date, end_date)
# Handle potential MultiIndex columns from yfinance
if isinstance(data.columns, pd.MultiIndex):
    closing_price = data['Close']
else:
    closing_price = data[['Close']]

# Main Section
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📈 {selected_stock} Performance")
    stock_data = yf.download(selected_stock, start=start_date, end=end_date)
    
    # Normalize Columns (Flatten MultiIndex if present)
    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = stock_data.columns.get_level_values(0)
    
    # Ensure stock_data['Close'] is a Series
    y_values = stock_data['Close']
    
    # Interactive Chart with Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock_data.index, y=y_values, name='Close Price', line=dict(color='#1f77b4', width=2)))
    
    ma_options = st.multiselect("Select Moving Averages", [10, 20, 50, 100], default=[20, 50])
    colors = {'10': '#ff7f0e', '20': '#2ca02c', '50': '#d62728', '100': '#9467bd'}
    
    for ma in ma_options:
        stock_data[f'MA_{ma}'] = stock_data['Close'].rolling(window=ma).mean()
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[f'MA_{ma}'], name=f'{ma} Day MA', line=dict(dash='dash', color=colors[str(ma)])))
    
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 Key Metrics")
    # Access values directly
    last_close = float(stock_data['Close'].iloc[-1])
    prev_close = float(stock_data['Close'].iloc[-2])
    delta = ((last_close - prev_close) / prev_close) * 100
    
    st.metric(label="Current Price", value=f"${last_close:.2f}", delta=f"{delta:.2f}%")
    
    vol_mean = float(stock_data['Volume'].mean())
    st.metric(label="Average Volume", value=f"{vol_mean:,.0f}")
    
    st.markdown("---")
    st.write("**Daily Return Analysis**")
    stock_data['Daily Return'] = stock_data['Close'].pct_change()
    fig_dist = px.histogram(stock_data.dropna(), x="Daily Return", nbins=50, title=f"Return Distribution", color_discrete_sequence=['#7f7f7f'])
    st.plotly_chart(fig_dist, use_container_width=True)

# Risk & Correlation
st.markdown("---")
st.header("🔍 Risk & Correlation Insights")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Correlation Heatmap")
    tech_rets = closing_price[tech_list].pct_change().dropna()
    fig_corr = px.imshow(tech_rets.corr(), text_auto=".2f", color_continuous_scale='YlGnBu')
    st.plotly_chart(fig_corr, use_container_width=True)

with c2:
    st.subheader("Risk vs Expected Return")
    tech_rets_all = closing_price.pct_change().dropna()
    risk_df = pd.DataFrame({
        'Expected Return': tech_rets_all.mean(),
        'Risk (Std Dev)': tech_rets_all.std()
    })
    fig_risk = px.scatter(risk_df, x='Expected Return', y='Risk (Std Dev)', text=risk_df.index, size_max=60)
    fig_risk.update_traces(marker=dict(size=15, color='#1f77b4', line=dict(width=2, color='DarkSlateGrey')))
    st.plotly_chart(fig_risk, use_container_width=True)

# Monte Carlo Prediction
st.markdown("---")
st.header("🎲 Monte Carlo Projection & Future Path")

sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    sim_runs = st.slider("Number of Simulations", 1000, 5000, 2000)
    sim_days = st.number_input("Prediction Horizon (Days)", value=252)
    run_sim = st.button("Run Simulation for " + selected_stock)

if run_sim:
    # Use stock-specific data for returns to avoid gaps in other stocks
    specific_rets = stock_data['Close'].pct_change().dropna()
    
    if specific_rets.empty:
        st.error(f"Not enough data to run simulation for {selected_stock}. Please try a wider date range.")
    else:
        mu = specific_rets.mean()
        sigma = specific_rets.std()
        start_p = float(stock_data['Close'].iloc[-1])
        
        # Daily simulation (dt = 1 day)
        sim_results = np.zeros((sim_days, sim_runs))
        
        for i in range(sim_runs):
            prices = [start_p]
            for _ in range(1, sim_days):
                # Daily drift and shock
                shock = np.random.normal(loc=mu, scale=sigma)
                next_price = prices[-1] * (1 + shock)
                prices.append(next_price)
            sim_results[:, i] = prices
    
    # Calculate quantiles and mean
    mean_path = sim_results.mean(axis=1)
    q99 = np.percentile(sim_results[-1, :], 1)
    q95 = np.percentile(sim_results[-1, :], 5)
    
    with sim_col2:
        # Prediction Chart
        fig_pred = go.Figure()
        
        # Historical Data (last 100 days for context)
        hist_data = stock_data['Close'].tail(100).squeeze()
        fig_pred.add_trace(go.Scatter(x=hist_data.index, y=hist_data.values, name="Historical", line=dict(color="#1f77b4", width=3)))
        
        # Projection Dates
        last_date = stock_data.index[-1]
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(sim_days)]
        
        # Plot a subset of paths (e.g., 50) for visualization
        for i in range(min(50, sim_runs)):
            fig_pred.add_trace(go.Scatter(x=future_dates, y=sim_results[:, i], 
                                        mode='lines', line=dict(width=0.5, color='rgba(158, 202, 225, 0.2)'),
                                        showlegend=False))
        
        # Mean Path
        fig_pred.add_trace(go.Scatter(x=future_dates, y=mean_path, name="Mean Forecast", line=dict(color="#d62728", width=3, dash='dash')))
        
        fig_pred.update_layout(title=f"Price Trajectory Forecast - {selected_stock}", template="plotly_white", xaxis_title="Date", yaxis_title="Price ($)")
        st.plotly_chart(fig_pred, use_container_width=True)
        
    st.markdown("### 📊 Distribution of Outcomes")
    dist_c1, dist_c2 = st.columns(2)
    
    with dist_c1:
        fig_dist = px.histogram(sim_results[-1, :], nbins=100, title="Probability Distribution of Final Price", color_discrete_sequence=['#7f7f7f'])
        fig_dist.add_vline(x=q99, line_width=4, line_dash="dash", line_color="red", annotation_text="1% Quantile")
        st.plotly_chart(fig_dist, use_container_width=True)
        
    with dist_c2:
        st.markdown(f"#### Simulation Insights for {selected_stock}")
        final_mean = mean_path[-1]
        potential_chg = ((final_mean - start_p) / start_p) * 100
        
        st.success(f"**Mean Predicted Price:** ${final_mean:.2f} ({potential_chg:+.2f}%)")
        st.warning(f"**95% Confidence Base:** ${q95:.2f}")
        st.error(f"**99% Value at Risk (VaR):** ${start_p - q99:.2f}")
        
        st.info(f"Based on {sim_runs} simulations over {sim_days} days, the model suggests a mean final price of ${final_mean:.2f}. There is a 1% probability the price could fall below ${q99:.2f}.")

st.markdown("---")
st.caption("Developed by Antigravity - Modern Stock Analysis Project")
