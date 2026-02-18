import pandas as pd
import numpy as np
import pandas_market_calendars as mcal

def run_trend_module(price_df, bench_series, sofr_series, target_vol, start_yr):
    # 1. Full-period math for indicators
    sma_fast = price_df.rolling(50).mean()
    sma_slow = price_df.rolling(200).mean()
    signals = (sma_fast > sma_slow).astype(int)
    
    returns = price_df.pct_change()
    realized_vol = returns.rolling(60).std() * np.sqrt(252)
    weights = (target_vol / realized_vol).fillna(0).clip(upper=1.5)
    
    # 2. Strategy Returns
    asset_ret = (signals.shift(1) * weights.shift(1) * returns).mean(axis=1)
    cash_pct = 1 - signals.mean(axis=1)
    strat_returns = asset_ret + (cash_pct.shift(1) * (sofr_series.shift(1) / 252))
    bench_returns = bench_series.pct_change().fillna(0)
    
    # 3. Slice for OOS Period
    oos_mask = strat_returns.index.year >= start_yr
    oos_strat = strat_returns[oos_mask]
    oos_bench = bench_returns[oos_mask]
    
    equity_curve = (1 + oos_strat).cumprod()
    bench_curve = (1 + oos_bench).cumprod()
    
    # 4. Drawdowns
    hwm = equity_curve.cummax()
    dd_series = (equity_curve / hwm) - 1
    
    # 5. Next Day Trading Date
    nyse = mcal.get_calendar('NYSE')
    last_dt = price_df.index[-1]
    sched = nyse.schedule(start_date=last_dt, end_date=last_dt + pd.Timedelta(days=10))
    next_day = sched.index[1] if len(sched) > 1 else sched.index[0]
    
    ann_ret = oos_strat.mean() * 252
    ann_vol = oos_strat.std() * np.sqrt(252)
    
    return {
        'equity_curve': equity_curve,
        'bench_curve': bench_curve,
        'sharpe': (ann_ret - 0.03) / ann_vol if ann_vol > 0 else 0,
        'ann_ret': ann_ret,
        'max_dd_peak': dd_series.min(),
        'avg_daily_dd': dd_series.mean(),
        'next_day': next_day.date(),
        'current_signals': signals.iloc[-1]
    }
