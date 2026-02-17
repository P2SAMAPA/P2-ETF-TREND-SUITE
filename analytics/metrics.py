import numpy as np
import pandas as pd

def compute_metrics(returns, sofr):

    sofr_daily = sofr.reindex(returns.index).fillna(method="ffill")["sofr"] / 252
    excess = returns - sofr_daily

    sharpe = np.sqrt(252) * excess.mean() / excess.std()

    equity = (1 + returns).cumprod()
    cagr = equity.iloc[-1] ** (252 / len(equity)) - 1

    vol = returns.std() * np.sqrt(252)

    rolling_max = equity.cummax()
    drawdown = equity / rolling_max - 1
    max_dd = drawdown.min()

    return {
        "sharpe": sharpe,
        "cagr": cagr,
        "vol": vol,
        "max_dd": max_dd
    }

