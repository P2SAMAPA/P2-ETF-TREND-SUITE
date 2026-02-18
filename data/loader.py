def sync_incremental_data(df):
    last_date = pd.to_datetime(df.index.max())
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    sync_start = last_date + pd.Timedelta(days=1)
    
    # Check if we even need to sync (avoiding weekend/pre-market errors)
    if sync_start > pd.Timestamp.now():
        return df

    try:
        # Download from yfinance with specific configuration to avoid Multi-Index issues
        new_data_raw = yf.download(tickers, start=sync_start, progress=False, group_by='column')
        
        if new_data_raw.empty:
            return df

        # Logic to handle different yfinance return structures
        if 'Adj Close' in new_data_raw.columns:
            new_data = new_data_raw['Adj Close']
        elif 'Close' in new_data_raw.columns:
            new_data = new_data_raw['Close']
        else:
            # If it's a single ticker or flattened
            new_data = new_data_raw

        # Standardize: Ensure we only have the tickers we want and no empty columns
        new_data = new_data[new_data.columns.intersection(tickers)]
        
        # Combine with master dataframe
        combined = pd.concat([df, new_data]).sort_index()
        # Keep the most recent data point if duplicates occur
        combined = combined[~combined.index.duplicated(keep='last')]
        
        combined.to_csv(FILENAME)
        upload_to_hf(FILENAME)
        return combined

    except Exception as e:
        st.error(f"Sync failed: {e}")
        return df
