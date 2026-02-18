import streamlit as st
import pandas as pd
from data.loader import refresh_market_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 ETF Trend Suite")

st.sidebar.title("Settings")
vol_target = st.sidebar.slider("Annual Vol Target", 0.05, 0.25, 0.126)

if st.sidebar.button("🔄 Refresh Market Data"):
    refresh_market_data()
    st.sidebar.success("Data Updated from Stooq/SOFR!")

if st.button("▶ Run All Modules"):
    data = pd.read_csv("market_data.csv", index_col=0, parse_dates=True)
    
    # Run Modules
    eq_res = run_trend_module(data[X_EQUITY_TICKERS], data['SOFR_ANNUAL'], vol_target)
    fi_res = run_trend_module(data[FI_TICKERS], data['SOFR_ANNUAL'], vol_target)
    
    # Performance Comparison
    spy_curve = (1 + data['SPY'].pct_change()).cumprod()
    comparison = pd.DataFrame({
        "X-ETF Strategy": eq_res['curve'],
        "SPY Benchmark": spy_curve
    }).dropna()

    st.header("📈 Performance: Equity Strategy vs. SPY")
    st.line_chart(comparison)
    
    # Target Allocations
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🛡️ Equity Allocation (Next Day)")
        st.dataframe(eq_res['alloc'][eq_res['alloc']['Weight (%)'] > 0])
    with col2:
        st.subheader("🏦 FI Comparison Allocation")
        st.dataframe(fi_res['alloc'][fi_res['alloc']['Weight (%)'] > 0])
