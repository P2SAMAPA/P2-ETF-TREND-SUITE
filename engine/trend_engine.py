import pandas as pd
import numpy as np
import pandas_market_calendars as mcal

def run_trend_module(price_df, bench_series, sofr_series, target_vol, start_yr):
    # 1. Signal Logic: Dual SMA Crossover
    sma_fast = price_df.rolling(50).mean()
    sma_slow = price_df.rolling(200).mean()
    signals = (sma_fast > sma_slow).astype(int)
    
    # 2. Volatility Logic: 60-Day Realized Standard Deviation
    returns = price_df.pct_change()
    asset_vol = returns.rolling(60).std() * np.sqrt(252)
    
    # 3. Risk-Budgeted Weighting
    # Methodology: Allocation = (Target Vol / Asset Vol) / Number of Active Assets
    # This ensures that each trending asset contributes a fixed 'slice' of risk.
    active_counts = signals.sum(axis=1)
    
    # Weight per asset: Target Vol divided by Asset Vol, then distributed among active trends
    raw_weights = (target_vol / asset_vol).divide(active_counts, axis=0).fillna(0)
    final_weights = raw_weights * signals
    
    # 4. Leverage Cap & Cash Logic
    # We cap total gross exposure at 1.5x (150%) to prevent extreme tail risk
    total_exposure = final_weights.sum(axis=1)
    scale_factor = total_exposure.apply(lambda x: 1.5/x if x > 1.5 else 1.0)
    final_weights = final_weights.multiply(scale_factor, axis=0)
    
    # Recalculate exposure after capping
    final_exposure = final_weights.sum(axis=1)
    cash_weight = 1.0 - final_exposure
    
    # 5. Returns: Asset Performance + Cash (SOFR) Interest
    # If exposure is < 100%, the remainder earns SOFR interest
    portfolio_ret = (final_weights.shift(1) * returns).sum(axis=1)
    portfolio_ret += cash_weight.shift(1) * (sofr_series.shift(1) / 252)
    
    bench_returns = bench_series.pct_change().fillna(0)
    
    # 6. OOS Performance Slicing
    oos_mask = portfolio_ret.index.year >= start_yr
    equity_curve = (1 + portfolio_ret[oos_mask]).cumprod()
    bench_curve = (1 + bench_returns[oos_mask]).cumprod()
    
    # 7. Drawdown & Stats
    dd_series = (equity_curve / equity_curve.cummax()) - 1
    ann_ret = portfolio_ret[oos_mask].mean() * 252
    ann_vol = portfolio_ret[oos_mask].std() * np.sqrt(252)
    
    # NYSE Calendar for Next Session
    nyse = mcal.get_calendar('NYSE')
    last_dt = price_df.index[-1]
    next_day = nyse.schedule(start_date=last_dt, end_date=last_dt + pd.Timedelta(days=10)).index[1]
    
    return {
        'equity_curve': equity_curve,
        'bench_curve': bench_curve,
        'ann_ret': ann_ret,
        'sharpe': (ann_ret - sofr_series.iloc[-1]) / ann_vol if ann_vol > 0 else 0,
        'max_dd_peak': dd_series.min(),
        'avg_daily_dd': dd_series.mean(),
        'next_day': next_day.date(),
        'current_weights': final_weights.iloc[-1],
        'cash_weight': cash_weight.iloc[-1],
        'current_sofr': sofr_series.iloc[-1]
    }
