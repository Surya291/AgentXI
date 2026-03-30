"""
Track which RSS item links have already been seen so that polls only surface
genuinely new articles.

Persists a flat set of guids (links) to data/rss_feed_state.json.
"""
from __future__ import annotations

import json
from pathlib import Path

from .models import NewsItem

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STATE_PATH = DATA_DIR / "rss_feed_state.json"


def _load(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {"seen_guids": []}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_seen_guids(path: Path = STATE_PATH) -> set[str]:
    return set(_load(path).get("seen_guids", []))


def mark_seen(items: list[NewsItem], path: Path = STATE_PATH) -> None:
    data = _load(path)
    seen: set[str] = set(data.get("seen_guids", []))
    for item in items:
        seen.add(item.guid)
    data["seen_guids"] = sorted(seen)
    _save(data, path)


def filter_new(items: list[NewsItem], path: Path = STATE_PATH) -> list[NewsItem]:
    """Return only items not yet seen, and mark them as seen."""
    seen = load_seen_guids(path)
    new_items = [i for i in items if i.guid not in seen]
    if new_items:
        mark_seen(new_items, path)
    return new_items


def reset_state(path: Path = STATE_PATH) -> None:
    """Wipe seen-state so the next poll returns everything."""
    _save({"seen_guids": []}, path)
