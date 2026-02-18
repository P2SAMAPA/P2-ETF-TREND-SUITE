import streamlit as st
import pandas as pd
import numpy as np
import pandas_market_calendars as mcal
from datetime import datetime
from data.loader import refresh_market_data, X_EQUITY_TICKERS, FI_TICKERS
from engine.trend_engine import run_trend_module

st.set_page_config(layout="wide", page_title="P2 Trend Suite")

# --- SIDEBAR UI ---
st.sidebar.title("Strategy Controls")

# 1. Module Toggle
option = st.sidebar.radio("Select Module", 
                         ("Option A - FI Trend Follower", "Option B - Equity Trend Follower"))

# 2. Year Slider
start_year = st.sidebar.slider("Start Year", 2008, 2026, 2015)

# 3. Parameters
vol_target = st.sidebar.slider("Annual Vol Target", 0.05, 0.25, 0.126)

if st.sidebar.button("🔄 Sync Market Data"):
    with st.spinner("Fetching Data..."):
        refresh_market_data()
    st.sidebar.success("Data Synced!")

# --- DATA PROCESSING ---
try:
    data = pd.read_csv("market_data.csv", index_col=0, parse_dates=True)
    
    # Filter by Year
    data = data[data.index.year >= start_year]

    # Assign Universe & Benchmark
    if "Option B" in option:
        universe = X_EQUITY_TICKERS
        benchmark_ticker = "SPY"
    else:
        universe = FI_TICKERS
        benchmark_ticker = "AGG"

    # Run Analysis
    results = run_trend_module(data[universe], data['SOFR_ANNUAL'], vol_target)
    
    # --- CALCULATE METRICS ---
    curve = results['curve']
    rets = results['returns']
    
    # Sharpe (Excess over 0)
    sharpe = (rets.mean() * 252) / (rets.std() * np.sqrt(252))
    
    # Annualized Return
    total_days = (curve.index[-1] - curve.index[0]).days
    ann_return = (curve.iloc[-1]**(365/total_days) - 1)
    
    # Drawdowns
    rolling_max = curve.cummax()
    drawdown = (curve - rolling_max) / rolling_max
    max_dd_peak = drawdown.min()
    max_dd_daily = rets.min()

    # NYSE Calendar for Next Day
    nyse = mcal.get_calendar('NYSE')
    schedule = nyse.schedule(start_date=datetime.now(), end_date='2026-12-31')
    next_day = schedule.index[0].strftime('%Y-%m-%d')

    # --- OUTPUT UI ---
    st.title(f"📊 {option}")
    
    # Stats Row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sharpe Ratio", f"{sharpe:.2f}")
    c2.metric("Annual Return", f"{ann_return:.2%}")
    c3.metric("Max DD (P-to-T)", f"{max_dd_peak:.2%}")
    c4.metric("Max DD (Daily)", f"{max_dd_daily:.2%}")
    c5.metric("Next Trade Date", next_day)

    # Allocation Table
    st.subheader(f"📍 Target Allocation for {next_day}")
    alloc = results['alloc']
    st.dataframe(alloc[alloc['Weight (%)'] > 0].sort_values("Weight (%)", ascending=False), use_container_width=True)

    # Performance Chart
    st.subheader(f"Cumulative Return vs {benchmark_ticker}")
    bench_curve = (1 + data[benchmark_ticker].pct_change().fillna(0)).cumprod()
    # Normalize benchmark to start at 1.0 at start_year
    bench_curve = bench_curve / bench_curve.iloc[0]
    
    chart_df = pd.DataFrame({
        "Strategy": curve,
        f"Benchmark ({benchmark_ticker})": bench_curve
    })
    st.line_chart(chart_df)

except Exception as e:
    st.info("Please Click 'Sync Market Data' in the sidebar to initialize the engine.")
    st.error(f"Waiting for data... (Technical details: {e})")
