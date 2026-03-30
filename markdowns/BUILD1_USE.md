# Build 1 — How to use the tools

Run all commands from the **AgentXI project root** (the folder that contains `main/` and `data/`). Use the project Python environment if you have one (for example `agent_venv/bin/python`).

---

## 1. Get a playing XI

**Module:** `main.optimizer.run_match_ids`

**What it does:** Prints a suggested 11 for the matches you choose, using the IPL schedule and squad data already in the repo.

### Required arguments

| Argument | Type | Meaning |
|----------|------|---------|
| `match_ids` | one or more integers | Match numbers from the schedule (e.g. `1` for match 1, `2` for match 2). |

### Optional flags

| Flag | Short | Meaning |
|------|-------|---------|
| `--pick` | `-p` | One or more **partial player names** to **force into** the XI. Matching is case-insensitive substring on the full name (e.g. `virat` → Virat Kohli). If several players match one string, the tool picks one and prints which one so you can confirm. |
| `--drop` | `-d` | One or more **partial player names** to **exclude** from the XI. Same matching rules as `--pick`. |

### Example commands

```bash
python -m main.optimizer.run_match_ids 1 2
python -m main.optimizer.run_match_ids 1 2 -p virat bumrah
python -m main.optimizer.run_match_ids 1 2 -d unadkat thushara
python -m main.optimizer.run_match_ids 1 2 -p kohli -d salt
```

### What you get back

- Text output: fixtures used, summary counts, then a table of 11 players with team, role, price, and a few numeric columns, plus totals and a short summary line at the bottom.
- Exit code `0` if a team was produced; non-zero if it could not produce a valid XI.

---

## 2. Update player status (availability and form)

**Module:** `main.player_status`

**What it does:** Records news-style signals per player. Future XI runs **read** this store so picks reflect what you set.

### Subcommands

#### `update`

| Argument / flag | Required? | Meaning |
|-----------------|-----------|---------|
| `player` | yes | Full player name as stored in squads (same spelling as `ShortName`). |
| `--availability` / `-a` | no* | One of: `available`, `benched`, `temporarily_injured`, `ruled_out`. |
| `--form` / `-f` | no* | One of: `bad`, `average`, `good`, `excellent`. |

\*At least one of `-a` or `-f` must be passed.

**Defaults if you never set anything:** availability = `available`, form = unset (neutral).

#### `reset`

| Argument | Meaning |
|----------|---------|
| `player` | Clears overrides for that player back to defaults. |

#### `show`

No arguments. Lists every player that still has a non-default status.

#### `log`

| Flag | Meaning |
|------|---------|
| `-n` | How many **latest** log lines to print (default `20`). |

### Example commands

```bash
python -m main.player_status update "Virat Kohli" -f excellent
python -m main.player_status update "Pat Cummins" -a ruled_out
python -m main.player_status update "Jasprit Bumrah" -a available -f good
python -m main.player_status reset "Pat Cummins"
python -m main.player_status show
python -m main.player_status log
python -m main.player_status log -n 50
```

### What you get back

- Short confirmation lines on `update` / `reset`.
- Tables or log lines on `show` / `log`.

---

## Order of operations (for the agent)

1. Use **player status** when the user has news (injury, benching, form).
2. Use **run_match_ids** when the user wants an XI for specific match numbers, optionally with forced picks or bans.
