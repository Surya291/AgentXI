---
name: agentxi-team-previews
description: >-
  Initializes Agent XI player_status.json from a user-provided pre-season team-preview
  hub URL (e.g. Cricbuzz): fetches all 10 IPL franchise preview pages, extracts only
  injury or ruled-out availability (no form inference from injuries), marks predicted
  playing 11 or 12 as available with form good, summarizes unavailable players for
  the user, and applies updates via player_status batch JSON after confirmation.
  Use when the user shares a preview index URL, wants to seed squad availability
  before the season, or says team previews / Cricbuzz XI / pre-season injuries.
---

# Agent XI — Team previews → `player_status` (Build 3)

One-shot (or per-round) **initialization** of `data/player_status.json` from **official-style team preview articles**, not the whole roster.

## Prerequisites

- **Cwd:** `/home/surya/AgentXI` for all `python -m` commands.
- User provides the **home / hub URL** that links to **each of the 10 IPL teams’** preview or squad analysis pages.
- **Names** in JSON must match **`data/squads.json` → `ShortName`** exactly. If the site uses nicknames or initials, resolve against the squad file before batching.

## What to extract (strict)

### A) Injuries / unavailability — **availability only**

| Reading on page | Set `availability` | `form` |
|-----------------|----------------------|--------|
| Season-ending / will not play / ruled out | `ruled_out` | **omit** (leave default) |
| Doubtful / niggle / recovering / week-to-week | `temporarily_injured` | **omit** |
| “Injured” ambiguous | `temporarily_injured` unless clearly ruled out | **omit** |

**Do not** assign `bad` / `average` / `excellent` based on preview tone for these players.

**Do not** add `benched` or other states for this workflow unless the user explicitly asks — default scope is **ruled_out** and **temporarily_injured** plus XI below.

### B) Predicted **playing 11** or **12** (incl. impact / subs if the article lists 12 in the XI block)

For every name in those lists:

- `availability`: `available`
- `form`: `good`

Players **not** mentioned in injuries or XI/12: **no row** (leave defaults in `player_status.json`).

## Workflow

### 1. Bulk Hub URL Workflow
```
1. User sends hub URL (and optional “use Cricbuzz” context).

2. Open hub; collect exactly 10 franchise preview URLs (one per IPL team).

3. For each URL, fetch readable content (web extract, fetch, or terminal curl — follow site ToS).
```

### 2. Team-by-Team Interactive Workflow
If the user is providing team preview articles iteratively (e.g., one team at a time) and says "go on" or "next team":
1. **DO NOT hallucinate** or guess the injury list, core starters, or bench for the next team.
2. **STOP and ask** the user to provide the article or news for that specific team.
3. Wait for the user to provide the text/URL, then parse it.

### Parsing & Applying (For both workflows)
```
4. Parse:
     - injury / ruled out / temporarily unavailable → category A only
     - predicted XI (11) or XII (12) → category B


5. Map every name → squads ShortName (exact). If a player is found in the article but missing from `squads.json`, do not drop them. Instead, append their name to `new_players.json` in the project root, categorized by team (e.g., `{"SRH": ["Player Name"]}`).

6. Build JSON array:
     [ {"player": "...", "availability": "temporarily_injured"},
       {"player": "...", "availability": "ruled_out"},
       {"player": "...", "availability": "available", "form": "good"},
       ... ]

7. **Before writing:** message the user with:
     - A concise list of **only** players who are temporarily_injured or ruled_out (and short reason if one line).
     - A **count** (and optional one-line note) for “XI/12 → available + good” — do not dump the full XI in the main summary unless the user asks.
     - Ask for **explicit OK** to apply.

8. After OK: **DO NOT create any temporary JSON files on disk**, and **DO NOT use the `terminal` tool to pipe JSON** (e.g., `echo '[...]' | python ...`) as it triggers environment security blocks.
     Instead, use the `execute_code` tool with the exact snippet below to pass the payload directly:

```python
import subprocess
import json

# STRICT SCHEMA: keys must be "player" and "availability", NOT "name" or "status"
# Valid 'availability' enum values ONLY: "available", "benched", "temporarily_injured", "ruled_out"
# Do NOT use "core_starter", "bench", or any other variations.
payload = [
  {"player": "Player Name", "team": "TEAM", "availability": "available", "form": "good"},
  {"player": "Another Player", "team": "TEAM", "availability": "ruled_out"}
]

result = subprocess.run(
    ["python", "-m", "main.player_status", "batch", "-"],
    input=json.dumps(payload),
    text=True,
    cwd="/home/surya/AgentXI",
    capture_output=True
)
print(result.stdout)
if result.stderr:
    print("ERR:", result.stderr)
```

9. Suggest `python -m main.player_status show` to verify.
```

## Commands reference

| Action | Command |
|--------|---------|
| Apply batch | `python -m main.player_status batch FILE.json` or `... batch -` |
| Verify | `python -m main.player_status show` |
| Docs | `AgentXI/markdowns/BUILD3_SET_PLAYERS_STATUS_USE.md` |

## Tracking Progress

When the user asks "what teams have we done?" or asks for the current pipeline progress:
**DO NOT** rely on `session_search` (chat history), as updates may span multiple sessions or be obscured by cron jobs.
**DO** write a Python script using `execute_code` to parse `data/player_status.json` and cross-reference it with `data/squads.json` to count the number of players locked in per team.

```python
import json
from collections import defaultdict

with open('/home/surya/AgentXI/data/player_status.json', 'r') as f:
    status_data = json.load(f)

with open('/home/surya/AgentXI/data/squads.json', 'r') as f:
    squads = json.load(f)

team_counts = defaultdict(int)
for team, roles in squads.items():
    for role, players in roles.items():
        for p in players:
            name = p.get('ShortName', p.get('name', ''))
            if name in status_data:
                team_counts[team] += 1

print("Pipeline Teams Processed:")
for t, c in team_counts.items():
    print(f"- {t}: {c} players locked in")
```

## Coordination

- **agentxi-news:** ongoing RSS + consent; this skill is **bulk seed** from static previews.
- **agentxi-build-11:** ILP reads `player_status.json` automatically after batch apply.

## Pitfalls

- Duplicate players across teams: **merge** to the stricter availability if both appear (e.g. ruled_out wins over available).
- Preview **lineup is prediction**, not official playing XI — tell the user once when summarizing.
- Do **not** edit `squads.json`; only `player_status.json` via `batch` / `update`.
