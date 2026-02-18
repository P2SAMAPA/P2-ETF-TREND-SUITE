import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
import time
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

X_EQUITY_TICKERS = ["XLK", "XLY", "XLP", "XLE", "XLV", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF", "XBI", "XME", "XOP", "XHB", "XSD", "XRT", "XPH", "XES", "XAR", "XHS", "XHE", "XSW", "XTN", "XTL", "XNTK", "XITK"]
FI_TICKERS = ["TLT", "IEF", "TIP", "TBT", "GLD", "SLV", "VGIT", "VCLT", "VCIT", "HYG", "PFF", "MBB", "VNQ", "LQD", "AGG"]

def load_from_hf():
    try:
        token = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")
        if not token: return None
        path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset", token=token)
        return pd.read_csv(path, index_col=0, parse_dates=True)
    except:
        return None

def seed_dataset_from_scratch():
    # Include benchmarks SPY and AGG
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    master_df = pd.DataFrame()
    status = st.empty()
    progress = st.progress(0)
    
    for i, t in enumerate(tickers):
        status.text(f"Fetching {t} from Stooq...")
        try:
            data = web.DataReader(f"{t}.US", 'stooq', start='2008-01-01')
            if not data.empty:
                master_df[t] = data['Close'].sort_index()
            time.sleep(0.6)
        except:
            try:
                master_df[t] = yf.download(t, start="2008-01-01", progress=False)['Adj Close']
            except: pass
        progress.progress((i + 1) / len(tickers))

    # Add SOFR Rate
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
    last_date = df.index.max()
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    new_data = yf.download(tickers, start=last_date, progress=False)['Adj Close']
    combined = pd.concat([df, new_data]).sort_index()
    combined = combined[~combined.index.duplicated(keep='last')]
    combined.to_csv(FILENAME)
    upload_to_hf(FILENAME)
    return combined

def upload_to_hf(path):
    api = HfApi()
    token = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")
    api.upload_file(path_or_fileobj=path, path_in_repo=FILENAME, repo_id=REPO_ID, repo_type="dataset", token=token)
