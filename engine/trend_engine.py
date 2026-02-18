import pandas as pd
import numpy as np
import pandas_market_calendars as mcal

def run_trend_module(price_df, bench_series, sofr_series, target_vol, start_yr, sub_option):
    # 1. Trend & Conviction Logic
    sma_200 = price_df.rolling(200).mean()
    sma_50 = price_df.rolling(50).mean()
    
    # Conviction = Percentage distance above the 200 SMA
    conviction_score = (price_df / sma_200) - 1
    signals = (sma_50 > sma_200).astype(int)
    
    # 2. Risk Metrics
    returns = price_df.pct_change()
    asset_vol = returns.rolling(60).std() * np.sqrt(252)
    
    # 3. Apply Sub-Option Concentration
    if sub_option == "3 Highest Conviction":
        ranks = conviction_score.rank(axis=1, ascending=False)
        signals = ((ranks <= 3) & (signals == 1)).astype(int)
    elif sub_option == "1 Highest Conviction":
        ranks = conviction_score.rank(axis=1, ascending=False)
        signals = ((ranks <= 1) & (signals == 1)).astype(int)
    
    # 4. Volatility Target Weighting
    active_counts = signals.sum(axis=1)
    raw_weights = (target_vol / asset_vol).divide(active_counts, axis=0).replace([np.inf, -np.inf], 0).fillna(0)
    final_weights = raw_weights * signals
    
    # 5. Leverage Cap (1.5x)
    total_exposure = final_weights.sum(axis=1)
    scale_factor = total_exposure.apply(lambda x: 1.5/x if x > 1.5 else 1.0)
    final_weights = final_weights.multiply(scale_factor, axis=0)
    
    # 6. Cash (SOFR) Allocation
    cash_weight = 1.0 - final_weights.sum(axis=1)
    
    # 7. Portfolio Returns
    portfolio_ret = (final_weights.shift(1) * returns).sum(axis=1)
    portfolio_ret += cash_weight.shift(1) * (sofr_series.shift(1) / 252)
    
    # 8. Out-of-Sample Slicing
    oos_mask = portfolio_ret.index.year >= start_yr
    equity_curve = (1 + portfolio_ret[oos_mask]).cumprod()
    bench_curve = (1 + bench_series.pct_change().fillna(0)[oos_mask]).cumprod()
    
    # Stats
    ann_ret = portfolio_ret[oos_mask].mean() * 252
    ann_vol = portfolio_ret[oos_mask].std() * np.sqrt(252)
    dd = (equity_curve / equity_curve.cummax()) - 1
    
    # --- FIXED NEXT DAY LOGIC ---
    nyse = mcal.get_calendar('NYSE')
    last_dt = price_df.index[-1]
    
    # Generate schedule starting from the day AFTER last_dt to ensure we find the future open
    search_start = last_dt + pd.Timedelta(days=1)
    sched = nyse.schedule(start_date=search_start, end_date=search_start + pd.Timedelta(days=10))
    
    # Take the first valid trading day from the future schedule
    next_day = sched.index[0] 
    # ----------------------------
    
    return {
        'equity_curve': equity_curve,
        'bench_curve': bench_curve,
        'ann_ret': ann_ret,
        'sharpe': (ann_ret - sofr_series.iloc[-1]) / ann_vol if ann_vol > 0 else 0,
        'max_dd': dd.min(),
        'next_day': next_day.date(),
        'current_weights': final_weights.iloc[-1],
        'cash_weight': cash_weight.iloc[-1],
        'current_sofr': sofr_series.iloc[-1]
    }
