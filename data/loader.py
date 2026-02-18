import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

X_EQUITY_TICKERS = ["XLK", "XLY", "XLP", "XLE", "XLV", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF", "XBI", "XME", "XOP", "XHB", "XSD", "XRT", "XPH", "XES", "XAR", "XHS", "XHE", "XSW", "XTN", "XTL", "XNTK", "XITK"]
FI_TICKERS = ["TLT", "IEF", "TIP", "TBT", "GLD", "SLV", "VGIT", "VCLT", "VCIT", "HYG", "PFF", "MBB", "VNQ", "LQD", "AGG"]

def load_from_hf():
    try:
        token = st.secrets["HF_TOKEN"]
        path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset", token=token)
        return pd.read_csv(path, index_col=0, parse_dates=True)
    except:
        return None

def seed_dataset():
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    # Download Wide Format
    df = yf.download(tickers, start="2008-01-01")['Adj Close']
    
    # Add SOFR
    sofr = web.DataReader('SOFR', 'fred', start="2008-01-01").ffill()
    df['SOFR_ANNUAL'] = sofr / 100
    df = df.sort_index().ffill()
    
    df.to_csv(FILENAME)
    upload_to_hf(FILENAME)
    return df

def upload_to_hf(path):
    api = HfApi()
    api.upload_file(path_or_fileobj=path, path_in_repo=FILENAME, repo_id=REPO_ID, repo_type="dataset", token=st.secrets["HF_TOKEN"])
