import streamlit as st
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Strategy Suite")

# --- INITIALIZATION ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

# --- SIDEBAR: DATA CONTROLS ---
with st.sidebar:
    st.header("🗂️ Data Management")
    if st.session_state.master_data is None:
        st.error("No dataset detected.")
        if st.button("🚀 Seed Database (2008-2026)", use_container_width=True):
            st.session_state.master_data = seed_dataset_from_scratch()
            st.rerun()
    else:
        last_dt = st.session_state.master_data.index.max()
        st.success(f"Database Active: {last_dt.date()}")
        if st.button("🔄 Sync New Data", use_container_width=True):
            st.session_state.master_data = sync_incremental_data(st.session_state.master_data)
            st.rerun()
    
    st.divider()
    st.header("⚙️ Strategy Settings")
    option = st.radio("Universe Selection", ("Option A - FI Trend", "Option B - Equity Trend"))
    start_yr = st.slider("Backtest Start Year", 2008, 2026, 2015)
    vol_target = st.slider("Target Vol (%)", 5, 20, 12) / 100
    
    st.divider()
    run_btn = st.button("🚀 Run Strategy Analysis", use_container_width=True, type="primary")

# --- MAIN PAGE: DISPLAY ---
if st.session_state.master_data is not None:
    if run_btn:
        with st.spinner("Crunching data..."):
            # Universe Selection
            univ = FI_TICKERS if "Option A" in option else X_EQUITY_TICKERS
            # Slice by date
            df = st.session_state.master_data[st.session_state.master_data.index.year >= start_yr]
            
            # Execute Engine
            results = run_trend_module(df[univ], df['SOFR_ANNUAL'], vol_target)
            
            # Show Metrics
            st.title(f"📊 {option} Performance Report")
            m1, m2, m3 = st.columns(3)
            m1.metric("Sharpe Ratio", f"{results['sharpe']:.2f}")
            m2.metric("Annual Return", f"{results['ann_ret']:.1%}")
            m3.metric("Max Drawdown", f"{results['max_dd']:.1%}")
            
            # Equity Curve
            st.subheader("Cumulative Growth (vs Cash)")
            st.line_chart(results['equity_curve'])
            
            # Allocation Check
            st.divider()
            st.subheader("Current Market Status")
            active_assets = results['current_signals'][results['current_signals'] > 0].index.tolist()
            st.write(f"**In-Trend Assets:** {', '.join(active_assets) if active_assets else 'All Cash'}")
            
    else:
        st.title("Welcome to the 2025 Trend Suite")
        st.info("👈 Use the sidebar to manage your data and click 'Run Strategy Analysis' to begin.")
else:
    st.warning("Please initialize the database using the 'Seed' button in the sidebar.")
