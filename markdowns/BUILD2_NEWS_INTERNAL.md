# Build 2 — News feed: internal architecture and code flow

Reference doc for the RSS poll, article fetch, and how it ties into player status timestamps. Repository root = `AgentXI/`.

---

## Layout

```
main/
  news/
    __init__.py             # Public API: fetch_feed, poll_for_new, fetch_article, NewsItem
    __main__.py             # Delegates to cli.main()
    models.py               # NewsItem dataclass + guid + (de)serialization
    rss_client.py           # urllib fetch + ElementTree RSS parse + CDATA strip
    state.py                # Persist seen article links → rss_feed_state.json
    poll.py                 # fetch_feed + filter_new (with error swallow)
    article_fetch.py        # HTMLParser-based plain-text extraction
    cli.py                  # argparse subcommands
  player_status.py          # last_updated UTC on each non-default row (Build 2 addition)
data/
  rss_feed_state.json       # { "seen_guids": [ "<url>", ... ] }  (sorted list)
```

---

## Persistence

| File | Role |
|------|------|
| `data/rss_feed_state.json` | Dedup set: article `link` strings treated as stable GUIDs. Written whenever `filter_new` marks items seen. |
| `data/player_status.json` | Per-player overrides; each saved row includes `last_updated` (ISO UTC, `...Z`) after any `update_player` that leaves a non-default state. |

Hermes can compare news `pubDate` / poll time against `last_updated` to avoid stale duplicate status proposals.

---

## `models.py`

- **`NewsItem`:** `title`, `description`, `link`, `pub_date` (raw RSS string), `parsed_at` (UTC `datetime` when parsed, CLI display uses raw `pub_date`).
- **`guid`:** property returning `link` — used as the dedup key (no separate RSS `<guid>` element required).
- **`to_dict` / `from_dict`:** for `latest-json` and any future serialization.

---

## `rss_client.py`

1. **`FEED_URL`:** CricTracker IPL RSS endpoint (default for fetch/poll).
2. **HTTP:** `urllib.request.Request` with `User-Agent: AgentXI-RSS/1.0`, `urlopen(..., timeout=15)`.
3. **Parse:** `xml.etree.ElementTree.fromstring` on response bytes; locate `channel`, iterate `item` children.
4. **Fields:** `title`, `description`, `link`, `pubDate` via `_get_tag_text`.
5. **CDATA:** regex `_CDATA_RE` unwraps `<![CDATA[...]]>` when present; otherwise strips whitespace.
6. **Skip:** items with empty `link` are dropped.
7. **Order:** feed order preserved (typically newest-first from publisher).

---

## `state.py`

- **`DATA_DIR`:** `Path(__file__).resolve().parents[2] / "data"` → `AgentXI/data`.
- **`_load` / `_save`:** JSON read/write; missing file ⇒ `{ "seen_guids": [] }`.
- **`load_seen_guids`:** returns `set` for O(1) membership.
- **`mark_seen`:** unions new item `guid`s into the list, **sorts** for stable diffs in git.
- **`filter_new`:** `new_items = [i for i in items if i.guid not in seen]`; if non-empty, **`mark_seen(new_items)`** then return `new_items`.  
  **Important:** marking happens for *all* newly returned items in one write — so a single poll persists every unseen link currently in the feed snapshot.
- **`reset_state`:** writes empty `seen_guids`.

---

## `poll.py`

- **`poll_for_new(url=FEED_URL)`:**  
  - `try: items = fetch_feed(url)`  
  - `except`: print `[news.poll] Feed fetch failed: ...` to **stderr**, return `[]`.  
  - else `return filter_new(items)`.

No internal sleep; scheduling is external (cron, Hermes loop, etc.).

---

## `article_fetch.py`

- **`_TextExtractor(HTMLParser)`:**  
  - Increments skip depth inside `script`, `style`, `noscript`, `nav`, `footer`, `header`, `aside` (drops boilerplate).  
  - Inserts newline before block-ish tags (`p`, headings, `li`, `div`, …) when not inside a skip region.  
  - Appends character data and resolves HTML entities via `html.unescape`.
- **`get_text`:** join fragments, strip each line, collapse 3+ newlines to 2.
- **`fetch_article`:** GET with browser-like `User-Agent`; decode UTF-8 with `errors="replace"`; on any exception return `"ERROR: {exc}"`.  
  - Truncate to **`max_chars` default 8_000** with suffix `[... truncated ...]`.

**Limitation:** full-page HTML includes nav chrome unless the site structure isolates article body; Hermes may still use title/description from RSS first.

---

## `cli.py`

| Subcommand | Behavior |
|------------|----------|
| `poll` | `poll_for_new()` → human-readable blocks (description clipped to 200 chars). |
| `fetch <url>` | `fetch_article(url)` → stdout. |
| `latest [-n]` | `fetch_feed()` → first N items; **does not** touch `rss_feed_state.json`. |
| `latest-json [-n]` | Same as `latest`, JSON array of `NewsItem.to_dict()`. |
| `reset-state` | `reset_state()`. |

Entry: `python -m main.news` → `cli.main()`.

---

## Integration with `player_status.py` (Build 2)

- On **`update_player`**, when the merged row is **not** default (`available` + form `None`), the entry gets **`last_updated = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`** before save.
- **`get_player_status`** returns a third value: `last_updated` or `None`.
- **`show_all`** prints a **Last Updated** column.

Reset-to-default removes the row from JSON (same as Build 1); no `last_updated` retained for that player until the next override.

---

## End-to-end flow (news → status loop)

```text
[scheduler hourly]
  poll_for_new()
    → fetch_feed()  → list[NewsItem] (full current feed)
    → filter_new()  → unseen by link; persist new links; return new_items

[Hermes / LLM]
  for item in new_items:
    classify(item.title, item.description) → player? injury/form signal?
    if actionable → Telegram notify; await user consent

  if consent and need detail:
    fetch_article(item.link)  → plain text (truncated)

  if consent to update:
    update_player(name, availability=..., form=...)
      → player_status.json row + last_updated + changelog line

[Build 1 ILP]
  data_loader reads player_status → scorer uses availability + form_multiplier
```

---

## Pseudocode (concise)

```text
function fetch_feed(url):
    xml = http_get(url)
    channel = parse_xml(xml).channel
    items = []
    for elem in channel.items:
        title, desc, link, pub = text(elem, title|description|link|pubDate)
        link = strip_cdata(link)
        if link == "":
            continue
        items.append(NewsItem(title, desc, link, pub, parsed_at=now_utc()))
    return items

function filter_new(items, state_path):
    seen = set(load_json(state_path).seen_guids)
    new = [i for i in items if i.link not in seen]
    if new:
        seen = seen ∪ { i.link for i in new }
        save_json(state_path, { "seen_guids": sorted(seen) })
    return new

function poll_for_new(url):
    try:
        return filter_new(fetch_feed(url))
    except error:
        log_stderr(error)
        return []

function fetch_article(url):
    html = http_get(url)
    text = HTMLParser_strip_nav_script(html)
    return truncate(text, 8000)

function update_player(name, ...):  # player_status
    merge fields; if row is default:
        delete key
    else:
        row.last_updated = utc_iso_z()
        save
    append changelog if fields changed
```

---

## Dependencies

- **Standard library only** for Build 2 news: `urllib.request`, `xml.etree.ElementTree`, `json`, `argparse`, `html.parser`, `html`, `re`, `pathlib`, `datetime`.

No PuLP, no third-party RSS libraries.

---

## Extension points

- **`<guid>` vs link:** if the feed ever duplicates links, switch `NewsItem.guid` to prefer `item/guid` text when present.
- **`pubDate` parsing:** currently stored as raw string; optional `email.utils.parsedate_to_datetime` for ordering or day-bucketing.
- **Article body:** replace `_TextExtractor` with readability-style heuristics or a headless browser if nav noise becomes a problem.
- **State file:** could add `last_poll_utc` or `last_item_pubdate` for observability without changing dedup semantics.
- **Hermes:** retries, backoff, and “notify only if `pubDate` is after player `last_updated`” are policy layers outside this package.
