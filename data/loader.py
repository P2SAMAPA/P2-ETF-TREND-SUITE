def sync_incremental_data(df):
    # Ensure index is datetime
    df.index = pd.to_datetime(df.index)
    last_date = df.index.max()
    
    tickers = list(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    
    # Calculate sync start (day after last record)
    sync_start = last_date + pd.Timedelta(days=1)
    
    # If sync_start is in the future, nothing to do
    if sync_start > pd.Timestamp.now().normalize():
        st.info("Data is already up to date.")
        return df

    try:
        # Download new data
        new_data_raw = yf.download(tickers, start=sync_start, progress=False)
        
        if new_data_raw.empty:
            st.warning("No new market data found to sync.")
            return df

        # Handle columns
        if 'Adj Close' in new_data_raw.columns:
            new_data = new_data_raw['Adj Close']
        else:
            new_data = new_data_raw['Close']

        # Clean NaNs before merging
        new_data = new_data.dropna(how='all')

        # Combine, sort, and deduplicate
        combined = pd.concat([df, new_data]).sort_index()
        combined = combined[~combined.index.duplicated(keep='last')]
        
        # Forward fill any holes in the middle, but don't fill the end
        combined = combined.ffill()

        # Save and Push
        combined.to_csv(FILENAME)
        upload_to_hf(FILENAME)
        
        st.success(f"Synced successfully up to {combined.index.max().date()}")
        return combined

    except Exception as e:
        st.error(f"Sync failed error: {e}")
        return df
