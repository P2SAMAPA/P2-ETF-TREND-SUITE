import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

# Explicitly define the lists first so they are available for export
X_EQUITY_TICKERS = ["XLK", "XLY", "XLP", "XLE", "XLV", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF", "XBI", "XME", "XOP", "XHB", "XSD", "XRT", "XPH", "XES", "XAR", "XHS", "XHE", "XSW", "XTN", "XTL", "XNTK", "XITK"]
FI_TICKERS = ["TLT", "IEF", "TIP", "TBT", "GLD", "SLV", "VGIT", "VCLT", "VCIT", "HYG", "PFF", "MBB", "VNQ", "LQD", "AGG"]

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

def get_safe_token():
    try: return st.secrets["HF_TOKEN"]
    except: return os.getenv("HF_TOKEN")

def load_from_hf():
    """Initial load function called by app.py"""
    token = get_safe_token()
    if not token: 
        return None
    try:
        path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset", token=token)
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df.ffill() # Handle internal NaNs immediately
    except Exception as e:
        st.error(f"HF Load Error: {e}")
        return None

def seed_dataset_from_scratch():
    """Initializes the CSV with full history"""
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    data = yf.download(tickers, start="2008-01-01", progress=False)
    
    # Robustly handle Column Multi-Index
    if 'Adj Close' in data.columns:
        master_df = data['Adj Close']
    else:
        master_df = data['Close']
    
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
    """The function triggered by the Sync Button"""
    if df is None:
        return seed_dataset_from_scratch()
        
    last_date = pd.to_datetime(df.index.max())
    sync_start = last_date + pd.Timedelta(days=1)
    
    # Check if data is already current to today
    if sync_start > pd.Timestamp.now().normalize():
        st.toast("Data is already up to date!", icon="✅")
        return df

    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    
    try:
        new_data_raw = yf.download(tickers, start=sync_start, progress=False)
        
        if new_data_raw.empty:
            st.toast("No new market sessions found.", icon="ℹ️")
            return df

        # Column selection
        if 'Adj Close' in new_data_raw.columns:
            new_data = new_data_raw['Adj Close']
        else:
            new_data = new_data_raw['Close']

        # Merge and clean
        combined = pd.concat([df, new_data]).sort_index()
        combined = combined[~combined.index.duplicated(keep='last')].ffill()
        
        # Save locally and push to cloud
        combined.to_csv(FILENAME)
        upload_to_hf(FILENAME)
        
        st.toast(f"Sync complete: {combined.index.max().date()}", icon="🚀")
        return combined
    except Exception as e:
        st.error(f"Sync failed: {e}")
        return df

def upload_to_hf(path):
    token = get_safe_token()
    if token:
        api = HfApi()
        api.upload_file(path_or_fileobj=path, path_in_repo=FILENAME, repo_id=REPO_ID, repo_type="dataset", token=token)
