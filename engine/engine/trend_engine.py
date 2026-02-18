import numpy as np
import pandas as pd

def run_trend_module(prices, daily_sofr, vol_target):
    # 1. Signals (20-day Keltner/Donchian)
    d_high = prices.rolling(20).max()
    k_sma = prices.rolling(20).mean()
    atr = (prices.rolling(20).max() - prices.rolling(20).min()) / 2
    k_upper = k_sma + (2 * atr)
    
    entry_band = np.minimum(d_high, k_upper)
    signals = (prices > entry_band.shift(1)).astype(int)
    
    # 2. Risk Parity Weighting
    rets = prices.pct_change()
    real_vol = rets.rolling(21).std() * np.sqrt(252)
    
    n = len(prices.columns)
    weights = (vol_target / n) / real_vol.shift(1)
    
    # 3. Strategy Returns (Positions + Cash Interest)
    strat_rets = (signals.shift(1) * weights.shift(1) * rets).sum(axis=1)
    unused_cap = 1 - (signals.shift(1) * weights.shift(1)).sum(axis=1)
    strat_rets += unused_cap.clip(0, 1) * (daily_sofr / 252)
    
    equity_curve = (1 + strat_rets).cumprod()
    
    # Next Day Allocation
    tomorrow_sig = (prices.iloc[-1] > entry_band.iloc[-1]).astype(int)
    tomorrow_w = (vol_target / n) / real_vol.iloc[-1]
    alloc = pd.DataFrame({
        "Ticker": prices.columns,
        "Weight (%)": (tomorrow_sig * tomorrow_w * 100).round(2)
    })
    
    return {"curve": equity_curve, "alloc": alloc}
