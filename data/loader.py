import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
from datasets import Dataset
import streamlit as st
from datetime import datetime

# Combined Universe (All will attempt Stooq first)
TICKERS = ["SPY", "QQQ", "IWM", "TLT", "IEF", "SHY", "GLD"]

def load_data(tickers=TICKERS):
    """Fetches data from Stooq with yfinance fallback."""
    all_series = {}

    for ticker in tickers:
        success = False
        # 1. Primary: Stooq
        try:
            # Stooq format: TICKER.US (e.g., TLT.US)
            stooq_symbol = f"{ticker}.US"
            df_stooq = web.DataReader(stooq_symbol, 'stooq')
            
            if not df_stooq.empty:
                # Stooq returns newest data first; sort to ascending for backtests
                all_series[ticker] = df_stooq['Close'].sort_index()
                st.toast(f"✅ {ticker} loaded from Stooq")
                success = True
        except Exception as e:
            print(f"Stooq failed for {ticker}: {e}")

        # 2. Fallback: yfinance
        if not success:
            try:
                yf_df = yf.download(ticker, period="max", progress=False)
                if not yf_df.empty:
                    # Use Adj Close to account for dividends/splits
                    all_series[ticker] = yf_df['Adj Close']
                    st.toast(f"⚠️ {ticker} loaded from yfinance (Fallback)")
                    success = True
            except Exception as e:
                st.error(f"❌ Critical: Could not load {ticker} from any source.")

    if all_series:
        # Align all tickers on the same dates and drop missing values
        return pd.concat(all_series, axis=1).dropna()
    return pd.DataFrame()

def push_to_hf(df, repo_id, token):
    """Pushes the current dataframe to Hugging Face Hub."""
    # Ensure Date is a column, not an index, for HF compatibility
    hf_export = df.reset_index()
    hf_export.columns = [str(col) for col in hf_export.columns] # Ensure string columns
    
    dataset = Dataset.from_pandas(hf_export)
    dataset.push_to_hub(repo_id, token=token)
    return True
