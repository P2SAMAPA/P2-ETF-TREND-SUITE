def compute_metrics(returns):

    import numpy as np

    ann_factor = 252

    cagr = (1 + returns.mean()) ** ann_factor - 1
    vol = returns.std() * (ann_factor ** 0.5)
    sharpe = cagr / vol if vol != 0 else 0

    cumulative = (1 + returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    max_dd = drawdown.min()

    return {
        "cagr": cagr,
        "vol": vol,
        "sharpe": sharpe,
        "max_dd": max_dd,
    }
