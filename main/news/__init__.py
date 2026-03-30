"""
AgentXI news module.

Public API
----------
fetch_feed()          -> list[NewsItem]   # parse the RSS feed
poll_for_new()        -> list[NewsItem]   # new items since last poll (persists state)
fetch_article(url)    -> str              # plain-text body of an article
"""
from .article_fetch import fetch_article
from .models import NewsItem
from .poll import poll_for_new
from .rss_client import fetch_feed

__all__ = ["fetch_feed", "poll_for_new", "fetch_article", "NewsItem"]
