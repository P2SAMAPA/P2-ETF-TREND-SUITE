import numpy as np
import pandas as pd

def run_trend_module(prices, daily_sofr, vol_target):
    # 1. Dual-Trend Signal
    d_high = prices.rolling(20).max()
    sma = prices.rolling(20).mean()
    atr = (prices.rolling(20).max() - prices.rolling(20).min()) / 2
    k_upper = sma + (2 * atr)
    
    entry_band = np.minimum(d_high, k_upper)
    signals = (prices > entry_band.shift(1)).astype(int)
    
    # 2. Risk Parity Position Sizing
    returns = prices.pct_change()
    realized_vol = returns.rolling(21).std() * np.sqrt(252)
    
    n = len(prices.columns)
    # Target weight = (Target Vol / Total Assets) / Individual Asset Vol
    target_weights = (vol_target / n) / realized_vol.shift(1)
    
    # 3. Strategy Returns (Positions + SOFR on Cash)
    pos_rets = (signals.shift(1) * target_weights.shift(1) * returns).sum(axis=1)
    weight_used = (signals.shift(1) * target_weights.shift(1)).sum(axis=1)
    cash_rets = (1 - weight_used).clip(0, 1) * (daily_sofr / 252)
    
    strat_rets = pos_rets + cash_rets
    equity_curve = (1 + strat_rets).fillna(0).cumprod()
    
    # 4. Target Allocation for Tomorrow
    tomorrow_sig = (prices.iloc[-1] > entry_band.iloc[-1]).astype(int)
    tomorrow_w = (vol_target / n) / realized_vol.iloc[-1]
    
    alloc = pd.DataFrame({
        "Ticker": prices.columns,
        "Signal": ["LONG" if s == 1 else "CASH" for s in tomorrow_sig],
        "Weight (%)": (tomorrow_sig * tomorrow_w * 100).round(2)
    })
    
    return {"curve": equity_curve, "alloc": alloc}
