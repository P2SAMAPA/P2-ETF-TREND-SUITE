import streamlit as st
import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime
from data.loader import load_from_hf, seed_dataset, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Trend Suite")

# Sidebar Logic
st.sidebar.title("Configuration")
option = st.sidebar.radio("Select Strategy", ("Option A - FI Trend Follower", "Option B - Equity Trend Follower"))
start_year = st.sidebar.slider("Start Year", 2008, 2026, 2015)
vol_target = st.sidebar.slider("Annual Vol Target", 0.05, 0.25, 0.12)

# Data Initialization
if 'data' not in st.session_state:
    st.session_state.data = load_from_hf()

if st.session_state.data is None:
    if st.button("🚀 First Time Setup: Seed 2008-2026 Data"):
        st.session_state.data = seed_dataset()
        st.rerun()
else:
    # RUN STRATEGY
    universe = FI_TICKERS if "Option A" in option else X_EQUITY_TICKERS
    bench = "AGG" if "Option A" in option else "SPY"
    
    # Filter by Year
    d = st.session_state.data[st.session_state.data.index.year >= start_year]
    results = run_trend_module(d[universe], d['SOFR_ANNUAL'], vol_target)
    
    # UI OUTPUTS (Sharpe, Max DD, etc.)
    st.title(f"📈 {option} Performance")
    # ... (Insert Metric & Chart code here)
