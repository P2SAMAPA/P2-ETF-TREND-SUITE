def load_data():
    import pandas as pd
    import yfinance as yf

    tickers = ["SPY", "QQQ", "TLT"]

    data = yf.download(
        tickers,
        start="2015-01-01",
        progress=False,
    )["Adj Close"]

    data = data.dropna()

    return data
