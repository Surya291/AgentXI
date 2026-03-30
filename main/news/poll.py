"""
One-shot poll: fetch feed, diff against seen-state, return new items.

Designed to be called by a scheduler (cron, APScheduler, Hermes loop) once
per hour.  Does NOT sleep internally — the caller is responsible for timing.
"""
from __future__ import annotations

from .models import NewsItem
from .rss_client import fetch_feed, FEED_URL
from .state import filter_new


def poll_for_new(url: str = FEED_URL) -> list[NewsItem]:
    """
    Fetch `url`, compare against persisted seen-state, return new items.

    Side-effect: marks returned items as seen so the next call won't repeat them.
    Returns an empty list if nothing is new or on network error (logged to stderr).
    """
    import sys

    try:
        items = fetch_feed(url)
    except Exception as exc:
        print(f"[news.poll] Feed fetch failed: {exc}", file=sys.stderr)
        return []

    return filter_new(items)
