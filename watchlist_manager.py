import json
import os
import yfinance as yf
import pandas as pd

WATCHLIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.json")

# Default starting watchlist if no watchlist.json exists
DEFAULT_WATCHLIST = ["AAPL", "GOOG", "MSFT", "AMZN", "TSLA"]

# Curated lookup dictionary for popular company names for instant zero-latency loading
POPULAR_STOCKS = {
    "AAPL": "Apple Inc.",
    "GOOG": "Alphabet Inc. (Google)",
    "GOOGL": "Alphabet Inc. (Google Class A)",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com, Inc.",
    "TSLA": "Tesla, Inc.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms, Inc.",
    "NFLX": "Netflix, Inc.",
    "AMD": "Advanced Micro Devices, Inc.",
    "INTC": "Intel Corporation",
    "JNJ": "Johnson & Johnson",
    "NKE": "NIKE, Inc.",
    "WMT": "Walmart Inc.",
    "DIS": "The Walt Disney Company",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "MA": "Mastercard Incorporated",
    "KO": "The Coca-Cola Company",
    "PEP": "PepsiCo, Inc.",
    "COST": "Costco Wholesale Corporation",
    "CRM": "Salesforce, Inc.",
    "ADBE": "Adobe Inc.",
    "CSCO": "Cisco Systems, Inc.",
    "ORCL": "Oracle Corporation",
    "IBM": "International Business Machines",
    "UBER": "Uber Technologies, Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco QQQ Trust"
}


def load_watchlist():
    """Load the saved watchlist from watchlist.json or initialize with defaults."""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    tickers = [str(x).strip().upper() for x in data if str(x).strip()]
                    # Deduplicate while preserving order
                    cleaned = list(dict.fromkeys(tickers))
                    if cleaned:
                        return cleaned
        except Exception:
            pass

    # If file doesn't exist or is invalid, persist and return default watchlist
    save_watchlist(DEFAULT_WATCHLIST)
    return list(DEFAULT_WATCHLIST)


def save_watchlist(watchlist):
    """Save the watchlist tickers list to watchlist.json."""
    try:
        cleaned = list(dict.fromkeys([str(x).strip().upper() for x in watchlist if str(x).strip()]))
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving watchlist: {e}")
        return False


def get_company_name(ticker):
    """Retrieve full company name from lookup dictionary or yfinance info."""
    ticker_clean = str(ticker).strip().upper()
    if ticker_clean in POPULAR_STOCKS:
        return POPULAR_STOCKS[ticker_clean]

    try:
        t = yf.Ticker(ticker_clean)
        info = getattr(t, "info", {})
        if isinstance(info, dict):
            name = info.get("shortName") or info.get("longName")
            if name:
                return name
    except Exception:
        pass

    return f"{ticker_clean}"


def validate_ticker(ticker):
    """
    Validate that a ticker symbol is non-empty and has downloadable historical price data.
    Returns (is_valid: bool, cleaned_ticker: str, error_message: str).
    """
    if not ticker or not isinstance(ticker, str):
        return False, "", "Ticker symbol cannot be empty."

    ticker_clean = ticker.strip().upper()
    if not ticker_clean:
        return False, "", "Ticker symbol cannot be empty."

    # Characters validation: alphanumeric plus hyphens/dots
    if not all(c.isalnum() or c in ".-" for c in ticker_clean):
        return False, ticker_clean, f"Invalid characters in ticker '{ticker_clean}'."

    # Verify trading data availability via yfinance
    try:
        hist = yf.Ticker(ticker_clean).history(period="5d")
        if hist is None or hist.empty:
            # Fallback check with download
            df = yf.download(ticker_clean, period="5d", progress=False)
            if df is None or df.empty:
                return False, ticker_clean, f"No market data found for ticker '{ticker_clean}'. Please verify the symbol."
        return True, ticker_clean, ""
    except Exception as e:
        return False, ticker_clean, f"Could not verify ticker '{ticker_clean}': {e}"


def add_stock(watchlist, ticker):
    """
    Add a stock to the watchlist with duplicate checking and market verification.
    Returns (updated_watchlist, success: bool, message: str, status_type: str).
    status_type can be 'success', 'warning', or 'error'.
    """
    if not ticker or not str(ticker).strip():
        return watchlist, False, "Please enter or select a valid stock ticker symbol.", "warning"

    ticker_clean = ticker.strip().upper()

    # Requirement 6: If already in watchlist, do not add again. Display a suitable message.
    if ticker_clean in watchlist:
        return watchlist, False, f"'{ticker_clean}' is already in your watchlist.", "warning"

    # Validate ticker with market data
    is_valid, cleaned, err_msg = validate_ticker(ticker_clean)
    if not is_valid:
        return watchlist, False, err_msg, "error"

    updated_watchlist = list(watchlist) + [cleaned]
    save_watchlist(updated_watchlist)
    company_name = get_company_name(cleaned)
    return updated_watchlist, True, f"Added {company_name} ({cleaned}) to your watchlist!", "success"


def remove_stock(watchlist, ticker):
    """
    Remove a stock from the watchlist.
    Returns (updated_watchlist, success: bool, message: str).
    """
    ticker_clean = str(ticker).strip().upper()
    if ticker_clean in watchlist:
        updated_watchlist = [t for t in watchlist if t != ticker_clean]
        save_watchlist(updated_watchlist)
        return updated_watchlist, True, f"Removed '{ticker_clean}' from your watchlist."
    return watchlist, False, f"'{ticker_clean}' was not found in your watchlist."


def fetch_watchlist_data(tickers):
    """
    Fetch latest prices and daily percentage changes for a list of tickers.
    Returns a list of dicts:
    [
        {
            'ticker': 'AAPL',
            'name': 'Apple Inc.',
            'price': 180.25,
            'prev_close': 178.50,
            'change': 1.75,
            'pct_change': 0.98
        },
        ...
    ]
    """
    if not tickers:
        return []

    # Clean ticker list
    tickers_clean = [t.strip().upper() for t in tickers if t and str(t).strip()]
    if not tickers_clean:
        return []

    results = []

    # Attempt batch download for speed
    try:
        batch_df = yf.download(tickers_clean, period="5d", progress=False)
    except Exception:
        batch_df = None

    for ticker in tickers_clean:
        name = get_company_name(ticker)
        price = None
        prev_close = None
        change = None
        pct_change = None

        # Extract from batch download if available
        if batch_df is not None and not batch_df.empty and "Close" in batch_df:
            close_data = batch_df["Close"]
            series = None
            try:
                if isinstance(close_data, pd.DataFrame):
                    if ticker in close_data.columns:
                        series = close_data[ticker].dropna()
                    elif len(tickers_clean) == 1 and len(close_data.columns) == 1:
                        series = close_data.iloc[:, 0].dropna()
                elif isinstance(close_data, pd.Series):
                    series = close_data.dropna()

                if series is not None and len(series) >= 2:
                    price = float(series.iloc[-1])
                    prev_close = float(series.iloc[-2])
                    change = price - prev_close
                    pct_change = (change / prev_close) * 100
                elif series is not None and len(series) == 1:
                    price = float(series.iloc[-1])
                    prev_close = price
                    change = 0.0
                    pct_change = 0.0
            except Exception:
                pass

        # Fallback to individual ticker history if batch extraction was incomplete
        if price is None:
            try:
                hist = yf.Ticker(ticker).history(period="5d")
                if hist is not None and not hist.empty and "Close" in hist:
                    series = hist["Close"].dropna()
                    if len(series) >= 2:
                        price = float(series.iloc[-1])
                        prev_close = float(series.iloc[-2])
                        change = price - prev_close
                        pct_change = (change / prev_close) * 100
                    elif len(series) == 1:
                        price = float(series.iloc[-1])
                        prev_close = price
                        change = 0.0
                        pct_change = 0.0
            except Exception:
                pass

        results.append({
            "ticker": ticker,
            "name": name,
            "price": price,
            "prev_close": prev_close,
            "change": change,
            "pct_change": pct_change
        })

    return results
