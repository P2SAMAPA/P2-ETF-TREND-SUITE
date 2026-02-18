import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Strategy Suite")

if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

with st.sidebar:
    st.header("🗂️ Data Controls")
    if st.session_state.master_data is None:
        if st.button("🚀 Seed Database (FRED/Stooq)"):
            st.session_state.master_data = seed_dataset_from_scratch()
            st.rerun()
    else:
        st.success(f"DB Last Updated: {st.session_state.master_data.index.max().date()}")
        if st.button("🔄 Sync Daily Data"):
            st.session_state.master_data = sync_incremental_data(st.session_state.master_data)
            st.rerun()
    
    st.divider()
    option = st.radio("Asset Universe", ("Option A - FI Trend", "Option B - Equity Trend"))
    start_yr = st.slider("Out-of-Sample Start", 2008, 2026, 2018)
    vol_target = st.slider("Volatility Target (%)", 5, 20, 12) / 100
    run_btn = st.button("🚀 Run Analysis", use_container_width=True, type="primary")

if st.session_state.master_data is not None:
    if run_btn:
        is_fi = "Option A" in option
        univ = FI_TICKERS if is_fi else X_EQUITY_TICKERS
        bench = "AGG" if is_fi else "SPY"
        
        results = run_trend_module(st.session_state.master_data[univ], 
                                 st.session_state.master_data[bench], 
                                 st.session_state.master_data['SOFR_ANNUAL'], 
                                 vol_target, start_yr)
        
        st.title(f"📈 {option} Performance Report")
        
        # Row 1: Key Metrics (Reordered)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Annual Return", f"{results['ann_ret']:.1%}")
        m2.metric("Sharpe Ratio", f"{results['sharpe']:.2f}")
        m3.metric("Max Drawdown", f"{results['max_dd_peak']:.1%}")
        m4.metric("Current SOFR (Live)", f"{results['current_sofr']:.2%}")

        # Row 2: Interactive Plotly Chart (Visible Years)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=results['equity_curve'].index, y=results['equity_curve'], name='Strategy'))
        fig.add_trace(go.Scatter(x=results['bench_curve'].index, y=results['bench_curve'], name=f'Benchmark ({bench})'))
        fig.update_layout(title="Growth of $1.00 (OOS)", template="plotly_dark", xaxis_title="Timeline")
        st.plotly_chart(fig, use_container_width=True)

        # Row 3: Methodology & Allocations
        st.divider()
        col_left, col_right = st.columns([1, 1.5])
        
        with col_left:
            st.subheader(f"🎯 Target Allocation: {results['next_day']}")
            weights_df = results['current_weights'][results['current_weights'] > 0.001].to_dict()
            weights_df['CASH (SOFR)'] = results['cash_weight']
            
            # Clean Table View
            final_df = pd.DataFrame.from_dict(weights_df, orient='index', columns=['Weight'])
            final_df['Weight'] = final_df['Weight'].apply(lambda x: f"{x:.2%}")
            st.table(final_df)

        with col_right:
            st.subheader("📚 Strategy Methodology")
            st.markdown(f"""
            This engine implements the **'Century of Profitable Trends'** framework (2025 Dow Award):
            
            1. **Regime Identification**: A dual 50/200-day Simple Moving Average (SMA) filter determines eligibility. Only assets in an uptrend are held.
            2. **Inverse-Volatility Sizing**: Unlike equal weighting, each asset is sized based on its 60-day realized volatility. Lower volatility assets receive higher capital allocations.
            3. **Portfolio Risk Targeting**: The system calculates a total portfolio weight to meet your **{vol_target:.0%} Volatility Target**.
            4. **Cash Scaling (SOFR)**: If the combined risk of the trending assets exceeds the target, or if assets fall out of trend, capital is diverted to **CASH**, earning the live SOFR rate. 
            5. **Leverage Management**: Gross exposure is dynamically managed and capped at 1.5x to prevent excessive drawdown during regime shifts.
            """)

            
    else:
        st.info("💡 Adjust your risk parameters and click 'Run Analysis' to see the predicted allocations.")
