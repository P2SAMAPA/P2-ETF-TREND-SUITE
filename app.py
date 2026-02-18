import streamlit as st
import pandas as pd
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data

st.set_page_config(layout="wide", page_title="P2 Trend Suite")

# --- SIDEBAR: DATA MANAGEMENT ---
st.sidebar.title("🗂️ Data Management")

# Initialize Session State
if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

# LOGIC: If no data, show SEED. If data exists, show SYNC.
if st.session_state.master_data is None:
    st.sidebar.warning("Database not found.")
    if st.sidebar.button("🚀 Step 1: Seed Database (2008-2026)"):
        with st.spinner("Downloading full history..."):
            st.session_state.master_data = seed_dataset_from_scratch()
            st.sidebar.success("Database Seeded!")
            st.rerun()
else:
    st.sidebar.success(f"Database Active: {st.session_state.master_data.index.max()}")
    
    # SYNC BUTTON for daily incremental updates
    if st.sidebar.button("🔄 Step 2: Sync Daily Data"):
        with st.spinner("Pinging Stooq/FRED for new data..."):
            st.session_state.master_data = sync_incremental_data(st.session_state.master_data)
            st.sidebar.success("Incremental Sync Complete!")
            st.rerun()

# --- SIDEBAR: STRATEGY CONTROLS ---
st.sidebar.divider()
st.sidebar.title("⚙️ Strategy Settings")
option = st.sidebar.radio("Select Module", ("Option A - FI Trend", "Option B - Equity Trend"))
start_year = st.sidebar.slider("Start Year", 2008, 2026, 2015)
vol_target = st.sidebar.slider("Annual Vol Target", 0.05, 0.25, 0.126)

# --- MAIN UI: ANALYSIS ---
if st.session_state.master_data is not None:
    # Your strategy execution code here...
    st.title(f"📊 {option}")
    # ...
else:
    st.info("Please use the sidebar to Seed the database first.")
