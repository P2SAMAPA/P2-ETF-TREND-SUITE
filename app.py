import streamlit as st

st.set_page_config(layout="wide")

st.title("P2 ETF Trend Suite - Debug Mode")

try:
    from data.hf_store import load_dataset
    st.success("hf_store imported successfully")
except Exception as e:
    st.error(f"hf_store failed: {e}")

try:
    from data.updater import update_market_data
    st.success("updater imported successfully")
except Exception as e:
    st.error(f"updater failed: {e}")

try:
    from data.fred import get_sofr_series
    st.success("fred imported successfully")
except Exception as e:
    st.error(f"fred failed: {e}")

try:
    from engine.backtest import run_backtest
    st.success("backtest imported successfully")
except Exception as e:
    st.error(f"backtest failed: {e}")

try:
    from analytics.metrics import compute_metrics
    st.success("metrics imported successfully")
except Exception as e:
    st.error(f"metrics failed: {e}")
