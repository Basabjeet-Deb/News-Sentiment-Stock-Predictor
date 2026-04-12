"""
Ticker -> sector enrichment with persistent cache.

Why:
- Batch OHLC fetches from yfinance are reliable but do not include fundamentals like sector/industry.
- UI analytics (top sectors) becomes meaningless if everything is "Unknown".

Approach:
- Maintain data/ticker_sectors.csv as a persistent cache.
- Incrementally enrich missing tickers using yfinance.Ticker(t).info (slow, so throttled).
- Same fetch fills sector, industry, and company display name (longName / shortName).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

from pipeline.ticker_utils import yahoo_ticker_symbol


@dataclass
class SectorCachePaths:
    data_dir: str

    @property
    def sectors_csv(self) -> str:
        return os.path.join(self.data_dir, "ticker_sectors.csv")


class SectorCache:
    def __init__(self, data_dir: str):
        self.paths = SectorCachePaths(data_dir=data_dir)
        os.makedirs(self.paths.data_dir, exist_ok=True)

    def load(self) -> pd.DataFrame:
        cols = ["ticker", "sector", "industry", "company_name", "updated_at"]
        if not os.path.exists(self.paths.sectors_csv):
            return pd.DataFrame(columns=cols)
        try:
            df = pd.read_csv(self.paths.sectors_csv)
        except Exception:
            return pd.DataFrame(columns=cols)
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        df["ticker"] = df["ticker"].map(lambda x: yahoo_ticker_symbol(str(x)))
        df["sector"] = df["sector"].astype(str).str.strip()
        df["industry"] = df["industry"].astype(str).str.strip()
        df["company_name"] = df["company_name"].fillna("").astype(str).str.strip()
        df["company_name"] = df["company_name"].replace("nan", "", regex=False)
        df["updated_at"] = df["updated_at"].astype(str).str.strip()
        return df[cols].drop_duplicates(subset=["ticker"], keep="last")

    def to_map(self) -> Dict[str, Dict[str, str]]:
        df = self.load()
        out: Dict[str, Dict[str, str]] = {}
        for _, r in df.iterrows():
            t = str(r.get("ticker", "")).upper().strip()
            if not t:
                continue
            cn = r.get("company_name", "")
            if cn is None or (isinstance(cn, float) and pd.isna(cn)):
                cn = ""
            else:
                cn = str(cn).strip()
            if cn.lower() == "nan":
                cn = ""
            out[t] = {
                "sector": str(r.get("sector", "") or "").strip(),
                "industry": str(r.get("industry", "") or "").strip(),
                "company_name": cn,
            }
        return out

    def save(self, df: pd.DataFrame) -> None:
        df = df.copy()
        df["ticker"] = df["ticker"].map(lambda x: yahoo_ticker_symbol(str(x)))
        df = df.dropna(subset=["ticker"])
        df = df[df["ticker"].str.len() > 0]
        for c in ["sector", "industry", "company_name", "updated_at"]:
            if c not in df.columns:
                df[c] = ""
        df.to_csv(self.paths.sectors_csv, index=False)

    def ensure(
        self,
        tickers: List[str],
        max_new: int = 80,
        sleep_s: float = 0.35,
    ) -> Dict[str, Dict[str, str]]:
        """
        Ensure cache has entries for tickers (best-effort).
        Only fetch up to `max_new` unknown tickers to keep pipeline responsive.
        Also backfills `company_name` when missing for known tickers (same cap).
        """
        tickers = [yahoo_ticker_symbol(str(t)) for t in tickers if str(t).strip()]
        tickers = list(dict.fromkeys(tickers))

        df = self.load()
        known = set(df["ticker"].tolist()) if not df.empty else set()

        missing: List[str] = []
        for t in tickers:
            if t not in known:
                missing.append(t)
                continue
            sub = df.loc[df["ticker"] == t]
            if sub.empty:
                missing.append(t)
                continue
            raw_cn = sub.iloc[-1].get("company_name", "")
            if raw_cn is None or (isinstance(raw_cn, float) and pd.isna(raw_cn)):
                cn = ""
            else:
                cn = str(raw_cn).strip()
            if cn.lower() == "nan":
                cn = ""
            if not cn:
                missing.append(t)

        target = missing[: max(0, int(max_new))]

        def _fetch_one(t: str) -> Tuple[str, str, str, str]:
            try:
                info = yf.Ticker(t).info or {}
                sector = str(info.get("sector") or "").strip() or "Unknown"
                industry = str(info.get("industry") or "").strip() or "Unknown"
                company = (
                    str(info.get("longName") or info.get("shortName") or info.get("displayName") or "")
                    .strip()
                )
                return t, sector, industry, company
            except Exception:
                return t, "Unknown", "Unknown", ""

        rows = []
        # Parallelize to speed up filling the cache, but keep workers modest
        # to avoid hammering Yahoo.
        max_workers = 8
        if target:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futs = {ex.submit(_fetch_one, t): t for t in target}
                for fut in as_completed(futs):
                    t, sector, industry, company = fut.result()
                    rows.append(
                        {
                            "ticker": t,
                            "sector": sector,
                            "industry": industry,
                            "company_name": company,
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
                    if sleep_s:
                        time.sleep(sleep_s)

        if rows:
            df2 = pd.DataFrame(rows)
            merged = pd.concat([df, df2], ignore_index=True) if not df.empty else df2
            merged = merged.drop_duplicates(subset=["ticker"], keep="last")
            self.save(merged)

        return self.to_map()


def main() -> None:
    """
    CLI: incrementally enrich sectors for the tracked universe.
    """
    import argparse
    from app.core.config import STOCK_TICKERS

    parser = argparse.ArgumentParser(description="Populate/refresh data/ticker_sectors.csv using yfinance .info (throttled).")
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--max-new", type=int, default=120)
    parser.add_argument("--sleep", type=float, default=0.35)
    args = parser.parse_args()

    data_dir = args.data_dir
    if not data_dir:
        # default repo data dir
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    cache = SectorCache(data_dir=data_dir)
    m = cache.ensure(STOCK_TICKERS, max_new=int(args.max_new), sleep_s=float(args.sleep))
    known_sec = sum(1 for v in m.values() if (v.get("sector") or "").strip() and v.get("sector") != "Unknown")
    known_names = sum(1 for v in m.values() if (v.get("company_name") or "").strip())
    print(f"[OK] Cache entries: {len(m)} (sectors resolved: {known_sec}, company names: {known_names})")


if __name__ == "__main__":
    main()

