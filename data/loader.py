import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

X_EQUITY_TICKERS = ["XLK", "XLY", "XLP", "XLE", "XLV", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF", "XBI", "XME", "XOP", "XHB", "XSD", "XRT", "XPH", "XES", "XAR", "XHS", "XHE", "XSW", "XTN", "XTL", "XNTK", "XITK"]
FI_TICKERS = ["TLT", "IEF", "TIP", "TBT", "GLD", "SLV", "VGIT", "VCLT", "VCIT", "HYG", "PFF", "MBB", "VNQ", "LQD", "AGG"]

def load_from_hf():
    """Reads the dataset from Hugging Face."""
    try:
        # Note: Use st.secrets if token is not in env
        token = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")
        path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset", token=token)
        return pd.read_csv(path, index_col=0, parse_dates=True)
    except Exception as e:
        print(f"Dataset load failed: {e}")
        return None

def seed_dataset_from_scratch():
    """Download full history from 2008 and upload to HF."""
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    master_df = pd.DataFrame()
    
    status = st.empty()
    progress_bar = st.progress(0)
    
    for i, t in enumerate(tickers):
        status.text(f"Seeding {t}...")
        try:
            # Fetching from 2008 for initial dataset
            data = yf.download(t, start="2008-01-01", progress=False)['Adj Close']
            master_df[t] = data
        except:
            continue
        progress_bar.progress((i + 1) / len(tickers))
    
    # Add SOFR
    sofr = web.DataReader('SOFR', 'fred', start="2008-01-01").ffill()
    master_df['SOFR_ANNUAL'] = sofr / 100
    master_df = master_df.sort_index().ffill()
    
    master_df.to_csv(FILENAME)
    
    # Upload
    api = HfApi()
    token = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")
    api.upload_file(
        path_or_fileobj=FILENAME,
        path_in_repo=FILENAME,
        repo_id=REPO_ID,
        repo_type="dataset",
        token=token
    )
    return master_df
