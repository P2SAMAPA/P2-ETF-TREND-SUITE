import streamlit as st
import pandas as pd
from data.loader import load_from_hf, seed_dataset_from_scratch, sync_incremental_data
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Trend Suite")

# ... (Previous Initialization and Sidebar code here) ...

if st.session_state.master_data is not None:
    if run_btn:
        with st.spinner("Analyzing Market Regimes..."):
            # Setup Universe and Benchmark
            is_fi = "Option A" in option
            univ = FI_TICKERS if is_fi else X_EQUITY_TICKERS
            bench_ticker = "AGG" if is_fi else "SPY"
            
            # Filter Data
            df = st.session_state.master_data[st.session_state.master_data.index.year >= start_yr]
            
            # Run Engine
            results = run_trend_module(df[univ], df[bench_ticker], df['SOFR_ANNUAL'], vol_target)
            
            # --- OUTPUT UI ---
            st.title(f"📈 {option} vs {bench_ticker} ({start_yr}-Present)")
            
            # Row 1: Key Performance Indicators
            m1, m2, m3, m4 = st.columns(4)
            ann_ret = results['strat_ret_series'].mean() * 252
            vol = results['strat_ret_series'].std() * np.sqrt(252)
            sharpe = (ann_ret - 0.03) / vol if vol > 0 else 0
            
            m1.metric("Sharpe Ratio", f"{sharpe:.2f}")
            m2.metric("Annual Return", f"{ann_ret:.1%}")
            m3.metric("Peak-to-Trough DD", f"{results['max_dd_peak']:.1%}", delta_color="inverse")
            m4.metric("Daily DD (Avg)", f"{results['dd_series'].mean():.2%}")

            # Row 2: Charts
            chart_data = pd.DataFrame({
                'Strategy': results['equity_curve'],
                f'Benchmark ({bench_ticker})': results['bench_curve']
            })
            st.subheader("Relative Growth of $1.00")
            st.line_chart(chart_data)

            # Row 3: Actionable Allocation (Next Trading Day)
            st.divider()
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📅 Next Trading Session")
                st.info(f"**NYSE Market Open:** {results['next_trading_day']}")
                st.write("**Required Action:** Rebalance at market open based on signals.")
            
            with c2:
                st.subheader("🎯 Target Allocations")
                if results['active_assets']:
                    st.success(f"**In-Trend Assets:** {', '.join(results['active_assets'])}")
                else:
                    st.warning("⚠️ **Strategy Signal: 100% CASH** (No active trends detected)")

            # Row 4: Methodology Footer
            st.divider()
            with st.expander("📚 Methodology & 2025 Dow Award Paper Reference"):
                st.markdown("""
                ### A Century of Profitable Trends (Dow Award 2025)
                This model implements the core findings of the **2025 Charles H. Dow Award** winning paper:
                * **Dual-Trend Filter:** Uses a crossover logic (50/200 SMA proxy for Donchian/Keltner) to identify regime shifts.
                * **Volatility Targeting:** Position sizes are inversely proportional to realized 60-day volatility to maintain a stable risk profile.
                * **Cash Management:** Uninvested capital is theoretically swept into SOFR-based cash instruments.
                * **Maximum Leverage:** Strategy is capped at 1.5x (150%) gross exposure to avoid blow-up risk.
                """)

    else:
        st.info("👈 Set your parameters and click **'Run Strategy Analysis'** in the sidebar.")
