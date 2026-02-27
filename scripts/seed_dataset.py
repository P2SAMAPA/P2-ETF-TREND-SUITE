#!/usr/bin/env python3
"""
Rebuild ETF dataset from scratch and upload to HuggingFace.
Triggered manually via GitHub Actions.
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def main():
    from data.loader import seed_dataset_from_scratch, get_safe_token, FI_TICKERS, X_EQUITY_TICKERS
    
    logger.info("=" * 60)
    logger.info("ETF DATASET REBUILD - STARTED")
    logger.info("=" * 60)
    
    # Check token
    logger.info("Checking HF_TOKEN...")
    token = get_safe_token()
    if not token:
        logger.error("❌ HF_TOKEN not found!")
        logger.error("Set HF_TOKEN secret in GitHub repository settings")
        sys.exit(1)
    logger.info("✅ HF_TOKEN found")
    
    # Show configuration
    all_tickers = sorted(set(X_EQUITY_TICKERS + FI_TICKERS + ["SPY", "AGG"]))
    logger.info(f"Equity tickers: {len(X_EQUITY_TICKERS)}")
    logger.info(f"Fixed Income tickers: {len(FI_TICKERS)}")
    logger.info(f"Total unique tickers: {len(all_tickers)}")
    logger.info(f"FI Tickers: {FI_TICKERS}")
    
    # Check for TBT
    if 'TBT' in FI_TICKERS:
        logger.warning("⚠️  TBT is still in FI_TICKERS - did you update loader.py?")
    else:
        logger.info("✅ TBT not in ticker list (as expected)")
    
    # Check for required tickers
    required = ['VCIT', 'LQD', 'HYG']
    missing_required = [t for t in required if t not in FI_TICKERS]
    if missing_required:
        logger.error(f"❌ Missing required tickers: {missing_required}")
        sys.exit(1)
    logger.info(f"✅ All required tickers present: {required}")
    
    # Build dataset
    logger.info("-" * 60)
    logger.info("🚀 Downloading data from Yahoo Finance (2008-present)...")
    logger.info("⏳ This will take 3-5 minutes...")
    
    try:
        df = seed_dataset_from_scratch()
        
        logger.info("-" * 60)
        logger.info(f"✅ SUCCESS! Dataset rebuilt")
        logger.info(f"📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        logger.info(f"📅 Date range: {df.index.min().date()} to {df.index.max().date()}")
        
        # Verify columns
        price_cols = [c for c in df.columns if c not in ['SOFR_ANNUAL']]
        logger.info(f"📈 Price columns: {len(price_cols)}")
        
        # Final verification
        if 'TBT' in df.columns:
            logger.warning("⚠️  TBT column still exists in data!")
        else:
            logger.info("✅ TBT successfully excluded from dataset")
            
        logger.info("=" * 60)
        logger.info("UPLOAD TO HUGGINGFACE COMPLETE")
        logger.info("Dataset URL: https://huggingface.co/datasets/P2SAMAPA/etf_trend_data")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
