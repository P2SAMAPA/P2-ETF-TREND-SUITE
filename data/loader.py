import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
import time
from huggingface_hub import hf_hub_download, HfApi
import os
import streamlit as st

REPO_ID = "P2SAMAPA/etf_trend_data"
FILENAME = "market_data.csv"

def seed_dataset():
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    master_df = pd.DataFrame()
    
    st.info("🛰️ Initializing Stooq Data Fetch (2008-Present)...")
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(tickers):
        # Stooq ticker format is usually 'TICKER.US'
        stooq_symbol = f"{ticker}.US"
        try:
            # PRIMARY: STOOQ
            data = web.DataReader(stooq_symbol, 'stooq', start='2008-01-01')
            if not data.empty:
                # Stooq returns data in reverse chronological order; we sort it.
                master_df[ticker] = data['Close'].sort_index()
            
            # Anti-Rate Limit: 0.8s delay between requests
            time.sleep(0.8) 
            
        except Exception as e:
            st.warning(f"⚠️ Stooq failed for {ticker}. Attempting YFinance fallback...")
            try:
                # BACKUP: YFinance
                yf_data = yf.download(ticker, start="2008-01-01", progress=False)['Adj Close']
                master_df[ticker] = yf_data
            except:
                st.error(f"❌ Failed to fetch {ticker} from all sources.")
        
        progress_bar.progress((i + 1) / len(tickers))
    
    # Add SOFR (Cash Rate) from FRED
    try:
        sofr = web.DataReader('SOFR', 'fred', start="2008-01-01").ffill()
        master_df['SOFR_ANNUAL'] = sofr / 100
    except:
        master_df['SOFR_ANNUAL'] = 0.05 # Conservative fallback

    master_df = master_df.sort_index().ffill()
    
    # Save & Upload
    master_df.to_csv(FILENAME)
    upload_to_hf(FILENAME)
    return master_df
