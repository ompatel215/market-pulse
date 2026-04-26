import yfinance as yf
import pandas as pd


def fetch_stock_prices(ticker: str, period: str = "1mo") -> pd.DataFrame:
    """
    Fetch daily OHLCV for a ticker via yfinance.
    Returns a DataFrame with columns: date, open, high, low, close, volume.
    Returns empty DataFrame on failure.
    """
    try:
        data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if data.empty:
            return pd.DataFrame()

        data = data.reset_index()
        # yfinance returns MultiIndex columns when auto_adjust=True sometimes
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0].lower() if c[1] == '' or c[1] == ticker else c[0].lower() for c in data.columns]
        else:
            data.columns = [c.lower() for c in data.columns]

        data = data.rename(columns={"index": "date", "date": "date"})
        data["date"] = pd.to_datetime(data["date"]).dt.normalize()
        return data[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return pd.DataFrame()
