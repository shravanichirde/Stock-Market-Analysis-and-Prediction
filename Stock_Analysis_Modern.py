
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from datetime import datetime
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')
sns.set_style('whitegrid')

# List of stocks
tech_list = ['AAPL', 'GOOG', 'MSFT', 'AMZN'] # Google ticker is GOOG in yfinance
end = datetime.now()
start = datetime(end.year - 1, end.month, end.day)

print("Fetching tech stocks data...")
stocks = {}
for stock in tech_list:
    stocks[stock] = yf.download(stock, start=start, end=end)
    print(f"Downloaded {stock}")

# Section 1 - Basic Analysis
print("\nSection 1 - Basic Analysis")
aapl = stocks['AAPL']

# Plot closing price
plt.figure(figsize=(10, 4))
aapl['Close'].plot(legend=True)
plt.title('AAPL Closing Price')
plt.savefig('AAPL_Close.png')
print("Saved AAPL_Close.png")

# Plot volume
plt.figure(figsize=(10, 4))
aapl['Volume'].plot(legend=True)
plt.title('AAPL Sales Volume')
plt.savefig('AAPL_Volume.png')
print("Saved AAPL_Volume.png")

# Moving Averages
ma_day = [10, 20, 50, 100]
for ma in ma_day:
    column_name = f"MA for {ma} days"
    aapl[column_name] = aapl['Close'].rolling(window=ma).mean()

plt.figure(figsize=(10, 4))
aapl[['Close', 'MA for 10 days', 'MA for 20 days', 'MA for 50 days', 'MA for 100 days']].plot()
plt.title('AAPL Moving Averages')
plt.savefig('AAPL_MA.png')
print("Saved AAPL_MA.png")

# Section 2 - Daily Return Analysis
print("\nSection 2 - Daily Return Analysis")
aapl['Daily Return'] = aapl['Close'].pct_change()

plt.figure(figsize=(12, 4))
aapl['Daily Return'].plot(legend=True, linestyle='--', marker='o')
plt.title('AAPL Daily Return')
plt.savefig('AAPL_Daily_Return.png')
print("Saved AAPL_Daily_Return.png")

plt.figure(figsize=(10, 4))
sns.histplot(aapl['Daily Return'].dropna(), bins=100, kde=True, color='magenta')
plt.title('AAPL Daily Return Distribution')
plt.savefig('AAPL_Daily_Return_Dist.png')
print("Saved AAPL_Daily_Return_Dist.png")

# Closing Price Correlation
closing_df = yf.download(tech_list, start=start, end=end)['Close']
tech_rets = closing_df.pct_change()

# Heatmap Comparison
plt.figure(figsize=(10, 8))
sns.heatmap(tech_rets.corr(), annot=True, fmt=".3g", cmap='YlGnBu')
plt.title('Correlation Heatmap - Tech Returns')
plt.savefig('Tech_Returns_Corr.png')
print("Saved Tech_Returns_Corr.png")

# Risk vs Expected Return
rets = tech_rets.dropna()
area = np.pi * 20
plt.figure(figsize=(10, 7))
plt.scatter(rets.mean(), rets.std(), s=area)
plt.xlabel('Expected returns')
plt.ylabel('Risk')

for label, x, y in zip(rets.columns, rets.mean(), rets.std()):
    plt.annotate(
        label, 
        xy=(x, y), xytext=(50, 50),
        textcoords='offset points', ha='right', va='bottom',
        arrowprops=dict(arrowstyle='fancy', connectionstyle='arc3,rad=-0.3'))
plt.title('Risk vs Expected Returns')
plt.savefig('Risk_vs_Return.png')
print("Saved Risk_vs_Return.png")

# Section 3 - Monte Carlo Simulation
print("\nSection 3 - Monte Carlo Simulation")

def stock_monte_carlo(start_price, days, mu, sigma):
    dt = 1/days
    price = np.zeros(days)
    price[0] = start_price
    shock = np.zeros(days)
    drift = np.zeros(days)
    
    for x in range(1, days):
        shock[x] = np.random.normal(loc=mu * dt, scale=sigma * np.sqrt(dt))
        drift[x] = mu * dt
        price[x] = price[x-1] + (price[x-1] * (drift[x] + shock[x]))
        
    return price

# Example for Google
start_price = float(closing_df['GOOG'].iloc[-1])
days = 365
mu = rets.mean()['GOOG']
sigma = rets.std()['GOOG']

runs = 10000
simulations = np.zeros(runs)
print(f"Running {runs} Monte Carlo simulations for GOOG...")
for run in range(runs):
    simulations[run] = stock_monte_carlo(start_price, days, mu, sigma)[days-1]

# Value at Risk Quantile
q = np.percentile(simulations, 1)

plt.figure(figsize=(10, 6))
plt.hist(simulations, bins=200)
plt.figtext(0.6, 0.8, s=f'Start Price: ${start_price:.2f}')
plt.figtext(0.6, 0.7, s=f'Mean Final Price: ${simulations.mean():.2f}')
plt.figtext(0.6, 0.6, s=f'VaR(0.99): ${start_price - q:.2f}')
plt.figtext(0.15, 0.6, s=f"q(0.99): ${q:.2f}")
plt.axvline(x=q, linewidth=4, color='r')
plt.title(f"Final price distribution for Google Stock (GOOG) after {days} days", weight='bold')
plt.savefig('GOOG_Monte_Carlo.png')
print("Saved GOOG_Monte_Carlo.png")

# Repeat for NYSE stocks if needed (omitting for brevity in run check, can be added)
print("\nModernized analysis complete!")
