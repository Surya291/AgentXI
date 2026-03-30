"""
Fetch the text body of a news article from its URL.

Uses only stdlib: urllib + html.parser.
Returns plain text, stripping all tags.
"""
from __future__ import annotations

import html
import re
import urllib.request
from html.parser import HTMLParser

_SKIP_TAGS = {"script", "style", "noscript", "nav", "footer", "header", "aside"}
_BLOCK_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "tr", "div", "article", "section", "br",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth: int = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        if tag in _BLOCK_TAGS and self._skip_depth == 0:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(html.unescape(f"&#{name};"))

    def get_text(self) -> str:
        raw = "".join(self._parts)
        lines = [ln.strip() for ln in raw.splitlines()]
        # collapse blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
        return cleaned.strip()


def fetch_article(url: str, timeout: int = 20, max_chars: int = 8_000) -> str:
    """
    Fetch the article at `url` and return its plain-text content.

    Args:
        url:       Full article URL.
        timeout:   HTTP timeout in seconds.
        max_chars: Truncate output after this many characters to keep
                   it token-friendly for the LLM.

    Returns:
        Plain-text body, or an error string starting with 'ERROR:'.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; AgentXI-Fetcher/1.0)"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return f"ERROR: {exc}"

    parser = _TextExtractor()
    parser.feed(raw_html)
    text = parser.get_text()

    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... truncated ...]"

    return text
