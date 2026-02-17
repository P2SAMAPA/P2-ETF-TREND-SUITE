import os
import pandas as pd
import yfinance as yf
from huggingface_hub import HfApi

DATASET_PATH = "P2SAMAPA/etf_trend_data"

def update_market_data(df):

    tickers = df["ticker"].unique()
    all_new = []

    for ticker in tickers:
        last_date = df[df["ticker"] == ticker]["date"].max()
        start_date = (last_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

        new_data = yf.download(ticker, start=start_date, progress=False)

        if new_data.empty:
            continue

        new_data.reset_index(inplace=True)
        new_data["ticker"] = ticker
        new_data.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adjusted_close",
            "Volume": "volume"
        }, inplace=True)

        all_new.append(new_data)

    if not all_new:
        return df

    new_df = pd.concat(all_new)
    df = pd.concat([df, new_df])
    df.drop_duplicates(subset=["date", "ticker"], inplace=True)
    df.sort_values(["ticker", "date"], inplace=True)

    df.to_parquet("updated.parquet")

    api = HfApi()
    api.upload_file(
        path_or_fileobj="updated.parquet",
        path_in_repo="data/train-00000-of-00001.parquet",
        repo_id=DATASET_PATH,
        repo_type="dataset",
        token=os.getenv("HF_TOKEN")
    )

    return df
