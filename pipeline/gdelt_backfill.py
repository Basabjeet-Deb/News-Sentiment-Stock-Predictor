"""
GDELT historical news backfill.

Purpose:
- Pull historical articles from the GDELT DOC 2.1 API (free public archive)
- Extract tickers mentioned in the text
- Run VADER sentiment + relevance scoring (same analyzer as the pipeline)
- Append into the project's append-only store: data/news_events.csv
- Cache raw pulls + maintain a simple checkpoint so we don't lose progress
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests

from app.core.config import STOCK_TICKERS
from pipeline.sentiment_analyzer import SentimentAnalyzer
from pipeline.time_series_dataset import TimeSeriesDatasetBuilder


GDELT_DOC_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


@dataclass
class BackfillConfig:
    data_dir: str
    days: int = 180
    max_records_per_day: int = 250
    page_size: int = 250
    sleep_s: float = 0.8
    query: str = (
        # Broad, finance-heavy query. We rely on ticker extraction to map to tickers.
        '(stock OR stocks OR share OR shares OR earnings OR guidance OR "price target" OR IPO OR merger OR acquisition)'
    )
    mode: str = "ArtList"
    format: str = "json"
    sort: str = "HybridRel"
    include_domains: Optional[List[str]] = None


def _fmt_dt(dt: datetime) -> str:
    # GDELT expects YYYYMMDDHHMMSS in UTC
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%d%H%M%S")


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _load_json(path: str) -> Optional[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _save_json(path: str, obj: Dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def _extract_tickers(text: str, ticker_set: Set[str]) -> List[str]:
    """
    Extract tickers from text using a conservative regex:
    - Supports 1-5 letters, optionally .X for class shares (BRK.B, BF.B)
    - Optional leading $ (e.g., $AAPL)
    """
    if not text:
        return []
    upper = text.upper()
    # Find potential ticker-like tokens.
    raw = re.findall(r"(?:^|[^A-Z0-9$])\$?([A-Z]{1,5}(?:\.[A-Z])?)\b", upper)
    out: List[str] = []
    for tok in raw:
        t = tok.strip().upper()
        if t in ticker_set:
            out.append(t)
    # De-dup, keep stable order
    seen = set()
    uniq = []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _gdelt_fetch_day(
    session: requests.Session,
    cfg: BackfillConfig,
    day: date,
) -> Tuple[List[Dict], Dict]:
    """
    Fetch up to cfg.max_records_per_day articles for the given UTC day.
    Returns (articles, meta)
    """
    start = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    fetched: List[Dict] = []
    start_record = 1
    calls = 0
    last_status = None
    last_error = None

    while len(fetched) < cfg.max_records_per_day:
        calls += 1
        params = {
            "query": cfg.query,
            "mode": cfg.mode,
            "format": cfg.format,
            "sort": cfg.sort,
            "startdatetime": _fmt_dt(start),
            "enddatetime": _fmt_dt(end),
            "maxrecords": min(cfg.page_size, cfg.max_records_per_day - len(fetched)),
            "startrecord": start_record,
        }
        if cfg.include_domains:
            # GDELT supports domain filters using domain: syntax in query.
            # We'll keep it simple by ANDing domains into the query string.
            dom_q = " OR ".join([f"domain:{d}" for d in cfg.include_domains])
            params["query"] = f"({cfg.query}) AND ({dom_q})"

        try:
            resp = session.get(GDELT_DOC_ENDPOINT, params=params, timeout=30)
            last_status = resp.status_code
            if resp.status_code != 200:
                last_error = f"http {resp.status_code}"
                break
            data = resp.json()
        except Exception as e:
            last_error = str(e)
            break

        articles = (data or {}).get("articles") or []
        if not articles:
            break

        fetched.extend(articles)
        # Next page. GDELT uses 1-indexed startrecord.
        start_record += len(articles)

        # Be polite
        if cfg.sleep_s:
            time.sleep(cfg.sleep_s)

        # Safety: if API keeps returning the same page, stop.
        if len(articles) == 0:
            break

    meta = {
        "day": str(day),
        "calls": calls,
        "fetched": len(fetched),
        "http_status": last_status,
        "error": last_error,
    }
    return fetched, meta


def backfill_gdelt(cfg: BackfillConfig) -> Dict:
    _ensure_dir(cfg.data_dir)
    cache_dir = os.path.join(cfg.data_dir, "gdelt_cache")
    _ensure_dir(cache_dir)
    state_path = os.path.join(cache_dir, "state.json")

    ticker_set = set([t.strip().upper() for t in STOCK_TICKERS if str(t).strip()])
    analyzer = SentimentAnalyzer()
    ds = TimeSeriesDatasetBuilder(data_dir=cfg.data_dir)

    state = _load_json(state_path) or {}
    # We always iterate from oldest -> newest so we can resume.
    today_utc = datetime.now(timezone.utc).date()
    start_day = today_utc - timedelta(days=int(cfg.days))

    # If we have a saved cursor, resume from there (inclusive).
    resume_day = state.get("resume_day")
    if resume_day:
        try:
            rd = datetime.fromisoformat(resume_day).date()
            if rd >= start_day and rd <= today_utc:
                start_day = rd
        except Exception:
            pass

    summary = {
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "days_requested": int(cfg.days),
        "start_day": str(start_day),
        "end_day": str(today_utc),
        "total_gdelt_articles": 0,
        "total_mapped_events": 0,
        "total_appended_events": 0,
        "days_completed": 0,
        "days_skipped_cached": 0,
        "errors": [],
    }

    with requests.Session() as session:
        session.headers.update({"User-Agent": "StockSense/1.0 (GDELT backfill)"})

        d = start_day
        while d <= today_utc:
            day_key = d.strftime("%Y%m%d")
            done_marker = os.path.join(cache_dir, f"{day_key}.done.json")
            raw_cache = os.path.join(cache_dir, f"{day_key}.raw.json")

            if os.path.exists(done_marker):
                summary["days_skipped_cached"] += 1
                summary["days_completed"] += 1
                d = d + timedelta(days=1)
                continue

            # Persist resume cursor early (so interruptions don't lose our place)
            state["resume_day"] = d.isoformat()
            _save_json(state_path, state)

            articles, meta = _gdelt_fetch_day(session=session, cfg=cfg, day=d)
            summary["total_gdelt_articles"] += int(meta.get("fetched") or 0)

            # Cache raw response (best effort)
            try:
                _save_json(raw_cache, {"meta": meta, "articles": articles})
            except Exception:
                pass

            if meta.get("error"):
                summary["errors"].append({"day": str(d), "error": meta.get("error"), "http_status": meta.get("http_status")})

            # Map -> project article schema, then analyze sentiment
            mapped: List[Dict] = []
            for a in articles:
                title = str(a.get("title") or "").strip()
                url = str(a.get("url") or "").strip()
                snippet = str(a.get("snippet") or "").strip()
                seendate = str(a.get("seendate") or "").strip()  # "YYYYMMDDTHHMMSSZ"
                source = str(a.get("sourceCountry") or a.get("sourceCollection") or a.get("source") or "GDELT").strip()

                # Parse seendate to a readable published_at
                published_at = ""
                try:
                    if seendate:
                        # e.g. 20260408T120000Z
                        published_at = datetime.strptime(seendate, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
                except Exception:
                    published_at = ""

                text_for_match = f"{title} {snippet}"
                tickers = _extract_tickers(text_for_match, ticker_set=ticker_set)
                if not tickers:
                    continue

                for t in tickers:
                    mapped.append(
                        {
                            "source": f"GDELT:{source}" if source else "GDELT",
                            "title": title,
                            "url": url,
                            "ticker": t,
                            "published_at": published_at,
                            "description": snippet,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            summary["total_mapped_events"] += len(mapped)

            if mapped:
                analyzed = analyzer.analyze_batch(mapped)
                filtered = analyzer.filter_relevant_impactful(analyzed)
                appended = ds.append_news_events(filtered)
                summary["total_appended_events"] += int(appended)

            # Mark day done (stores meta for debugging)
            try:
                _save_json(done_marker, {"meta": meta, "mapped_events": len(mapped), "appended_events": int(summary["total_appended_events"])})
            except Exception:
                pass

            summary["days_completed"] += 1
            d = d + timedelta(days=1)

    summary["status"] = "complete"
    summary["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Clear resume cursor since we've finished.
    try:
        state["resume_day"] = None
        _save_json(state_path, state)
    except Exception:
        pass

    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Backfill historical news using GDELT DOC 2.1 and store into news_events.csv")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--max-per-day", type=int, default=250)
    parser.add_argument("--sleep", type=float, default=0.8)
    parser.add_argument("--query", type=str, default=None)
    args = parser.parse_args()

    cfg = BackfillConfig(
        data_dir=args.data_dir,
        days=int(args.days),
        max_records_per_day=int(args.max_per_day),
        sleep_s=float(args.sleep),
        query=args.query or BackfillConfig.query,
    )
    out = backfill_gdelt(cfg)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

