"""
Dedupe and cap news articles before sentiment (RAM + runtime budget).
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from dateutil import parser as date_parser


def _normalize_url(url: str) -> str:
    if not url or not isinstance(url, str):
        return ""
    u = url.strip().lower()
    if not u:
        return ""
    try:
        p = urlparse(u)
        path = (p.path or "").rstrip("/")
        return f"{p.netloc}{path}"
    except Exception:
        return u.split("?", 1)[0]


def _article_dedupe_key(article: Dict) -> str:
    u = _normalize_url(article.get("url") or "")
    t = (article.get("title") or "").strip().lower()[:500]
    return f"{u}|{t}"


def dedupe_articles(articles: List[Dict]) -> List[Dict]:
    """Drop duplicates by normalized URL + title (fast, no fuzzy matching)."""
    seen: set = set()
    out: List[Dict] = []
    for a in articles:
        title = (a.get("title") or "").strip()
        if not title:
            out.append(a)
            continue
        key = _article_dedupe_key(a)
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def parse_article_datetime(article: Dict) -> Optional[datetime]:
    """Best-effort parse from published_at or scraped_at."""
    for field in ("published_at", "scraped_at"):
        raw = article.get(field)
        if not raw or not isinstance(raw, str):
            continue
        raw = raw.strip()
        if not raw:
            continue
        try:
            return date_parser.parse(raw, fuzzy=True)
        except (ValueError, TypeError, OverflowError):
            continue
    return None


def sort_newest_first(articles: List[Dict]) -> List[Dict]:
    def sort_key(a: Dict) -> datetime:
        dt = parse_article_datetime(a)
        return dt or datetime.min

    return sorted(articles, key=sort_key, reverse=True)


def cap_articles(articles: List[Dict], max_count: int) -> List[Dict]:
    if max_count <= 0 or len(articles) <= max_count:
        return articles
    return articles[:max_count]


def prepare_articles_for_pipeline(articles: List[Dict], max_after_prep: int) -> List[Dict]:
    """
    Dedupe, sort newest first, then cap to max_after_prep.
    """
    d = dedupe_articles(articles)
    s = sort_newest_first(d)
    return cap_articles(s, max_after_prep)
