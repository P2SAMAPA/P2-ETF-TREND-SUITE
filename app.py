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

# 1. Option Selection
option = st.sidebar.radio("Select Strategy Module", 
                         ("Option A - FI Trend Follower", "Option B - Equity Trend Follower"))

# 2. Year Slider
start_year = st.sidebar.slider("Start Year (OOS Period)", 2008, 2025, 2015)

# 3. Vol Target & Sync
vol_target = st.sidebar.slider("Annual Vol Target", 0.05, 0.25, 0.126)
if st.sidebar.button("🔄 Sync Market Data"):
    refresh_market_data()
    st.sidebar.success("Data Synced!")

# --- CALENDAR LOGIC ---
nyse = mcal.get_calendar('NYSE')
today = datetime.now().strftime('%Y-%m-%d')
schedule = nyse.schedule(start_date=today, end_date='2026-12-31')
next_trading_day = schedule.index[0].strftime('%A, %b %d, %Y')

# --- EXECUTION ---
if st.button("▶ Run Analysis"):
    data = pd.read_csv("market_data.csv", index_col=0, parse_dates=True)
    
    # Filter by Start Year
    data = data[data.index.year >= start_year]
    
    # Select Universe & Benchmark
    if "Option B" in option:
        universe = X_EQUITY_TICKERS
        benchmark_ticker = "SPY"
        module_name = "Equity"
    else:
        universe = FI_TICKERS
        benchmark_ticker = "AGG"
        module_name = "Fixed Income"

    # Run Engine
    results = run_trend_module(data[universe], data['SOFR_ANNUAL'], vol_target)
    
    # Metrics Calculation
    returns = results['returns']
    cum_returns = results['curve']
    bench_returns = data[benchmark_ticker].pct_change().fillna(0)
    bench_curve = (1 + bench_returns).cumprod()
    
    # Stats
    ann_return = (cum_returns.iloc[-1]**(252/len(returns)) - 1)
    sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
    
    rolling_max = cum_returns.cummax()
    drawdown = (cum_returns - rolling_max) / rolling_max
    max_dd_peak = drawdown.min()
    
    # --- OUTPUT UI ---
    st.header(f"📊 {option} Results")
    
    # Target Allocation Section
    st.subheader(f"📅 Next Day Target Allocation: {next_trading_day}")
    alloc_df = results['alloc']
    st.table(alloc_df[alloc_df['Weight (%)'] > 0].sort_values("Weight (%)", ascending=False))

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Annualized Return", f"{ann_return:.2%}")
    m2.metric("Sharpe Ratio", f"{sharpe:.2f}")
    m3.metric("Max DD (Peak-to-Trough)", f"{max_dd_peak:.2%}")
    m4.metric("Last Daily Return", f"{returns.iloc[-1]:.2%}")

    # Chart
    st.subheader(f"Cumulative Return vs {benchmark_ticker}")
    chart_data = pd.DataFrame({
        "Strategy": cum_returns,
        f"Benchmark ({benchmark_ticker})": bench_curve
    })
    st.line_chart(chart_data)
