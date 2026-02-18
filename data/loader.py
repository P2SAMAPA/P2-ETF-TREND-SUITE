def sync_incremental_data(df_existing):
    """Downloads only missing data since last update and saves to HF."""
    import yfinance as yf
    
    # Identify last date in the CSV
    last_date = pd.to_datetime(df_existing.index).max()
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    
    # Fetch new bars from yfinance or stooq
    new_data = yf.download(tickers, start=last_date, progress=False)['Adj Close']
    
    # Combine (Drop duplicates to avoid double-counting the last day)
    combined = pd.concat([df_existing, new_data])
    combined = combined[~combined.index.duplicated(keep='last')].sort_index()
    
    # Save & Push
    combined.to_csv(FILENAME)
    api = HfApi()
    api.upload_file(
        path_or_fileobj=FILENAME,
        path_in_repo=FILENAME,
        repo_id=REPO_ID,
        repo_type="dataset",
        token=st.secrets["HF_TOKEN"]
    )
    return combined
