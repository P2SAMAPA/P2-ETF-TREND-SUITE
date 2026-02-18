import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
import time
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

# The 27 Equity X-ETFs and 15 FI ETFs from the 2025 Paper
X_EQUITY_TICKERS = ["XLK", "XLY", "XLP", "XLE", "XLV", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF", "XBI", "XME", "XOP", "XHB", "XSD", "XRT", "XPH", "XES", "XAR", "XHS", "XHE", "XSW", "XTN", "XTL", "XNTK", "XITK"]
FI_TICKERS = ["TLT", "IEF", "TIP", "TBT", "GLD", "SLV", "VGIT", "VCLT", "VCIT", "HYG", "PFF", "MBB", "VNQ", "LQD", "AGG"]

def get_hf_token():
    """Safely retrieves the token without triggering a SecretNotFoundError crash."""
    try:
        return st.secrets["HF_TOKEN"]
    except:
        return os.getenv("HF_TOKEN")

def load_from_hf():
    """Reads dataset from Hugging Face if it exists."""
    token = get_hf_token()
    if not token:
        return None
    try:
        path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset", token=token)
        return pd.read_csv(path, index_col=0, parse_dates=True)
    except:
        return None

def seed_dataset_from_scratch():
    """Downloads 2008-Present data from STOOQ."""
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    master_df = pd.DataFrame()
    
    status = st.empty()
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(tickers):
        status.text(f"Fetching {ticker} from Stooq...")
        try:
            # Stooq primary
            data = web.DataReader(f"{ticker}.US", 'stooq', start='2008-01-01')
            if not data.empty:
                master_df[ticker] = data['Close'].sort_index()
            time.sleep(0.6) # Anti-rate limit
        except:
            # YFinance fallback
            try:
                yf_data = yf.download(ticker, start="2008-01-01", progress=False)['Adj Close']
                master_df[ticker] = yf_data
            except:
                pass
        progress_bar.progress((i + 1) / len(tickers))

    # Add SOFR Rate
    try:
        sofr = web.DataReader('SOFR', 'fred', start="2008-01-01").ffill()
        master_df['SOFR_ANNUAL'] = sofr / 100
    except:
        master_df['SOFR_ANNUAL'] = 0.05

    master_df = master_df.sort_index().ffill()
    master_df.to_csv(FILENAME)
    
    upload_to_hf(FILENAME)
    return master_df

def sync_incremental_data(df_existing):
    """Updates only new data since last index date."""
    last_date = pd.to_datetime(df_existing.index).max()
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    
    # Simple incremental fetch
    new_data = yf.download(tickers, start=last_date, progress=False)['Adj Close']
    combined = pd.concat([df_existing, new_data])
    combined = combined[~combined.index.duplicated(keep='last')].sort_index()
    
    combined.to_csv(FILENAME)
    upload_to_hf(FILENAME)
    return combined

def upload_to_hf(path):
    api = HfApi()
    token = get_hf_token()
    api.upload_file(
        path_or_fileobj=path, 
        path_in_repo=FILENAME, 
        repo_id=REPO_ID, 
        repo_type="dataset", 
        token=token
    )
