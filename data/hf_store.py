import pandas as pd
from datasets import load_dataset as hf_load_dataset

DATASET_PATH = "P2SAMAPA/etf_trend_data"

def load_dataset():
    dataset = hf_load_dataset(DATASET_PATH)

    # HF datasets return a dict of splits
    if "train" in dataset:
        dataset = dataset["train"]

    df = dataset.to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"])

    return df
