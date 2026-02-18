import streamlit as st
from data.loader import load_from_hf, seed_dataset_from_scratch, X_EQUITY_TICKERS, FI_TICKERS
# ... other imports

st.sidebar.title("Data Management")

# Check if data exists
if 'master_data' not in st.session_state:
    st.session_state.master_data = load_from_hf()

if st.session_state.master_data is None:
    st.warning("Dataset not found on Hugging Face. Please Seed the Database.")
    if st.sidebar.button("🚀 Step 1: Seed Database (2008-Present)"):
        with st.spinner("Downloading 18 years of data... this takes a few minutes."):
            st.session_state.master_data = seed_dataset_from_scratch()
        st.success("Database seeded and uploaded to HF!")
else:
    if st.sidebar.button("🔄 Step 2: Daily Incremental Sync"):
        # (Existing incremental sync logic here)
        st.sidebar.write("Last Data Point:", st.session_state.master_data.index.max())

# --- REST OF THE UI ---
# Run Option A/B logic using st.session_state.master_data
