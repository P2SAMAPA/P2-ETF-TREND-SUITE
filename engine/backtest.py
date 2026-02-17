import pandas as pd
import numpy as np

def run_backtest(df, initial_capital, vol_target, lookback):

    df = df.sort_values(["ticker", "date"])
    prices = df.pivot(index="date", columns="ticker", values="adjusted_close")
    returns = prices.pct_change().dropna()

    momentum = prices.pct_change(lookback)
    signal = momentum.rank(axis=1, ascending=False)
    top = signal <= 3

    weights = top.div(top.sum(axis=1), axis=0)

    rolling_cov = returns.rolling(60).cov()
    vol = []

    for date in weights.index:
        if date not in rolling_cov.index:
            vol.append(0)
            continue

        w = weights.loc[date].values
        cov = rolling_cov.loc[date].values.reshape(len(w), len(w))
        portfolio_vol = np.sqrt(w @ cov @ w) * np.sqrt(252)

        scale = vol_target / portfolio_vol if portfolio_vol > 0 else 0
        weights.loc[date] = w * scale
        vol.append(portfolio_vol)

    strategy_returns = (weights.shift(1) * returns).sum(axis=1)
    equity_curve = (1 + strategy_returns).cumprod() * initial_capital

    latest_weights = weights.iloc[-1]
    allocation = pd.DataFrame({
        "Ticker": latest_weights.index,
        "Weight": latest_weights.values
    }).sort_values("Weight", ascending=False)

    return {
        "returns": strategy_returns,
        "equity_curve": equity_curve,
        "latest_allocation": allocation
    }

