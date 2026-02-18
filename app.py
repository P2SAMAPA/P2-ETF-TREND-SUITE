import streamlit as st

st.set_page_config(page_title="P2 ETF Trend Suite", layout="wide")

st.title("📊 P2 ETF Trend Suite")
st.markdown("Stooq-Primary Data Engine + HF Integration")

# Sidebar Controls
st.sidebar.header("Parameters")
initial_capital = st.sidebar.number_input("Initial Capital", value=100000)
vol_target = st.sidebar.slider("Target Volatility", 0.05, 0.30, 0.15)
lookback = st.sidebar.slider("Lookback (Days)", 50, 300, 200)

st.sidebar.markdown("---")
st.sidebar.header("Hugging Face Sync")
hf_repo = st.sidebar.text_input("Repo ID", placeholder="user/dataset-name")
hf_token = st.sidebar.text_input("HF Token", type="password")

run_button = st.sidebar.button("▶ Run Full Process")

if run_button:
    from data.loader import load_data, push_to_hf
    from engine.backtest import run_backtest
    from analytics.metrics import compute_metrics

    # Phase 1: Data Fetching
    with st.spinner("Fetching data from Stooq..."):
        df = load_data()
    
    if not df.empty:
        st.subheader("📈 Market Data Preview")
        st.dataframe(df.tail(5), use_container_width=True)

        # Phase 2: Backtesting
        with st.spinner("Calculating Trend Strategy..."):
            results = run_backtest(df, initial_capital, vol_target, lookback)
            metrics = compute_metrics(results["returns"])

        # Display Results
        st.success("Analysis Complete")
        c1, c2, c3 = st.columns(3)
        c1.metric("CAGR", f"{metrics['cagr']:.2%}")
        c2.metric("Sharpe", f"{metrics['sharpe']:.2f}")
        c3.metric("Max Drawdown", f"{metrics['max_dd']:.2%}")

        st.line_chart(results["equity_curve"])

        # Phase 3: HF Sync
        if hf_repo and hf_token:
            with st.spinner("Syncing to Hugging Face..."):
                push_to_hf(df, hf_repo, hf_token)
            st.sidebar.success("✅ Dataset Synced!")
    else:
        st.error("Data fetch failed. Verify ticker symbols.")
