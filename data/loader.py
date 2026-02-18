import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
import time
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

# Make sure these match exactly what app.py expects
def load_from_hf():
    token = st.secrets.get("HF_TOKEN")
    if not token: return None
    try:
        path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset", token=token)
        return pd.read_csv(path, index_col=0, parse_dates=True)
    except:
        return None

def seed_dataset_from_scratch():
    # ... (Your Stooq download logic here)
    # Ensure this function name matches the import in app.py
    return master_df

def sync_incremental_data(df_existing):
    # ... (Your incremental update logic here)
    return combined
