# BUILD 3 — Initialize player status from team previews  |  Hermes / CLI

## Purpose

Seed or refresh `data/player_status.json` using **pre-season IPL team preview pages** (e.g. a Cricbuzz hub that links to all 10 franchises). The workflow is **availability-first** for injuries, plus **predicted XI (11 or 12)** players marked **available** with **form: good**.

---

## Rules (what to extract)

| Source signal | `availability` | `form` |
|---------------|------------------|--------|
| Ruled out / season-ending / will not play | `ruled_out` | omit (default `None`) |
| Temporarily injured / doubtful / recovering / niggle | `temporarily_injured` | omit |
| Generic “injured” without clarity | `temporarily_injured` unless text clearly says ruled out | omit |
| Named in **predicted playing 11** or **12** (incl. impact subs if listed as XI) | `available` | `good` |

- **Do not** infer **form** (bad/average/excellent) from preview prose for injury-only stories — only use form for the **XI/12 initialization** rule above.
- **Do not** batch-update the whole squad; only players explicitly called out as unavailable **or** listed in the predicted XI/12.
- Player **`player`** strings must match **`squads.json` `ShortName`** exactly.

---

## Batch apply (after user confirms)

Write a JSON **array** of objects:

```json
[
  {"player": "Example Player", "availability": "temporarily_injured"},
  {"player": "Another Player", "availability": "ruled_out"},
  {"player": "XI Player One", "availability": "available", "form": "good"}
]
```

Apply from **AgentXI root**:

```bash
python -m main.player_status batch path/to/updates.json
```

Stdin:

```bash
cat updates.json | python -m main.player_status batch -
```

Each row needs **`player`** plus at least one of **`availability`** or **`form`**. Changelog lines and `last_updated` behave the same as single `update`.

---

## Single-player (unchanged)

```bash
python -m main.player_status update "Player Name" -a temporarily_injured
python -m main.player_status update "Player Name" -a available -f good
python -m main.player_status show
```

---

## User-facing summary (before writing)

When presenting results to the user, prioritize:

1. **Unavailability only:** list players with `temporarily_injured`, `ruled_out`, and (if you used it) unclear long-term injury mapped to one of those — **not** the full “available + good” XI list in the main summary (mention counts only if helpful).
2. Confirm **XI/12** count: “N players set to available + good from predicted XI.”
3. Ask for **explicit confirmation** before running `batch`.

---

## Related

- Skill (Hermes): `agentxi-team-previews` → `/agentxi-team-previews`
- Internal design: `BUILD3_SET_PLAYERS_STATUS_INTERNAL.md`
- Squad names: `data/squads.json`
