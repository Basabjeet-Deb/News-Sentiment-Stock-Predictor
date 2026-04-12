"""
Time-series dataset builder for News Sentiment Stock Predictor.

Goal:
- Turn scraped/analyzed news into a daily panel (ticker, date) with aggregated features
- Join with future returns labels from price history (yfinance)

This is the missing piece that makes the project a true forecasting system.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import yfinance as yf
import contextlib
import io


@dataclass
class DatasetPaths:
    data_dir: str

    @property
    def news_events_csv(self) -> str:
        return os.path.join(self.data_dir, "news_events.csv")

    @property
    def daily_panel_csv(self) -> str:
        return os.path.join(self.data_dir, "daily_panel.csv")


class TimeSeriesDatasetBuilder:
    """
    Maintains an append-only news events store and produces daily features + labels.

    Time axis:
    - Prefers `published_at` when parseable (critical for historical backfills)
    - Falls back to `scraped_at` (always present and reliable for "today" scraping)
    """

    def __init__(self, data_dir: str):
        self.paths = DatasetPaths(data_dir=data_dir)
        os.makedirs(self.paths.data_dir, exist_ok=True)

    def append_news_events(self, articles: List[Dict]) -> int:
        """
        Append raw/analyzed articles to `news_events.csv` with a stable schema.
        De-duplicates by URL+title+scraped_at (best-effort).
        """
        if not articles:
            return 0

        df = pd.DataFrame(articles).copy()

        # Normalize required fields
        if "scraped_at" not in df.columns:
            df["scraped_at"] = datetime.now(timezone.utc).isoformat()

        # Keep only columns we know how to use; keep extras too for later analysis
        # but enforce key fields.
        for col in ["title", "url", "source", "ticker", "published_at", "description"]:
            if col not in df.columns:
                df[col] = ""

        # Sentiment analyzer outputs these flat fields
        for col in [
            "sentiment_compound",
            "sentiment_positive",
            "sentiment_negative",
            "sentiment_neutral",
            "sentiment_label",
            "impact_level",
            "relevance_score",
            "is_relevant",
            "is_impactful",
        ]:
            if col not in df.columns:
                df[col] = np.nan

        # Parse scraped_at to datetime
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce", utc=True)
        df = df[df["scraped_at"].notna()].copy()

        # Basic cleanup
        df["ticker"] = df["ticker"].fillna("").astype(str).str.upper().str.strip()
        df["title"] = df["title"].fillna("").astype(str).str.strip()
        df["url"] = df["url"].fillna("").astype(str).str.strip()
        df["source"] = df["source"].fillna("").astype(str).str.strip()

        # Best-effort filter: keep market-wide items too (ticker empty),
        # but drop empty-title rows.
        df = df[df["title"].str.len() > 5].copy()

        # De-duplicate against existing store if present
        df["_dedupe_key"] = (
            df["title"].str.lower().str.slice(0, 200)
            + "|"
            + df["url"].str.lower().str.slice(0, 300)
            + "|"
            + df["ticker"].astype(str).str.upper().str.strip().str.slice(0, 15)
            + "|"
            + df["scraped_at"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        )

        existing_keys = set()
        if os.path.exists(self.paths.news_events_csv):
            try:
                existing = pd.read_csv(self.paths.news_events_csv, usecols=["_dedupe_key"])
                existing_keys = set(existing["_dedupe_key"].dropna().astype(str).tolist())
            except Exception:
                existing_keys = set()

        df = df[~df["_dedupe_key"].isin(existing_keys)].copy()
        if df.empty:
            return 0

        # Append
        write_header = not os.path.exists(self.paths.news_events_csv)
        df.to_csv(self.paths.news_events_csv, mode="a", header=write_header, index=False)
        return len(df)

    def build_daily_panel(
        self,
        tickers: List[str],
        horizon_days: int = 1,
        lookback_days: int = 90,
    ) -> pd.DataFrame:
        """
        Build a daily (ticker, date) dataset with news aggregates and forward-return labels.
        """
        if not os.path.exists(self.paths.news_events_csv):
            raise FileNotFoundError("news_events.csv not found. Run pipeline scraping first.")

        events = pd.read_csv(self.paths.news_events_csv)
        events["scraped_at"] = pd.to_datetime(events["scraped_at"], errors="coerce", utc=True)
        events = events[events["scraped_at"].notna()].copy()

        # Prefer published_at if it looks parseable; otherwise fall back to scraped_at.
        if "published_at" in events.columns:
            events["_published_at_dt"] = pd.to_datetime(events["published_at"], errors="coerce", utc=True)
            # Some sources/backfills can contain sentinel/invalid ancient dates (e.g., year 0001).
            # Treat anything unrealistically old as invalid and fall back to scraped_at.
            try:
                too_old = events["_published_at_dt"] < pd.Timestamp("2000-01-01", tz="UTC")
                events.loc[too_old, "_published_at_dt"] = pd.NaT
            except Exception:
                pass
            events["_event_time"] = events["_published_at_dt"].where(events["_published_at_dt"].notna(), events["scraped_at"])
        else:
            events["_event_time"] = events["scraped_at"]

        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        events = events[events["_event_time"] >= cutoff].copy()

        # Derive date bucket (UTC day)
        events["date"] = events["_event_time"].dt.date.astype(str)
        events["ticker"] = events["ticker"].fillna("").astype(str).str.upper().str.strip()

        # Numeric conversions
        for col in ["sentiment_compound", "relevance_score"]:
            if col in events.columns:
                events[col] = pd.to_numeric(events[col], errors="coerce")

        # Aggregate per ticker-date, plus market-wide (ticker empty) features we can later join.
        per = events[events["ticker"].isin([t.upper() for t in tickers])].copy()
        if per.empty:
            raise ValueError("No ticker-tagged events available yet. Scraper may not be extracting tickers.")

        daily = (
            per.groupby(["ticker", "date"])
            .agg(
                news_count=("title", "count"),
                sent_mean=("sentiment_compound", "mean"),
                sent_std=("sentiment_compound", "std"),
                sent_min=("sentiment_compound", "min"),
                sent_max=("sentiment_compound", "max"),
                relevance_mean=("relevance_score", "mean"),
                high_impact_count=("impact_level", lambda s: int((s == "high").sum()) if hasattr(s, "__len__") else 0),
                macro_count=("impact_level", lambda s: int((s == "macro").sum()) if hasattr(s, "__len__") else 0),
            )
            .reset_index()
        )

        # Fill NaNs from std etc.
        daily["sent_std"] = daily["sent_std"].fillna(0.0)
        daily["relevance_mean"] = daily["relevance_mean"].fillna(0.0)
        daily["sent_mean"] = daily["sent_mean"].fillna(0.0)
        daily["sent_min"] = daily["sent_min"].fillna(0.0)
        daily["sent_max"] = daily["sent_max"].fillna(0.0)

        # Labels: forward return using close prices
        labels = self._build_forward_return_labels(
            tickers=tickers,
            horizon_days=horizon_days,
            lookback_days=lookback_days + horizon_days + 10,
        )

        # IMPORTANT: Make the panel a real time series.
        # Use labels as the base calendar (trading days) and left-join daily news features.
        # This ensures we keep "zero-news days" so the model can learn dynamics over time.
        base = labels.copy()
        daily = daily.copy()
        panel = base.merge(daily, on=["ticker", "date"], how="left")

        # Fill missing news features for days with no articles
        fill0 = [
            "news_count",
            "sent_mean",
            "sent_std",
            "sent_min",
            "sent_max",
            "relevance_mean",
            "high_impact_count",
            "macro_count",
        ]
        for c in fill0:
            if c in panel.columns:
                panel[c] = pd.to_numeric(panel[c], errors="coerce").fillna(0.0)

        # Add rolling features (3d/7d) on the completed series
        panel["date_dt"] = pd.to_datetime(panel["date"], errors="coerce")
        panel = panel[panel["date_dt"].notna()].copy()
        panel = panel.sort_values(["ticker", "date_dt"]).reset_index(drop=True)
        for win in [3, 7]:
            panel[f"sent_mean_roll{win}"] = (
                panel.groupby("ticker")["sent_mean"].transform(lambda s: s.rolling(win, min_periods=1).mean())
            )
            panel[f"news_count_roll{win}"] = (
                panel.groupby("ticker")["news_count"].transform(lambda s: s.rolling(win, min_periods=1).sum())
            )

        # Save
        panel.to_csv(self.paths.daily_panel_csv, index=False)
        return panel

    def _build_forward_return_labels(self, tickers: List[str], horizon_days: int, lookback_days: int) -> pd.DataFrame:
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=lookback_days)

        # Normalize tickers for Yahoo (class shares use "-")
        tickers_norm = [str(t).strip().upper().replace(".", "-") for t in tickers if str(t).strip()]
        tickers_norm = sorted(list(dict.fromkeys(tickers_norm)))

        if not tickers_norm:
            return pd.DataFrame(columns=["ticker", "date", "return_fwd", "direction_fwd"])

        # yfinance batch downloads can silently drop tickers if the request is too large.
        # Download in chunks to maximize coverage.
        def _chunks(xs: List[str], n: int) -> List[List[str]]:
            return [xs[i : i + n] for i in range(0, len(xs), n)]

        rows: List[Dict] = []
        for chunk in _chunks(tickers_norm, 75):
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    data = yf.download(
                        tickers=" ".join(chunk),
                        start=str(start),
                        end=str(end + timedelta(days=1)),
                        interval="1d",
                        group_by="ticker",
                        auto_adjust=False,
                        threads=True,
                        progress=False,
                    )
            except Exception:
                continue

            for t in chunk:
                try:
                    if isinstance(getattr(data, "columns", None), pd.MultiIndex):
                        if t not in data.columns.get_level_values(0):
                            continue
                        tdf = data[t].copy()
                    else:
                        # Single ticker response
                        tdf = data.copy()
                    if tdf is None or tdf.empty or "Close" not in tdf.columns:
                        continue
                    tdf = tdf.dropna(subset=["Close"]).copy()
                    tdf = tdf.reset_index()
                    date_col = "Date" if "Date" in tdf.columns else tdf.columns[0]
                    tdf[date_col] = pd.to_datetime(tdf[date_col], errors="coerce").dt.date.astype(str)
                    tdf = tdf.rename(columns={date_col: "date"})
                    tdf = tdf.sort_values("date")
                    tdf["close"] = pd.to_numeric(tdf["Close"], errors="coerce")
                    tdf = tdf[tdf["close"].notna()]
                    tdf["close_fwd"] = tdf["close"].shift(-horizon_days)
                    tdf["return_fwd"] = (tdf["close_fwd"] / tdf["close"]) - 1.0
                    tdf["direction_fwd"] = (tdf["return_fwd"] > 0).astype(int)
                    out = tdf[["date", "return_fwd", "direction_fwd"]].dropna()
                    out["ticker"] = t
                    rows.extend(out.to_dict("records"))
                except Exception:
                    continue

        if not rows:
            return pd.DataFrame(columns=["ticker", "date", "return_fwd", "direction_fwd"])
        return pd.DataFrame(rows)

