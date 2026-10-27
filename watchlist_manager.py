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
                    cleaned = list(dict.fromkeys(tickers))
                    if cleaned:
                        return cleaned
        except Exception:
            pass

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

    if not all(c.isalnum() or c in ".-" for c in ticker_clean):
        return False, ticker_clean, f"Invalid characters in ticker '{ticker_clean}'."

    try:
        hist = yf.Ticker(ticker_clean).history(period="5d")
        if hist is None or hist.empty:
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

    if ticker_clean in watchlist:
        return watchlist, False, f"'{ticker_clean}' is already in your watchlist.", "warning"

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
    """
    if not tickers:
        return []

    tickers_clean = [t.strip().upper() for t in tickers if t and str(t).strip()]
    if not tickers_clean:
        return []

    results = []

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


def format_large_number(num):
    """Format large numbers into human-readable K, M, B, T strings."""
    if num is None:
        return "N/A"
    try:
        val = float(num)
        if abs(val) >= 1e12:
            return f"${val / 1e12:.2f}T"
        elif abs(val) >= 1e9:
            return f"${val / 1e9:.2f}B"
        elif abs(val) >= 1e6:
            return f"${val / 1e6:.2f}M"
        elif abs(val) >= 1e3:
            return f"${val / 1e3:.2f}K"
        else:
            return f"${val:.2f}"
    except (ValueError, TypeError):
        return "N/A"


def fetch_detailed_quote(ticker):
    """
    Fetch comprehensive market metrics for a single ticker using fast_info & fallback.
    Returns a dict with price, change, day range, 52-week range, volume, and market cap.
    """
    sym = str(ticker).strip().upper()
    name = get_company_name(sym)
    result = {
        "ticker": sym,
        "name": name,
        "price": None,
        "prev_close": None,
        "change": None,
        "pct_change": None,
        "day_high": None,
        "day_low": None,
        "year_high": None,
        "year_low": None,
        "volume": None,
        "market_cap": None,
        "market_cap_str": "N/A",
        "currency": "USD"
    }

    try:
        t = yf.Ticker(sym)
        fi = getattr(t, "fast_info", None)
        if fi:
            try:
                last_p = getattr(fi, "last_price", None) or getattr(fi, "lastPrice", None)
                prev_c = getattr(fi, "previous_close", None) or getattr(fi, "previousClose", None) or getattr(fi, "regularMarketPreviousClose", None)
                if last_p is not None:
                    result["price"] = float(last_p)
                if prev_c is not None:
                    result["prev_close"] = float(prev_c)
                if result["price"] is not None and result["prev_close"] is not None and result["prev_close"] > 0:
                    result["change"] = result["price"] - result["prev_close"]
                    result["pct_change"] = (result["change"] / result["prev_close"]) * 100

                dh = getattr(fi, "day_high", None) or getattr(fi, "dayHigh", None)
                dl = getattr(fi, "day_low", None) or getattr(fi, "dayLow", None)
                yh = getattr(fi, "year_high", None) or getattr(fi, "yearHigh", None)
                yl = getattr(fi, "year_low", None) or getattr(fi, "yearLow", None)
                vol = getattr(fi, "last_volume", None) or getattr(fi, "lastVolume", None)
                mcap = getattr(fi, "market_cap", None) or getattr(fi, "marketCap", None)

                if dh is not None: result["day_high"] = float(dh)
                if dl is not None: result["day_low"] = float(dl)
                if yh is not None: result["year_high"] = float(yh)
                if yl is not None: result["year_low"] = float(yl)
                if vol is not None: result["volume"] = float(vol)
                if mcap is not None:
                    result["market_cap"] = float(mcap)
                    result["market_cap_str"] = format_large_number(mcap)
            except Exception:
                pass
    except Exception:
        pass

    # Fallback to history if fast_info missing price
    if result["price"] is None:
        try:
            hist = yf.Ticker(sym).history(period="5d")
            if hist is not None and not hist.empty:
                series = hist["Close"].dropna()
                if len(series) >= 2:
                    p = float(series.iloc[-1])
                    pc = float(series.iloc[-2])
                    result["price"] = p
                    result["prev_close"] = pc
                    result["change"] = p - pc
                    result["pct_change"] = ((p - pc) / pc) * 100
                elif len(series) == 1:
                    result["price"] = float(series.iloc[-1])
                    result["change"] = 0.0
                    result["pct_change"] = 0.0

                if "High" in hist and not hist["High"].empty:
                    result["day_high"] = float(hist["High"].dropna().iloc[-1])
                if "Low" in hist and not hist["Low"].empty:
                    result["day_low"] = float(hist["Low"].dropna().iloc[-1])
                if "Volume" in hist and not hist["Volume"].empty:
                    result["volume"] = float(hist["Volume"].dropna().iloc[-1])
        except Exception:
            pass

    return result


def fetch_detailed_quotes(tickers):
    """Fetch detailed quotes for a list of tickers."""
    cleaned = list(dict.fromkeys([str(t).strip().upper() for t in tickers if str(t).strip()]))
    return [fetch_detailed_quote(sym) for sym in cleaned]


def fetch_stock_summary(ticker):
    """
    Fetch in-depth company profile and fundamentals for the Stock Summary view.
    """
    sym = str(ticker).strip().upper()
    summary = {
        "ticker": sym,
        "name": get_company_name(sym),
        "sector": "N/A",
        "industry": "N/A",
        "country": "N/A",
        "city": "N/A",
        "website": "",
        "employees": "N/A",
        "description": "Business profile not available.",
        "market_cap": "N/A",
        "enterprise_value": "N/A",
        "pe_trailing": "N/A",
        "pe_forward": "N/A",
        "peg_ratio": "N/A",
        "price_to_book": "N/A",
        "price_to_sales": "N/A",
        "beta": "N/A",
        "dividend_rate": "N/A",
        "dividend_yield": "N/A",
        "payout_ratio": "N/A",
        "fifty_two_week_high": None,
        "fifty_two_week_low": None,
        "fifty_two_week_change": "N/A",
        "fifty_day_average": "N/A",
        "two_hundred_day_average": "N/A",
        "total_revenue": "N/A",
        "gross_profit": "N/A",
        "profit_margin": "N/A",
        "operating_margin": "N/A",
        "return_on_assets": "N/A",
        "return_on_equity": "N/A",
        "eps_trailing": "N/A",
        "shares_outstanding": "N/A"
    }

    try:
        t = yf.Ticker(sym)
        info = getattr(t, "info", {})
        if isinstance(info, dict) and info:
            summary["name"] = info.get("shortName") or info.get("longName") or summary["name"]
            summary["sector"] = info.get("sector") or "N/A"
            summary["industry"] = info.get("industry") or "N/A"
            summary["country"] = info.get("country") or "N/A"
            summary["city"] = info.get("city") or "N/A"
            summary["website"] = info.get("website") or ""
            if info.get("fullTimeEmployees"):
                summary["employees"] = f"{info['fullTimeEmployees']:,}"
            summary["description"] = info.get("longBusinessSummary") or info.get("description") or summary["description"]

            # Valuation & financial stats
            if info.get("marketCap"):
                summary["market_cap"] = format_large_number(info["marketCap"])
            if info.get("enterpriseValue"):
                summary["enterprise_value"] = format_large_number(info["enterpriseValue"])
            if info.get("trailingPE"):
                summary["pe_trailing"] = f"{info['trailingPE']:.2f}"
            if info.get("forwardPE"):
                summary["pe_forward"] = f"{info['forwardPE']:.2f}"
            if info.get("pegRatio"):
                summary["peg_ratio"] = f"{info['pegRatio']:.2f}"
            if info.get("priceToBook"):
                summary["price_to_book"] = f"{info['priceToBook']:.2f}"
            if info.get("priceToSalesTrailing12Months"):
                summary["price_to_sales"] = f"{info['priceToSalesTrailing12Months']:.2f}"
            if info.get("beta"):
                summary["beta"] = f"{info['beta']:.2f}"

            # Dividends
            if info.get("dividendRate"):
                summary["dividend_rate"] = f"${info['dividendRate']:.2f}"
            if info.get("dividendYield"):
                summary["dividend_yield"] = f"{info['dividendYield'] * 100:.2f}%"
            if info.get("payoutRatio"):
                summary["payout_ratio"] = f"{info['payoutRatio'] * 100:.2f}%"

            # 52-week & technicals
            summary["fifty_two_week_high"] = info.get("fiftyTwoWeekHigh")
            summary["fifty_two_week_low"] = info.get("fiftyTwoWeekLow")
            if info.get("52WeekChange"):
                summary["fifty_two_week_change"] = f"{info['52WeekChange'] * 100:+.2f}%"
            if info.get("fiftyDayAverage"):
                summary["fifty_day_average"] = f"${info['fiftyDayAverage']:.2f}"
            if info.get("twoHundredDayAverage"):
                summary["two_hundred_day_average"] = f"${info['twoHundredDayAverage']:.2f}"

            # Income & performance
            if info.get("totalRevenue"):
                summary["total_revenue"] = format_large_number(info["totalRevenue"])
            if info.get("grossProfits") or info.get("grossProfit"):
                summary["gross_profit"] = format_large_number(info.get("grossProfits") or info.get("grossProfit"))
            if info.get("profitMargins"):
                summary["profit_margin"] = f"{info['profitMargins'] * 100:.2f}%"
            if info.get("operatingMargins"):
                summary["operating_margin"] = f"{info['operatingMargins'] * 100:.2f}%"
            if info.get("returnOnAssets"):
                summary["return_on_assets"] = f"{info['returnOnAssets'] * 100:.2f}%"
            if info.get("returnOnEquity"):
                summary["return_on_equity"] = f"{info['returnOnEquity'] * 100:.2f}%"
            if info.get("trailingEps"):
                summary["eps_trailing"] = f"${info['trailingEps']:.2f}"
            if info.get("sharesOutstanding"):
                summary["shares_outstanding"] = format_large_number(info["sharesOutstanding"])
    except Exception as e:
        print(f"Error fetching summary for {sym}: {e}")

    return summary
