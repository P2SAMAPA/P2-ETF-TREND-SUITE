import pandas as pd
import numpy as np

def run_trend_module(price_df, sofr_series, target_vol=0.12):
    """
    Implements 2025 Dow Award Logic.
    """
    # 1. Dual-Trend Signal (Fast vs Slow SMA)
    sma_fast = price_df.rolling(50).mean()
    sma_slow = price_df.rolling(200).mean()
    # Signal is 1 if in trend, 0 if cash
    signals = (sma_fast > sma_slow).astype(int)
    
    # 2. Volatility Targeting (Inverse Vol Sizing)
    returns = price_df.pct_change()
    realized_vol = returns.rolling(60).std() * np.sqrt(252)
    # Weights = Target Vol / Realized Vol
    weights = (target_vol / realized_vol).fillna(0)
    weights = weights.clip(upper=1.5) # Cap leverage at 150%
    
    # 3. Portfolio Returns
    # Position = Signal * Weight
    asset_returns = (signals.shift(1) * weights.shift(1) * returns).mean(axis=1)
    
    # 4. Interest on Cash (SOFR)
    # If signals are 0 (in cash), we earn SOFR
    cash_percentage = 1 - signals.mean(axis=1)
    interest_returns = (cash_percentage.shift(1) * (sofr_series.shift(1) / 252))
    
    total_returns = asset_returns + interest_returns
    equity_curve = (1 + total_returns).fillna(0).cumprod()
    
    # 5. Metrics
    ann_ret = total_returns.mean() * 252
    ann_vol = total_returns.std() * np.sqrt(252)
    sharpe = (ann_ret - 0.035) / ann_vol if ann_vol > 0 else 0
    
    dd = equity_curve / equity_curve.cummax() - 1
    max_dd = dd.min()
    
    return {
        'equity_curve': equity_curve,
        'sharpe': sharpe,
        'ann_ret': ann_ret,
        'max_dd': max_dd,
        'current_signals': signals.iloc[-1]
    }
