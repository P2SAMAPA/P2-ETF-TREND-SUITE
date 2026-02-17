def run_backtest(df, initial_capital, vol_target, lookback):

    import numpy as np
    import pandas as pd

    returns = df.pct_change().dropna()

    momentum = df.pct_change(lookback)

    weights = (momentum > 0).astype(int)
    weights = weights.div(weights.sum(axis=1), axis=0).fillna(0)

    strategy_returns = (weights.shift(1) * returns).sum(axis=1)

    equity_curve = (1 + strategy_returns).cumprod() * initial_capital

    return {
        "returns": strategy_returns,
        "equity_curve": equity_curve,
    }
