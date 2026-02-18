import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

# --- GLOBAL CONSTANTS ---
X_EQUITY_TICKERS = ["XLK", "XLY", "XLP", "XLE", "XLV", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF", "XBI", "XME", "XOP", "XHB", "XSD", "XRT", "XPH", "XES", "XAR", "XHS", "XHE", "XSW", "XTN", "XTL", "XNTK", "XITK"]
FI_TICKERS = ["TLT", "IEF", "TIP", "TBT", "GLD", "SLV", "VGIT", "VCLT", "VCIT", "HYG", "PFF", "MBB", "VNQ", "LQD", "AGG"]

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

def get_safe_token():
    try: return st.secrets["HF_TOKEN"]
    except: return os.getenv("HF_TOKEN")

def load_from_hf():
    token = get_safe_token()
    if not token: return None
    try:
        path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset", token=token)
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df.ffill()
    except: return None

def seed_dataset_from_scratch():
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    data = yf.download(tickers, start="2008-01-01", progress=False)
    master_df = data['Adj Close'] if 'Adj Close' in data.columns else data['Close']
    try:
        sofr = web.DataReader('SOFR', 'fred', start="2008-01-01").ffill()
        master_df['SOFR_ANNUAL'] = sofr / 100
    except:
        master_df['SOFR_ANNUAL'] = 0.045
    master_df = master_df.sort_index().ffill()
    master_df.to_csv(FILENAME)
    upload_to_hf(FILENAME)
    return master_df

def sync_incremental_data(df):
    """Syncs data and returns (df, success_bool)"""
    if df is None: return None, False
    last_date = pd.to_datetime(df.index.max())
    sync_start = last_date + pd.Timedelta(days=1)
    
    if sync_start > pd.Timestamp.now().normalize():
        return df, False

    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    try:
        new_data_raw = yf.download(tickers, start=sync_start, progress=False)
        if new_data_raw.empty: return df, False

        new_data = new_data_raw['Adj Close'] if 'Adj Close' in new_data_raw.columns else new_data_raw['Close']
        combined = pd.concat([df, new_data]).sort_index()
        combined = combined[~combined.index.duplicated(keep='last')].ffill()
        
        combined.to_csv(FILENAME)
        upload_to_hf(FILENAME)
        return combined, True
    except:
        return df, False

def upload_to_hf(path):
    token = get_safe_token()
    if token:
        api = HfApi()
        api.upload_file(path_or_fileobj=path, path_in_repo=FILENAME, repo_id=REPO_ID, repo_type="dataset", token=token)
