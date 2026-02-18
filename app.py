import streamlit as st
import pandas as pd
import numpy as np
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Strategy Suite | 2025 Dow Award Edition")

# --- SAFE SESSION INITIALIZATION ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("🗂️ Data Management")
    if st.session_state.master_data is None:
        st.error("Dataset not found.")
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
    option = st.radio("Strategy Selection", ("Option A - FI Trend", "Option B - Equity Trend"))
    start_yr = st.slider("OOS Start Year", 2008, 2026, 2018)
    vol_target = st.slider("Ann. Vol Target (%)", 5, 25, 12) / 100
    run_btn = st.button("🚀 Run Analysis", use_container_width=True, type="primary")

# --- MAIN OUTPUT UI ---
if st.session_state.master_data is not None:
    if run_btn:
        with st.spinner("Analyzing Market Regimes..."):
            # 1. Setup Universe and Benchmark
            is_fi = "Option A" in option
            univ = FI_TICKERS if is_fi else X_EQUITY_TICKERS
            bench_ticker = "AGG" if is_fi else "SPY"
            
            # 2. Filter Data (Using Start Year as OOS boundary)
            # The engine uses data prior to start_yr for signal lookback (Training/Buffer)
            df = st.session_state.master_data
            
            # 3. Execute Engine
            results = run_trend_module(df[univ], df[bench_ticker], df['SOFR_ANNUAL'], vol_target, start_yr)
            
            # 4. KPI Header
            st.title(f"📈 {option} Performance vs {bench_ticker}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("OOS Sharpe", f"{results['sharpe']:.2f}")
            m2.metric("Ann. Return", f"{results['ann_ret']:.1%}")
            m3.metric("Peak-to-Trough DD", f"{results['max_dd_peak']:.1%}")
            m4.metric("Avg Daily DD", f"{results['avg_daily_dd']:.2%}")

            # 5. Equity Curve Chart
            chart_df = pd.DataFrame({
                "Strategy Portfolio": results['equity_curve'],
                f"Benchmark ({bench_ticker})": results['bench_curve']
            })
            st.subheader("Cumulative Growth of $1.00 (Out-of-Sample)")
            st.line_chart(chart_df)

            # 6. Actionable Allocation (Next Trading Day)
            st.divider()
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📅 Next Trading Session")
                st.info(f"**NYSE Market Date:** {results['next_day']}\n\n**Action:** Execute at Open")
            with c2:
                st.subheader("🎯 Required Allocation")
                active = results['current_signals'][results['current_signals'] > 0].index.tolist()
                if active:
                    st.success(f"**Long Positions:** {', '.join(active)}")
                else:
                    st.warning("⚖️ **Position:** 100% CASH (Market Neutral)")

            # 7. Methodology Footer
            st.divider()
            with st.expander("📚 Methodology & 2025 Dow Award Reference"):
                st.markdown("""
                ### A Century of Profitable Trends (Zarattini & Antonacci, 2025)
                This model implements the framework from the 2025 Charles H. Dow Award winning paper:
                * **Regime Filter:** Dual SMA logic (50/200 crossover) proxying for Keltner/Donchian channels.
                * **Volatility Targeting:** Positions sized by $Weight = \sigma_{target} / \sigma_{realized}$, capped at 1.5x.
                * **Benchmarking:** Equity trends are compared to SPY; Fixed Income to AGG.
                * **OOS Testing:** The analysis shown above represents the **Out-of-Sample** period. Data prior to the start year is used solely for initial indicator 'burn-in'.
                """)
    else:
        st.info("💡 Adjust your parameters in the sidebar and click **'Run Analysis'**.")
else:
    st.warning("👈 Please click 'Seed Database' to initialize historical data.")
