import pandas as pd
import numpy as np
import pandas_market_calendars as mcal

def run_trend_module(price_df, bench_series, sofr_series, target_vol, start_yr, sub_option):
    """
    Quantitative Engine based on Zarattini & Antonacci (2025).
    Implements Volatility Targeting and Conviction-based ETF Allocation.
    """
    
    # --- 1. DATA CLEANING & PREPARATION ---
    # Forward fill holes and drop assets with no data in the current window
    price_df = price_df.ffill()
    # Ensure benchmarks and SOFR are aligned
    sofr_series = sofr_series.ffill()
    
    # --- 2. TREND & CONVICTION SIGNALS ---
    sma_200 = price_df.rolling(200).mean()
    sma_50 = price_df.rolling(50).mean()
    
    # Conviction = % distance above the 200 SMA (momentum strength)
    conviction_score = (price_df / sma_200) - 1
    # Basic Signal: 50 SMA > 200 SMA
    base_signals = (sma_50 > sma_200).astype(int)
    
    # --- 3. CONVICTION FILTERING (Sub-Options) ---
    if sub_option == "3 Highest Conviction":
        # Rank assets daily; 1 is highest conviction. 
        # Only assets in a base trend (base_signals == 1) are eligible for ranking.
        ranked_conviction = conviction_score.where(base_signals == 1)
        ranks = ranked_conviction.rank(axis=1, ascending=False)
        final_signals = ((ranks <= 3)).astype(int)
    elif sub_option == "1 Highest Conviction":
        ranked_conviction = conviction_score.where(base_signals == 1)
        ranks = ranked_conviction.rank(axis=1, ascending=False)
        final_signals = ((ranks <= 1)).astype(int)
    else:
        # "All Trending ETFs"
        final_signals = base_signals
    
    # --- 4. VOLATILITY TARGETING (RISK BUDGETING) ---
    returns = price_df.pct_change()
    # 60-day Annualized Realized Volatility
    asset_vol = returns.rolling(60).std() * np.sqrt(252)
    
    # Safety: If vol is NaN or 0, set to a very high number to prevent infinite weights
    asset_vol = asset_vol.replace(0, np.nan).fillna(9.99)
    
    # Methodology: Target Vol / Asset Vol, distributed across active signals
    active_counts = final_signals.sum(axis=1)
    # Avoid division by zero if no assets are in trend
    raw_weights = (target_vol / asset_vol).divide(active_counts, axis=0).replace([np.inf, -np.inf], 0).fillna(0)
    
    # Multiply by signals to zero out non-trending assets
    final_weights = raw_weights * final_signals
    
    # --- 5. EXPOSURE & LEVERAGE MANAGEMENT ---
    total_exposure = final_weights.sum(axis=1)
    # Cap total gross leverage at 1.5x (150%)
    leverage_cap = 1.5
    scale_factor = total_exposure.apply(lambda x: leverage_cap/x if x > leverage_cap else 1.0)
    final_weights = final_weights.multiply(scale_factor, axis=0)
    
    # --- 6. CASH (SOFR) ALLOCATION ---
    # Remainder of the 100% capital not used in the risk budget goes to SOFR
    final_exposure = final_weights.sum(axis=1)
    cash_weight = 1.0 - final_exposure
    
    # --- 7. PERFORMANCE CALCULATION ---
    # Strategy Return = (Weights * Asset Returns) + (Cash Weight * SOFR)
    # We shift weights by 1 to prevent look-ahead bias (trading at today's close for tomorrow)
    portfolio_ret = (final_weights.shift(1) * returns).sum(axis=1)
    portfolio_ret += cash_weight.shift(1) * (sofr_series.shift(1) / 252)
    
    # --- 8. OUT-OF-SAMPLE (OOS) METRICS ---
    oos_mask = portfolio_ret.index.year >= start_yr
    oos_returns = portfolio_ret[oos_mask]
    
    equity_curve = (1 + oos_returns).cumprod()
    bench_returns = bench_series.pct_change().fillna(0)[oos_mask]
    bench_curve = (1 + bench_returns).cumprod()
    
    # Drawdowns
    dd_series = (equity_curve / equity_curve.cummax()) - 1
    
    # Stats
    ann_ret = oos_returns.mean() * 252
    ann_vol = oos_returns.std() * np.sqrt(252)
    current_sofr = sofr_series.ffill().iloc[-1]
    
    # Sharpe Ratio: (Return - RiskFree) / Vol
    sharpe = (ann_ret - current_sofr) / ann_vol if ann_vol > 0 else 0
    
    # --- 9. NEXT TRADING DAY CALENDAR ---
    nyse = mcal.get_calendar('NYSE')
    # Anchor to system clock to ensure we always look FORWARD
    today_dt = pd.Timestamp.now().normalize()
    search_start = today_dt + pd.Timedelta(days=1)
    sched = nyse.schedule(start_date=search_start, end_date=search_start + pd.Timedelta(days=10))
    next_day = sched.index[0]
    
    return {
        'equity_curve': equity_curve,
        'bench_curve': bench_curve,
        'ann_ret': ann_ret,
        'sharpe': sharpe,
        'max_dd': dd_series.min(),
        'next_day': next_day.date(),
        'current_weights': final_weights.iloc[-1],
        'cash_weight': cash_weight.iloc[-1],
        'current_sofr': current_sofr
    }
