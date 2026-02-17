import streamlit as st

# =====================================================
# PAGE CONFIG (ONLY LIGHT CODE HERE)
# =====================================================

st.set_page_config(
    page_title="P2 ETF Trend Suite",
    layout="wide",
)

st.title("📊 P2 ETF Trend Suite")
st.markdown("Institutional ETF Trend + Volatility Targeting Engine")

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Strategy Controls")

initial_capital = st.sidebar.number_input(
    "Initial Capital",
    value=100000,
    step=10000,
)

vol_target = st.sidebar.slider(
    "Target Annual Volatility",
    0.05, 0.30, 0.15
)

lookback = st.sidebar.slider(
    "Momentum Lookback (days)",
    50, 300, 200
)

run_button = st.sidebar.button("▶ Run Backtest")

st.sidebar.markdown("---")
st.sidebar.info("Backtest runs only when button is pressed.")

# =====================================================
# EXECUTION BLOCK
# =====================================================

if run_button:

    with st.spinner("Loading engine..."):

        # Lazy imports happen HERE
        from engine.backtest import run_backtest
        from data.loader import load_data
        from analytics.metrics import compute_metrics

    with st.spinner("Loading market data..."):
        df = load_data()

    with st.spinner("Running strategy..."):
        results = run_backtest(
            df=df,
            initial_capital=initial_capital,
            vol_target=vol_target,
            lookback=lookback,
        )

    metrics = compute_metrics(results["returns"])

    st.success("Backtest Complete")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CAGR", f"{metrics['cagr']:.2%}")
    col2.metric("Sharpe", f"{metrics['sharpe']:.2f}")
    col3.metric("Max Drawdown", f"{metrics['max_dd']:.2%}")
    col4.metric("Volatility", f"{metrics['vol']:.2%}")

    st.subheader("Equity Curve")
    st.line_chart(results["equity_curve"])

else:
    st.info("Configure parameters and click Run Backtest.")
