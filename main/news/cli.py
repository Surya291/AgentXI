#!/usr/bin/env python3
"""
CLI for the AgentXI news module.

Usage:
  python -m main.news poll               # print any new items since last poll
  python -m main.news fetch <url>        # print full article text
  python -m main.news latest [-n N]      # print N most recent items (no state update)
  python -m main.news reset-state        # wipe seen-state (next poll returns everything)
"""
from __future__ import annotations

import argparse
import json
import sys

from .article_fetch import fetch_article
from .poll import poll_for_new
from .rss_client import fetch_feed
from .state import reset_state


def cmd_poll(args: argparse.Namespace) -> None:
    new_items = poll_for_new()
    if not new_items:
        print("No new items.")
        return
    print(f"{len(new_items)} new item(s):\n")
    for item in new_items:
        print(f"  [{item.pub_date}]")
        print(f"  Title      : {item.title}")
        print(f"  Description: {item.description[:200]}{'...' if len(item.description) > 200 else ''}")
        print(f"  Link       : {item.link}")
        print()


def cmd_fetch(args: argparse.Namespace) -> None:
    text = fetch_article(args.url)
    print(text)


def cmd_latest(args: argparse.Namespace) -> None:
    items = fetch_feed()
    n = min(args.n, len(items))
    print(f"Latest {n} item(s) from feed:\n")
    for item in items[:n]:
        print(f"  [{item.pub_date}]")
        print(f"  Title      : {item.title}")
        print(f"  Description: {item.description[:200]}{'...' if len(item.description) > 200 else ''}")
        print(f"  Link       : {item.link}")
        print()


def cmd_latest_json(args: argparse.Namespace) -> None:
    items = fetch_feed()
    n = min(args.n, len(items))
    print(json.dumps([i.to_dict() for i in items[:n]], indent=2, ensure_ascii=False))


def cmd_reset_state(_args: argparse.Namespace) -> None:
    reset_state()
    print("Seen-state reset. Next poll will return all feed items.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m main.news",
        description="AgentXI news feed utilities",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("poll", help="Print new items since last poll")

    p_fetch = sub.add_parser("fetch", help="Print full text of an article")
    p_fetch.add_argument("url", help="Full article URL")

    p_latest = sub.add_parser("latest", help="Print N most recent feed items (no state update)")
    p_latest.add_argument("-n", type=int, default=5, help="Number of items (default 5)")

    p_latest_json = sub.add_parser("latest-json", help="Same as latest but outputs JSON")
    p_latest_json.add_argument("-n", type=int, default=5)

    sub.add_parser("reset-state", help="Wipe seen-state")

    args = parser.parse_args()
    dispatch = {
        "poll": cmd_poll,
        "fetch": cmd_fetch,
        "latest": cmd_latest,
        "latest-json": cmd_latest_json,
        "reset-state": cmd_reset_state,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
