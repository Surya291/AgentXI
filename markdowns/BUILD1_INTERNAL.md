# Build 1 — Internal architecture and code flow

Reference doc for how the playing-XI selector and player-status layer are wired. Repository root = `AgentXI/`.

---

## Layout

```
main/
  player_status.py          # CLI + JSON store + form multipliers + changelog
  optimizer/
    __init__.py
    models.py               # Role enum, MatchInfo, PlayerCandidate
    data_loader.py          # Schedule, squads, metric CSVs → candidate pool
    scorer.py               # Base EV by role, form × fixture bonus, availability filter
    ilp_selector.py         # PuLP binary program, locks and bans
    run_match_ids.py        # CLI + partial-name resolution for pick/drop
data/
  ipl_2026_schedule.csv
  squads.json
  new-combined-batters.csv
  new-combined-bowlers.csv
  player_status.json        # optional overrides (only non-default rows)
  player_status_changelog.log
```

---

## Data sources

| File | Role |
|------|------|
| `ipl_2026_schedule.csv` | Map `match_ids` → home/away teams for the window. |
| `squads.json` | Per-team buckets: `WICKET KEEPER`, `BATSMAN`, `ALL ROUNDER`, `BOWLER`; player `ShortName`, `Value` (credits), `isOverseasPlayer`. |
| `new-combined-batters.csv` | `Player` → `weighted_batting_impact_per_innings`. |
| `new-combined-bowlers.csv` | `Player` → `weighted_bowling_impact_per_match`. |
| `player_status.json` | Per-player `availability` and/or `form` when not default. |

---

## `models.py`

- **`Role`:** `WK`, `BAT`, `AR`, `BOWL` — normalized from squad skill keys.
- **`MatchInfo`:** one schedule row.
- **`PlayerCandidate`:** name, team, role, price, overseas flag; optional `bat_ev` / `bowl_ev`; `base_ev`, `adjusted_ev`; `availability`, `form`, `form_multiplier`; drop metadata.

---

## `data_loader.py`

1. Load full schedule; resolve `match_ids` to `MatchInfo` list; error if a number is missing.
2. **`get_team_appearances`:** count how often each team appears in that window (for repeat-fixture weighting).
3. **`load_squads`:** flatten only teams that appear in the window into `PlayerCandidate` rows; attach metrics by exact `ShortName` ↔ CSV `Player`.
4. **`load_all_statuses`** from `player_status.py`: merge `availability`, `form`, and `get_form_multiplier(form)` onto each candidate.

---

## `player_status.py`

- **Storage:** `player_status.json` — only entries that differ from defaults (`available` + form `None`).
- **`update_player`:** validates enums; merges fields; removes key if back to default; **`_log`** appends UTC line to `player_status_changelog.log` with old→new for changed fields; `reset` logs prior state.
- **`get_form_multiplier`:** map form → float (neutral 1.0, down for bad/average, up for good/excellent).
- **`is_available`:** only `available` passes the scorer gate.

---

## `scorer.py`

1. **Availability:** if not `available`, mark dropped with reason (same list as “missing metric” style reporting in CLI).
2. **`compute_base_ev`:**  
   - `WK` / `BAT`: batting metric only.  
   - `BOWL`: bowling metric only.  
   - `AR`: `0.8*max(bat,bowl) + 0.5*min(bat,bowl)` when both exist; `0.8 * single` if one side only; else drop.
3. **`apply_fixture_bonus`:** `base_after_form * (1 + 0.05 * (appearances - 1))` per team in the match window.
4. Pipeline per surviving player: `base_ev` → multiply by `form_multiplier` → then fixture bonus → `adjusted_ev`.

---

## `ilp_selector.py` (PuLP)

- Binary `x[i]` per candidate index.
- **Objective:** maximize sum of `adjusted_ev[i] * x[i]`.
- **Constraints:** exactly 11 players; budget ≤ 100; role mins/maxes (WK 1–4, BAT 3–6, AR 1–4, BOWL 3–6); ≤7 per franchise; ≤4 overseas.
- **`locked_indices`:** `x[i] == 1` (hard picks from CLI).
- **`banned_indices`:** `x[i] == 0` (hard drops). Overlap pick+drop: runner removes lock if name is in both (drop wins).

Solver: `PULP_CBC_CMD`; optimal status required or return `None`.

---

## `run_match_ids.py`

1. `build_candidate_pool(match_ids)` → `usable = score_and_filter(...)`.
2. **`_match_partial`:** lowercase substring on `PlayerCandidate.name`.
3. **`resolve_picks` / `resolve_drops`:** for each query string, 0 matches → skip; 1 match → lock/ban that index; many → print all, choose index with max `adjusted_ev`, log auto-selection.
4. `select_best_xi(usable, locked_indices, banned_indices)`.
5. **`print_result`:** sorted by role order; Lock column for picked names.

**Programmatic:** `run(match_ids, pick_queries=None, drop_queries=None)` returns selected list or `None`.

---

## End-to-end flow (XI)

```text
match_ids
  → schedule → eligible teams + appearance counts
  → squads + CSV metrics + player_status.json
  → scorer (filter + base_ev + form × fixture → adjusted_ev)
  → optional pick/drop → index locks/bans
  → PuLP → 11 players
```

---

## Dependencies

- **PuLP** (CBC) for the ILP.
- Standard library: `json`, `csv`, `argparse`, `pathlib`, `datetime` (changelog).

---

## Extension points (if you evolve Build 1)

- Captain/VC not modeled in the ILP yet.
- Name matching for status CLI is exact player string; XI CLI uses partial match.
- Changelog is append-only text; `player_status.json` is the source of truth for runtime reads.
