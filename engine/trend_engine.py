import pandas as pd
import numpy as np
import pandas_market_calendars as mcal

def run_trend_module(price_df, benchmark_df, sofr_series, target_vol=0.12):
    """
    Enhanced Engine for 2025 Dow Award Logic.
    Includes Dual Drawdowns and Benchmark Comparison.
    """
    # 1. Signals & Weights
    sma_fast = price_df.rolling(50).mean()
    sma_slow = price_df.rolling(200).mean()
    signals = (sma_fast > sma_slow).astype(int)
    
    returns = price_df.pct_change()
    realized_vol = returns.rolling(60).std() * np.sqrt(252)
    weights = (target_vol / realized_vol).fillna(0).clip(upper=1.5)
    
    # 2. Returns Calculation
    # Strategy
    asset_ret = (signals.shift(1) * weights.shift(1) * returns).mean(axis=1)
    cash_pct = 1 - signals.mean(axis=1)
    strat_returns = asset_ret + (cash_pct.shift(1) * (sofr_series.shift(1) / 252))
    
    # Benchmark (Buy & Hold)
    bench_returns = benchmark_df.pct_change().fillna(0)
    
    # Equity Curves
    equity_curve = (1 + strat_returns).cumprod()
    bench_curve = (1 + bench_returns).cumprod()
    
    # 3. Drawdown Calculations
    def get_dd_stats(curve):
        hwm = curve.cummax()
        dd = (curve / hwm) - 1
        return dd.min(), dd # Max DD and the full DD series
    
    max_dd_peak, dd_series = get_dd_stats(equity_curve)
    
    # 4. Next Trading Day & Allocations (NYSE Calendar)
    nyse = mcal.get_calendar('NYSE')
    last_date = price_df.index[-1]
    next_day = nyse.valid_days(start_date=last_date + pd.Timedelta(days=1), end_date=last_date + pd.Timedelta(days=10))[0]
    
    # Current Allocations (Based on most recent signals)
    current_signals = signals.iloc[-1]
    active_assets = current_signals[current_signals > 0].index.tolist()
    
    return {
        'equity_curve': equity_curve,
        'bench_curve': bench_curve,
        'strat_ret_series': strat_returns,
        'max_dd_peak': max_dd_peak,
        'dd_series': dd_series,
        'next_trading_day': next_day.date(),
        'active_assets': active_assets,
        'signals': current_signals
    }
