import streamlit as st
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data

st.set_page_config(layout="wide", page_title="P2 Strategy Suite")

# 1. Initialize Session State Data
if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

# 2. Sidebar Layout
with st.sidebar:
    st.title("🗂️ Data Management")
    
    if st.session_state.master_data is None:
        st.error("No dataset detected in repository.")
        if st.button("🚀 Seed Database (2008-Present)", use_container_width=True):
            st.session_state.master_data = seed_dataset_from_scratch()
            st.rerun()
    else:
        last_dt = st.session_state.master_data.index.max()
        st.success(f"Database Active\nLast Date: {last_dt.date()}")
        
        if st.button("🔄 Sync Daily Data", use_container_width=True):
            with st.spinner("Updating records..."):
                st.session_state.master_data = sync_incremental_data(st.session_state.master_data)
                st.rerun()
    
    st.divider()
    st.title("⚙️ Strategy Settings")
    option = st.sidebar.radio("Strategy Type", ("Option A - FI Trend", "Option B - Equity Trend"))
    start_yr = st.sidebar.slider("Start Year", 2008, 2026, 2015)
    vol_target = st.sidebar.slider("Vol Target (%)", 5, 25, 12) / 100

# 3. Main Page
if st.session_state.master_data is not None:
    st.title(f"📊 {option} Performance")
    # filtered_data = st.session_state.master_data[st.session_state.master_data.index.year >= start_yr]
    # engine_results = run_strategy(filtered_data, vol_target)
    st.info("Strategy Engine ready. Select parameters in the sidebar to begin analysis.")
else:
    st.warning("👈 Please click the 'Seed' button in the sidebar to initialize the historical data.")
