"""
Shared ticker normalization for Yahoo Finance / yfinance.

Price batch downloads and OHLC keys use Yahoo's symbol form (e.g. BRK.B -> BRK-B).
Metadata caches must use the same keys so lookups align.
"""


def yahoo_ticker_symbol(ticker: str) -> str:
    t = (ticker or "").strip().upper()
    if not t:
        return t
    if "." in t:
        t = t.replace(".", "-")
    return t
