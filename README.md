# 📈 AlphaStock - Stock Market Analysis & Prediction Platform

A modern, interactive financial analytics and stock price forecasting platform built with Python, Streamlit, Plotly, and yFinance. 

---

## 🚀 Key Features & Navigation

The platform features a responsive top navigation bar designed for rapid technical analysis, real-time tracking, and quantitative risk management:

### 1. 🏠 Home / Dashboard
* **Benchmark Market Overview**: Real-time snapshot of market leaders (`SPY`, `QQQ`, `AAPL`, `MSFT`, `NVDA`).
* **Interactive Price Action**: Toggle between interactive **Candlestick** and **Line charts** with selectable Moving Average overlays (10, 20, 50, 100, 200 days).
* **Trading Volume Subplot**: Color-coded volume bars synchronized with price action.
* **Returns & Volatility Distribution**: Daily returns histogram, standard deviation, and 95% single-day VaR threshold.

### 2. 💵 Current Stock Prices
* **Mega-Cap Leaders Showcase**: Dedicated metric cards displaying live price, intraday dollar change, percentage change, and range.
* **Comprehensive Real-Time Market Table**: Full real-time quote board covering all tracked and watchlist equities with live sorting, search filter, day range, 52-week range, and market capitalization.
* **Instant Actions**: Switch the active analysis target or jump directly into technical indicators with a single click.

### 3. 📈 SMA vs EMA (Technical Analysis Workbench)
* **Comparative Moving Average Analysis**: Evaluate **Simple Moving Averages (SMA)** vs **Exponential Moving Averages (EMA)** across customizable short-term (5–50 days) and long-term (30–200 days) horizons.
* **Momentum Spread Indicator**: Visualize $(\text{EMA} - \text{SMA})$ momentum divergence subplots to detect trend acceleration or fading momentum.
* **Crossover & Trend Signals**:
  * 🟢 **Golden Cross**: Short-term moving average crosses above long-term moving average (Bullish breakout).
  * 🔴 **Death Cross**: Short-term moving average crosses below long-term moving average (Bearish breakdown).
  * **Trend Bias**: Status indicators categorizing market posture as *Strongly Bullish*, *Bullish*, *Neutral / Consolidating*, or *Bearish*.

### 4. 📋 Stock Summary & Fundamentals
* **Corporate Profile**: Sector, Industry, Headquarters, Website, and Full-Time Employees.
* **52-Week Range Visual Gauge**: Interactive position bar highlighting where current price trades relative to 52-week low and high extremes.
* **Business Overview**: In-depth narrative of corporate operations and business segments.
* **Financial Multiples & Health**:
  * **Valuation**: Market Cap, Enterprise Value, Trailing P/E, Forward P/E, PEG Ratio, Price-to-Book (P/B), Price-to-Sales (P/S), Beta.
  * **Profitability**: Revenue (TTM), Gross Profit, Operating Margins, Profit Margins, ROA, ROE, Diluted EPS.
  * **Dividends & Capital Structure**: Dividend Rate, Yield %, Payout Ratio, Shares Outstanding.

### 5. ⭐ Watchlist Management
* **Personalized Watchlist**: Add custom stock symbols with real-time ticker validation and lookup support for 30+ popular equities.
* **Persistence**: Automatically saved to [`watchlist.json`](watchlist.json).
* **Real-time Monitoring**: Track percentage changes, top gainers, and manage saved symbols.

### 6. 🎲 Risk & Monte Carlo Simulation
* **Cross-Asset Correlation**: Pairwise correlation heatmap across portfolio and benchmark equities.
* **Risk vs Expected Return**: Scatter plot comparing expected returns ($\mu$) against volatility ($\sigma$).
* **Monte Carlo Stochastic Projections**:
  * Simulates up to 5,000 price paths using **Geometric Brownian Motion (GBM)** over customizable trading horizons (30–365 days).
  * Calculates mean price forecast, 95% confidence baseline, and 99% empirical Value at Risk (VaR).

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shravanichirde/Stock-Market-Analysis-and-Prediction.git
   cd Stock-Market-Analysis-and-Prediction
   ```

2. **Ensure branch is set to `main`**:
   ```bash
   git checkout main
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application**:
   ```bash
   streamlit run Stock_Dashboard.py
   ```
   *(Or alternatively: `streamlit run app.py`)*

---

## 📦 Project Structure

```
Stock-Market-Analysis-and-Prediction/
├── Stock_Dashboard.py        # Core application with responsive Navbar and full views
├── app.py                    # Application launcher
├── watchlist_manager.py      # Watchlist data management & quote services
├── watchlist.json            # Persistent user watchlist
├── requirements.txt          # Python dependencies
├── Stock_Analysis_Modern.py  # Standalone script for automated chart generation
└── README.md                 # Project documentation
```
