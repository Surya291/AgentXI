"""Fetch and parse the CricTracker IPL RSS feed."""
from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

from .models import NewsItem

FEED_URL = "https://www.crictracker.com/t20/ipl-indian-premier-league/feed/"
_CDATA_RE = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)


def _strip_cdata(text: Optional[str]) -> str:
    if not text:
        return ""
    m = _CDATA_RE.search(text)
    return m.group(1).strip() if m else text.strip()


def _get_tag_text(elem: ET.Element, tag: str) -> str:
    child = elem.find(tag)
    if child is None:
        return ""
    raw = (child.text or "").strip()
    return _strip_cdata(raw) if raw else ""


def fetch_feed(url: str = FEED_URL, timeout: int = 15) -> list[NewsItem]:
    """
    Fetch the RSS feed and return a list of NewsItems sorted newest-first.
    Raises urllib.error.URLError / http.client.RemoteDisconnected on network failures.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AgentXI-RSS/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw_xml = resp.read()

    root = ET.fromstring(raw_xml)
    channel = root.find("channel")
    if channel is None:
        return []

    items: list[NewsItem] = []
    now = datetime.now(timezone.utc)

    for item_elem in channel.findall("item"):
        title = _get_tag_text(item_elem, "title")
        description = _get_tag_text(item_elem, "description")
        link = _get_tag_text(item_elem, "link")
        pub_date = _get_tag_text(item_elem, "pubDate")

        if not link:
            continue

        items.append(
            NewsItem(
                title=title,
                description=description,
                link=link,
                pub_date=pub_date,
                parsed_at=now,
            )
        )

    return items
