import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

# Universes
X_EQUITY_TICKERS = ["XLK", "XLY", "XLP", "XLE", "XLV", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF", "XBI", "XME", "XOP", "XHB", "XSD", "XRT", "XPH", "XES", "XAR", "XHS", "XHE", "XSW", "XTN", "XTL", "XNTK", "XITK"]
FI_TICKERS = ["TLT", "IEF", "TIP", "TBT", "GLD", "SLV", "VGIT", "VCLT", "VCIT", "HYG", "PFF", "MBB", "VNQ", "LQD", "AGG"]

def seed_dataset_from_scratch():
    """Download full history from 2008 for all 42+ tickers and upload to HF."""
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    master_df = pd.DataFrame()
    
    progress_bar = st.progress(0)
    for i, t in enumerate(tickers):
        try:
            # We use yfinance for the heavy initial lift as it handles long historical ranges reliably
            data = yf.download(t, start="2008-01-01", progress=False)['Adj Close']
            master_df[t] = data
        except Exception as e:
            st.warning(f"Failed to fetch {t}: {e}")
        progress_bar.progress((i + 1) / len(tickers))
    
    # Add SOFR (Cash Interest)
    sofr = web.DataReader('SOFR', 'fred', start="2008-01-01").ffill()
    master_df['SOFR_ANNUAL'] = sofr / 100
    
    master_df = master_df.sort_index().ffill().dropna(how='all')
    
    # Save and Upload
    master_df.to_csv(FILENAME)
    upload_to_hf(FILENAME)
    return master_df

def upload_to_hf(local_path):
    """Pushes the local CSV to your Hugging Face Dataset repo."""
    api = HfApi()
    api.upload_file(
        path_or_fileobj=local_path,
        path_in_repo=FILENAME,
        repo_id=REPO_ID,
        repo_type="dataset",
        token=st.secrets["HF_TOKEN"]
    )

def load_from_hf():
    """Reads the dataset from Hugging Face."""
    try:
        path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset", token=st.secrets["HF_TOKEN"])
        return pd.read_csv(path, index_col=0, parse_dates=True)
    except:
        return None
