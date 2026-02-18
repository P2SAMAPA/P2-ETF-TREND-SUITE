import pandas_datareader.data as web
import yfinance as yf
import pandas as pd
import streamlit as st

# 27 "X-" EQUITY ETFS
X_EQUITY_TICKERS = [
    "XLK", "XLY", "XLP", "XLE", "XLV", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF",
    "XBI", "XME", "XOP", "XHB", "XSD", "XRT", "XPH", "XES", "XAR", "XHS", "XHE", 
    "XSW", "XTN", "XTL", "XNTK", "XITK"
]

# 15 FIXED INCOME / COMPARISON
FI_TICKERS = ["TLT", "IEF", "TIP", "TBT", "GLD", "SLV", "VGIT", "VCLT", "VCIT", "HYG", "PFF", "MBB", "VNQ", "LQD", "AGG"]

def refresh_market_data():
    """Syncs Stooq/FRED data to local CSV and HF."""
    all_prices = {}
    # Download all groups + SPY Benchmark
    for t in list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY"])):
        try:
            all_prices[t] = web.DataReader(f"{t}.US", "stooq")['Close']
        except:
            all_prices[t] = yf.download(t, progress=False)['Adj Close']
            
    # Fetch SOFR (Cash Yield) from FRED
    sofr = web.DataReader('SOFR', 'fred').ffill()
    
    df = pd.DataFrame(all_prices).sort_index().ffill()
    df['SOFR_ANNUAL'] = sofr / 100
    df.to_csv("market_data.csv")
    return df
