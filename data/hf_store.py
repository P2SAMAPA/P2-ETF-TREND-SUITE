from datasets import load_dataset
import pandas as pd

DATASET_PATH = "P2SAMAPA/etf_trend_data"

def load_dataset():
    dataset = load_dataset(DATASET_PATH, split="train")
    df = dataset.to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    return df
