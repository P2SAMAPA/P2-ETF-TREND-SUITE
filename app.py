import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Strategy Suite")

# Initial Data Load
if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

with st.sidebar:
    st.header("🗂️ Configuration")
    
    if st.session_state.master_data is None:
        if st.button("🚀 Seed Database"):
            st.session_state.master_data = seed_dataset_from_scratch()
            st.rerun()
    else:
        # Show database status
        st.success(f"DB Last Entry: {st.session_state.master_data.index.max().date()}")
        
        # Sync Action
        if st.button("🔄 Sync New Data"):
            updated_df, status_code = sync_incremental_data(st.session_state.master_data)
            st.session_state.master_data = updated_df
            
            # Map logical codes to UI messages
            messages = {
                "success": "✅ Data refreshed",
                "already_current": "ℹ️ Already up-to-date",
                "no_new_data_yet": "⏳ Market not yet closed",
                "api_failure": "❌ Connection/API issue",
                "error": "❌ Critical Error"
            }
            # Save message to session state so it survives the rerun
            st.session_state.sync_status = messages.get(status_code, "❓ Unknown Status")
            st.rerun()

        # Persistent status display
        if 'sync_status' in st.session_state:
            st.sidebar.info(st.session_state.sync_status)

    st.divider()
    
    # Strategy Parameters
    option = st.selectbox("Universe Selection", ("Option A - FI Trend", "Option B - Equity Trend"))
    sub_option = st.selectbox("Conviction Strategy", 
                             ("All Trending ETFs", "3 Highest Conviction", "1 Highest Conviction"))
    start_yr = st.slider("OOS Start Year", 2008, 2026, 2018)
    vol_target = st.slider("Risk Target (%)", 5, 20, 12) / 100
    
    run_btn = st.button("🚀 Run Analysis", use_container_width=True, type="primary")

if st.session_state.master_data is not None:
    if run_btn:
        # Configuration mapping
        is_fi = "Option A" in option
        univ = FI_TICKERS if is_fi else X_EQUITY_TICKERS
        bench = "AGG" if is_fi else "SPY"
        
        # Compute Results
        results = run_trend_module(st.session_state.master_data[univ], 
                                 st.session_state.master_data[bench], 
                                 st.session_state.master_data['SOFR_ANNUAL'], 
                                 vol_target, start_yr, sub_option)
        
        st.title(f"📊 {option}: {sub_option}")
        
        # Display Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Annual Return", f"{results['ann_ret']:.1%}")
        m2.metric("Sharpe Ratio", f"{results['sharpe']:.2f}")
        m3.metric("Max Drawdown", f"{results['max_dd']:.1%}")
        m4.metric("Current SOFR", f"{results['current_sofr']:.2%}")

        # Performance Visualization
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=results['equity_curve'].index, y=results['equity_curve'], name='Strategy'))
        fig.add_trace(go.Scatter(x=results['bench_curve'].index, y=results['bench_curve'], name=f'Benchmark ({bench})'))
        fig.update_layout(title="Out-of-Sample Performance", template="plotly_dark", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        col_l, col_r = st.columns([1, 1.5])
        
        with col_l:
            st.subheader(f"🎯 Target Allocation: {results['next_day']}")
            weights = results['current_weights'][results['current_weights'] > 0.0001].to_dict()
            weights['CASH (SOFR)'] = results['cash_weight']
            st.table(pd.DataFrame.from_dict(weights, orient='index', columns=['Weight']).style.format("{:.2%}"))

        with col_r:
            st.subheader("📚 Methodology: Zarattini & Antonacci")
            st.markdown("Strategy uses 50/200 SMA filters, conviction ranking, and 60-day volatility targeting.")
    else:
        st.info("💡 Adjust your parameters and click 'Run Analysis'.")
else:
    st.warning("⚠️ Data source missing. Please Seed or check HF Token.")
