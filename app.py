import streamlit as st
import pandas as pd
import numpy as np
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Strategy Suite | 2025 Dow Edition")

# --- INITIALIZATION ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🗂️ Data Management")
    if st.session_state.master_data is None:
        st.warning("Database missing.")
        if st.button("🚀 Seed Database (2008-2026)", use_container_width=True):
            st.session_state.master_data = seed_dataset_from_scratch()
            st.rerun()
    else:
        last_dt = pd.to_datetime(st.session_state.master_data.index).max()
        st.success(f"Database Active: {last_dt.date()}")
        if st.button("🔄 Sync Daily Data", use_container_width=True):
            st.session_state.master_data = sync_incremental_data(st.session_state.master_data)
            st.rerun()
    
    st.divider()
    st.header("⚙️ Strategy Settings")
    option = st.radio("Selection", ("Option A - FI Trend", "Option B - Equity Trend"))
    start_yr = st.slider("OOS Start Year", 2008, 2026, 2018)
    vol_target = st.slider("Target Vol (%)", 5, 25, 12) / 100
    run_btn = st.button("🚀 Run Analysis", use_container_width=True, type="primary")

# --- MAIN UI ---
if st.session_state.master_data is not None:
    if run_btn:
        with st.spinner("Processing Strategy..."):
            is_fi = "Option A" in option
            univ = FI_TICKERS if is_fi else X_EQUITY_TICKERS
            bench = "AGG" if is_fi else "SPY"
            
            # Execute
            results = run_trend_module(st.session_state.master_data[univ], 
                                     st.session_state.master_data[bench], 
                                     st.session_state.master_data['SOFR_ANNUAL'], 
                                     vol_target, start_yr)
            
            st.title(f"📈 {option} Performance vs {bench}")
            
            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("OOS Sharpe", f"{results['sharpe']:.2f}")
            m2.metric("Ann. Return", f"{results['ann_ret']:.1%}")
            m3.metric("Max DD (Peak-Trough)", f"{results['max_dd_peak']:.1%}")
            m4.metric("Avg Daily DD", f"{results['avg_daily_dd']:.2%}")

            # Chart
            chart_df = pd.DataFrame({
                "Strategy": results['equity_curve'],
                f"Benchmark ({bench})": results['bench_curve']
            })
            st.subheader("OOS Growth Comparison")
            st.line_chart(chart_df)

            # Execution Info
            st.divider()
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📅 Next Session")
                st.info(f"**NYSE Date:** {results['next_day']}")
            with c2:
                st.subheader("🎯 Allocation")
                active = results['current_signals'][results['current_signals'] > 0].index.tolist()
                if active:
                    st.success(f"**Long:** {', '.join(active)}")
                else:
                    st.warning("⚖️ **100% Cash**")

            # Footer
            st.divider()
            with st.expander("📚 Methodology"):
                st.write("Implemented via 'A Century of Profitable Trends' (2025 Dow Award Paper).")
    else:
        st.info("💡 Adjust settings and click 'Run Analysis'.")
else:
    st.warning("Please Seed Database in the sidebar.")
