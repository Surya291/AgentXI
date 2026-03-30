# Build 3 — Team previews → player_status: internal notes

Reference for initializing `player_status.json` from external preview sites and the **batch** CLI. Repository root = `AgentXI/`.

---

## Layout

```
main/
  player_status.py       # update, batch, bulk_update(), load_batch_json()
data/
  player_status.json     # overlay; only non-default rows persisted
  player_status_changelog.log
markdowns/
  BUILD3_SET_PLAYERS_STATUS_USE.md
  BUILD3_SET_PLAYERS_STATUS_INTERNAL.md
.hermes_agent11/skills/agentxi/
  agentxi-team-previews/SKILL.md
```

---

## Batch CLI

- **Command:** `python -m main.player_status batch <json_file|->`
- **Input:** JSON array of objects. Required: `player` (string). At least one of `availability` or `form` must be present or the row is skipped with a message.
- **Implementation:** `load_batch_json()` reads file or stdin (`-`); `json.loads`; must be `list`. `bulk_update()` iterates and calls `update_player()` per row (same merge, default-row removal, `last_updated`, changelog as single updates).
- **Return:** prints `applied` / `skipped` counts.

---

## Merge semantics (unchanged from Build 1)

- `update_player` merges onto any existing row; omitted fields in a **single** update are not passed as `None` from CLI — for batch JSON, omitted keys mean “do not pass to `update_player`” only if we use `.get()` — **current behavior:** if JSON omits `form`, `form` is `None` in Python and `update_player(..., form=None)` does **not** change form. Same for `availability`.
- To change only availability, send `{"player": "X", "availability": "ruled_out"}`.

---

## Preview workflow (agent-side, not code)

1. User supplies **hub URL** (index of team previews).
2. Agent discovers **10 team** article URLs (IPL franchises).
3. For each page: extract **injury / unavailability** narrative → map to `ruled_out` or `temporarily_injured` only (no form from this path).
4. Extract **predicted playing 11** and **12** (if site lists 12) → each name → `available` + `form: good`.
5. Normalize names against `squads.json` `ShortName`; unresolved names must be flagged to the user, not guessed.
6. Present **summary** (unavailable players detailed; XI summarized by count).
7. On confirmation: write JSON file → `player_status batch`.

---

## Pseudocode

```text
previews = [fetch(url) for url in ten_team_urls_from_hub(hub_url)]
injury_rows = []
xi_rows = []
for page in previews:
    for player in parse_injured_or_ruled_out(page):
        injury_rows.append({player, availability: map_injury(player.context)})
    for player in parse_predicted_xi_11_or_12(page):
        xi_rows.append({player, availability: available, form: good})

dedupe by player name (last write wins or merge policy — prefer stricter availability)
present summary(injury_rows)  # only unavailable in main narrative
confirm user
batch_write_json(injury_rows + xi_rows)
shell: python -m main.player_status batch updates.json
```

---

## ILP interaction

Same as Build 1: `data_loader` reads `player_status.json`; `scorer` excludes non-`available` and applies `form_multiplier`. **Good** form → 1.10× on EV.

---

## Extension points

- **Idempotent re-run:** batch overwrites per-player merge state; to fully reset, use `reset` per player or script clearing `player_status.json`.
- **Hub-specific parsers:** keep parsing logic in the agent / Hermes; Python layer stays JSON + `batch` only unless you add a dedicated fetcher module later.
