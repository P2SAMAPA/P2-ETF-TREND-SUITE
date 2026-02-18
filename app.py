import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Strategy Suite")

if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

with st.sidebar:
    st.header("🗂️ Configuration")
    option = st.selectbox("Universe Selection", ("Option A - FI Trend", "Option B - Equity Trend"))
    
    # NEW SUB-OPTIONS
    sub_option = st.selectbox("Conviction Level", 
                             ("All Trending ETFs", "3 Highest Conviction", "1 Highest Conviction"))
    
    start_yr = st.slider("OOS Start", 2008, 2026, 2018)
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
                                 vol_target, start_yr, sub_option)
        
        st.title(f"📊 {option} - {sub_option}")
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Annual Return", f"{results['ann_ret']:.1%}")
        m2.metric("Sharpe Ratio", f"{results['sharpe']:.2f}")
        m3.metric("Max Drawdown", f"{results['max_dd']:.1%}")
        m4.metric("Current SOFR", f"{results['current_sofr']:.2%}")

        # Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=results['equity_curve'].index, y=results['equity_curve'], name='Strategy'))
        fig.add_trace(go.Scatter(x=results['bench_curve'].index, y=results['bench_curve'], name=f'Benchmark ({bench})'))
        fig.update_layout(title="OOS Performance", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # Methodology & Target
        st.divider()
        col_left, col_right = st.columns([1, 1.5])
        
        with col_left:
            st.subheader(f"🎯 Target Allocation: {results['next_day']}")
            w = results['current_weights'][results['current_weights'] > 0.0001].to_dict()
            w['CASH (SOFR)'] = results['cash_weight']
            st.table(pd.DataFrame.from_dict(w, orient='index', columns=['Weight']).style.format("{:.2%}"))

        with col_right:
            st.subheader("📚 Methodology: Zarattini & Antonacci (2025)")
            st.markdown(f"""
            This strategy implements the **2025 Charles H. Dow Award** framework authored by **Andrea Zarattini** and **Michael Antonacci**.
            
            * **Trend Detection**: Uses a 50/200 SMA dual-filter.
            * **Conviction Scoring**: Assets are ranked based on their relative distance from the 200-day trend line.
            * **Concentration**: Under **{sub_option}**, the engine filters the universe to only the top-tier trending assets.
            * **Risk Sizing**: Allocation is inversely proportional to 60-day volatility. If the selected ETFs cannot safely fill the **{vol_target:.0%}** risk budget, the remainder is held in **CASH (SOFR)**.
            """)
            


### Why this is powerful:
* **The "3 Highest Conviction" sub-option** creates a "Best of the Best" portfolio. Instead of diluting your risk budget across 20 ETFs that are barely in trend, it puts the full 12% risk budget into the 3 strongest leaders.
* **The "1 Highest Conviction" sub-option** is the ultimate momentum play, concentrating all allowed risk into the single strongest trend.
* **Authorship**: Zarattini and Antonacci's names are now front-and-center in the methodology section.

**Would you like me to add a "Drawdown Overlay" chart so you can compare the risk spikes between the Concentrated (1-ETF) and Broad (All ETFs) sub-options?**
