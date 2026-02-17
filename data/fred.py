import os
import pandas as pd
from fredapi import Fred

def get_sofr_series():
    fred = Fred(api_key=os.getenv("FRED_API_KEY"))
    sofr = fred.get_series("SOFR")
    sofr = sofr.to_frame("sofr")
    sofr.index = pd.to_datetime(sofr.index)
    sofr["sofr"] = sofr["sofr"] / 100
    return sofr
