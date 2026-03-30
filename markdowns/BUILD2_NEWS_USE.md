# BUILD 2 — News Feed  |  Hermes Skill Reference

## What this does
Polls the CricTracker IPL RSS feed every hour, surfaces new articles, and lets you fetch the full content of any article.  Combined with `player_status`, this closes the loop: news → relevance check → update player form/availability → better ILP picks.

---

## Commands

### 1. Poll for new articles
```
python -m main.news poll
```
Returns only articles published since the last poll.  State is persisted; running it twice in a row will return nothing the second time.

**Output:** One block per new article — `pubDate`, `title`, `description` (first 200 chars), `link`.

---

### 2. Fetch full article text
```
python -m main.news fetch <url>
```
Strips HTML, returns plain text (max ~8 000 chars, truncated if longer).

| Arg | Description |
|-----|-------------|
| `url` | Full article URL (e.g. from a poll result) |

---

### 3. See recent feed (no state update)
```
python -m main.news latest [-n N]
python -m main.news latest-json [-n N]   # machine-readable
```
Fetches live feed and prints the N most recent items.  Does **not** mark items as seen.

| Arg | Default | Description |
|-----|---------|-------------|
| `-n` | 5 | Number of items to show |

---

### 4. Reset seen-state
```
python -m main.news reset-state
```
Wipes the dedup state so the next `poll` returns everything currently in the feed.  Useful after a gap in polling.

---

## Hermes hourly loop (intended flow)

```
1. python -m main.news poll
      → new_items (list of title + description + link)

2. [Hermes LLM] For each item:
      - Does title/description mention a specific player?
      - Does it suggest form change (injury, poor run, great form)?
      - If yes → notify user on Telegram with title + description

3. [User replies on Telegram] "yes update" / "no skip"

4. If yes:
      - Optionally fetch full text: python -m main.news fetch <link>
      - python -m main.player_status update "<Player Name>" --availability <val> --form <val>

5. [Next ILP run picks up the updated status automatically]
```

The `last_updated` field in `player_status.json` timestamps every change so Hermes can always tell how fresh its information is.

---

## Files touched

| Path | Role |
|------|------|
| `main/news/__init__.py` | Public API (`fetch_feed`, `poll_for_new`, `fetch_article`) |
| `main/news/rss_client.py` | RSS fetch + XML parse |
| `main/news/article_fetch.py` | HTML → plain text extractor |
| `main/news/state.py` | Seen-guid persistence (`data/rss_feed_state.json`) |
| `main/news/poll.py` | One-shot new-items diff |
| `main/news/cli.py` | CLI entry point |
| `data/rss_feed_state.json` | Persisted set of seen article links |
| `main/player_status.py` | Updated: now writes `last_updated` (UTC ISO) on every change |
