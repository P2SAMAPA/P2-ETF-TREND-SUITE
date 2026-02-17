import streamlit as st

# =====================================================
# PAGE CONFIG (must be first Streamlit command)
# =====================================================

st.set_page_config(
    page_title="P2 ETF Trend Suite",
    layout="wide",
)

st.title("📊 P2 ETF Trend Suite")
st.markdown("Institutional ETF Trend + Volatility Targeting Engine")

# =====================================================
# SIDEBAR CONTROLS
# =====================================================

st.sidebar.header("Strategy Controls")

initial_capital = st.sidebar.number_input(
    "Initial Capital",
    value=100000,
    step=10000,
)

vol_target = st.sidebar.slider(
    "Target Annual Volatility",
    min_value=0.05,
    max_value=0.30,
    value=0.15,
)

lookback = st.sidebar.slider(
    "Momentum Lookback (days)",
    min_value=50,
    max_value=300,
    value=200,
)

run_button = st.sidebar.button("▶ Run Backtest")

st.sidebar.markdown("---")
st.sidebar.info("Backtest runs only when button is pressed.")

# =====================================================
# MAIN EXECUTION (runs ONLY when button clicked)
# =====================================================

if run_button:

    # Import heavy modules only when needed
    from data.hf_store import load_dataset
    from data.updater import update_market_data
    from data.fred import get_sofr_series
    from engine.backtest import run_backtest
    from analytics.metrics import compute_metrics

    # ---------------------------
    # Load Dataset
    # ---------------------------
    with st.spinner("Loading ETF dataset from Hugging Face..."):
        df = load_dataset()

    # ---------------------------
    # Pull SOFR
    # ---------------------------
    with st.spinner("Pulling SOFR from FRED..."):
        sofr = get_sofr_series()

    # ---------------------------
    # Run Backtest
    # ---------------------------
    with st.spinner("Running backtest engine..."):
        results = run_backtest(
            df=df,
            initial_capital=initial_capital,
            vol_target=vol_target,
            lookback=lookback,
        )

    metrics = compute_metrics(results["returns"], sofr)

    st.success("Backtest Complete")

    # =====================================================
    # METRICS PANEL
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("CAGR", f"{metrics['cagr']:.2%}")
    col2.metric("Sharpe (SOFR)", f"{metrics['sharpe']:.2f}")
    col3.metric("Max Drawdown", f"{metrics['max_dd']:.2%}")
    col4.metric("Volatility", f"{metrics['vol']:.2%}")

    st.markdown("---")

    # =====================================================
    # EQUITY CURVE
    # =====================================================

    st.subheader("Equity Curve")
    st.line_chart(results["equity_curve"])

    st.markdown("---")

    # =====================================================
    # ALLOCATION TABLE
    # =====================================================

    st.subheader("Latest Portfolio Allocation")
    st.dataframe(results["latest_allocation"], use_container_width=True)

else:
    st.info("Configure parameters in the sidebar and click **Run Backtest**.")
