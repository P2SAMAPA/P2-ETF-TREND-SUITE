import streamlit as st
import os

from data.hf_store import load_dataset
from data.updater import update_market_data
from data.fred import get_sofr_series
from engine.backtest import run_backtest
from analytics.metrics import compute_metrics

st.set_page_config(layout="wide")

st.title("📊 P2 ETF Trend Suite")
st.markdown("Institutional ETF Trend + Volatility Targeting Engine")

# ========================
# Sidebar Controls
# ========================

st.sidebar.header("Controls")

initial_capital = st.sidebar.number_input("Initial Capital", value=100000, step=10000)
vol_target = st.sidebar.slider("Target Annual Volatility", 0.05, 0.30, 0.15)
lookback = st.sidebar.slider("Momentum Lookback (days)", 50, 300, 200)

refresh = st.sidebar.button("🔄 Refresh Market Data")

# ========================
# Data Load
# ========================

with st.spinner("Loading ETF dataset..."):
    df = load_dataset()

if refresh:
    with st.spinner("Updating market data from yfinance..."):
        df = update_market_data(df)
    st.success("Dataset updated successfully.")

# ========================
# Backtest
# ========================

with st.spinner("Pulling SOFR from FRED..."):
    sofr = get_sofr_series()

with st.spinner("Running backtest..."):
    results = run_backtest(
        df=df,
        initial_capital=initial_capital,
        vol_target=vol_target,
        lookback=lookback,
    )

metrics = compute_metrics(results["returns"], sofr)

# ========================
# Layout
# ========================

col1, col2, col3, col4 = st.columns(4)

col1.metric("CAGR", f"{metrics['cagr']:.2%}")
col2.metric("Sharpe (SOFR)", f"{metrics['sharpe']:.2f}")
col3.metric("Max Drawdown", f"{metrics['max_dd']:.2%}")
col4.metric("Volatility", f"{metrics['vol']:.2%}")

st.line_chart(results["equity_curve"])

st.subheader("Current Allocation")
st.dataframe(results["latest_allocation"])
