import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Strategy Suite")

# Initialize Session State safely
if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

with st.sidebar:
    st.header("🗂️ Configuration")
    
    if st.session_state.master_data is None:
        if st.button("🚀 Seed Database"):
            st.session_state.master_data = seed_dataset_from_scratch()
            st.rerun()
    else:
        st.success(f"DB Last Entry: {st.session_state.master_data.index.max().date()}")
        
        # Sync Button with Persistent UI Feedback
        if st.button("🔄 Sync New Data"):
            updated_df, success = sync_incremental_data(st.session_state.master_data)
            st.session_state.master_data = updated_df
            
            # Store the result so it survives the rerun
            if success:
                st.session_state.sync_status = "✅ Data refreshed"
            else:
                st.session_state.sync_status = "❌ Data refresh failed"
            
            st.rerun()

        # Display the persisted status message if it exists in state
        if 'sync_status' in st.session_state:
            st.sidebar.write(st.session_state.sync_status)

    st.divider()
    
    # Strategy Inputs
    option = st.selectbox("Universe Selection", ("Option A - FI Trend", "Option B - Equity Trend"))
    sub_option = st.selectbox("Conviction Strategy", 
                             ("All Trending ETFs", "3 Highest Conviction", "1 Highest Conviction"))
    start_yr = st.slider("OOS Start Year", 2008, 2026, 2018)
    vol_target = st.slider("Risk Target (%)", 5, 20, 12) / 100
    
    run_btn = st.button("🚀 Run Analysis", use_container_width=True, type="primary")

if st.session_state.master_data is not None:
    if run_btn:
        # Determine Universe and Benchmark
        is_fi = "Option A" in option
        univ = FI_TICKERS if is_fi else X_EQUITY_TICKERS
        bench = "AGG" if is_fi else "SPY"
        
        # Run the Quantitative Engine
        results = run_trend_module(st.session_state.master_data[univ], 
                                 st.session_state.master_data[bench], 
                                 st.session_state.master_data['SOFR_ANNUAL'], 
                                 vol_target, start_yr, sub_option)
        
        st.title(f"📊 {option}: {sub_option}")
        
        # Row 1: Key Performance Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Annual Return", f"{results['ann_ret']:.1%}")
        m2.metric("Sharpe Ratio", f"{results['sharpe']:.2f}")
        m3.metric("Max Drawdown", f"{results['max_dd']:.1%}")
        m4.metric("Current SOFR", f"{results['current_sofr']:.2%}")

        # Row 2: Performance Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=results['equity_curve'].index, y=results['equity_curve'], name='Strategy'))
        fig.add_trace(go.Scatter(x=results['bench_curve'].index, y=results['bench_curve'], name=f'Benchmark ({bench})'))
        fig.update_layout(
            title="Out-of-Sample Cumulative Performance", 
            template="plotly_dark", 
            xaxis_title="Timeline",
            yaxis_title="Growth of $1.00",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Row 3: Methodology & Next-Day Allocations
        st.divider()
        col_left, col_right = st.columns([1, 1.5])
        
        with col_left:
            st.subheader(f"🎯 Target Allocation: {results['next_day']}")
            # Filter out zero weights for the display table
            weights = results['current_weights'][results['current_weights'] > 0.0001].to_dict()
            weights['CASH (SOFR)'] = results['cash_weight']
            
            df_weights = pd.DataFrame.from_dict(weights, orient='index', columns=['Weight'])
            st.table(df_weights.style.format("{:.2%}"))

        with col_right:
            st.subheader("📚 Methodology: Zarattini & Antonacci")
            st.markdown(f"""
            This strategy implements the **2025 Charles H. Dow Award** winning framework by **Andrea Zarattini** and **Michael Antonacci**.
            
            1. **Regime Identification**: A dual 50/200-day SMA filter determines asset eligibility. 
            2. **Conviction Ranking**: Assets are ranked by their distance from the 200-day SMA (Trend Strength).
            3. **Concentrated Sizing**: In **{sub_option}** mode, the risk budget is focused only on top leaders.
            4. **Volatility Targeting**: Allocations are sized inversely to 60-day volatility to maintain a stable **{vol_target:.0%}** risk profile.
            5. **Cash Buffer**: Remaining budget earns the live SOFR rate (Federal Reserve Bank of New York).
            """)
    else:
        st.info("💡 Adjust your risk parameters in the sidebar and click 'Run Analysis' to see predicted allocations.")
else:
    st.warning("⚠️ No data found. Please check your HF_TOKEN or click 'Seed Database'.")
