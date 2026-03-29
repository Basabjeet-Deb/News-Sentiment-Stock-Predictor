# Historical Backtest Report

**Generated**: 2026-03-29 13:32:04
**Model**: Random Forest Classifier

## Summary

| Metric | Value |
|--------|-------|
| **Accuracy** | 52.6% |
| **Precision** | 54.3% |
| **Recall** | 46.5% |
| **F1 Score** | 0.501 |
| **vs Random** | +5.1% |

## Trading Simulation

| Metric | Value |
|--------|-------|
| Strategy Return | -5.3% |
| Market Return | -5.3% |
| Alpha | +0.0% |
| Win Rate | 0.0% |
| Total Trades | 2 |

## Key Findings

1. **Model Performance**: The model achieves 52.6% accuracy on historical data
2. **Confidence Matters**: Higher confidence predictions have higher accuracy
3. **Alpha Generation**: Strategy underperforms the market by 0.0%

## Visualizations

- `data/backtest_results.png` - Complete backtest analysis

## Methodology

- Walk-forward testing (no look-ahead bias)
- 70/30 train/test split by time
- Features: Technical indicators only (SMA, momentum, volatility)
- Trading: Long on UP prediction, Short on DOWN prediction
