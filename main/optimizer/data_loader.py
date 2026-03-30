from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Optional

from .models import MatchInfo, PlayerCandidate, Role, SQUAD_ROLE_MAP
from ..player_status import (
    load_all_statuses,
    get_form_multiplier,
    DEFAULT_AVAILABILITY,
    DEFAULT_FORM,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

SCHEDULE_PATH = DATA_DIR / "ipl_2026_schedule.csv"
SQUADS_PATH = DATA_DIR / "squads.json"
BATTERS_PATH = DATA_DIR / "new-combined-batters.csv"
BOWLERS_PATH = DATA_DIR / "new-combined-bowlers.csv"


def load_schedule(path: Path = SCHEDULE_PATH) -> list[MatchInfo]:
    matches: list[MatchInfo] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            matches.append(
                MatchInfo(
                    match_no=int(row["Match No"]),
                    date=row["Date"].strip(),
                    home_team=row["Home Team"].strip(),
                    away_team=row["Away Team"].strip(),
                    venue=row["Venue (City)"].strip(),
                )
            )
    return matches


def resolve_matches(
    schedule: list[MatchInfo], match_ids: list[int]
) -> list[MatchInfo]:
    by_no = {m.match_no: m for m in schedule}
    resolved = []
    for mid in match_ids:
        if mid not in by_no:
            raise ValueError(f"Match #{mid} not found in schedule")
        resolved.append(by_no[mid])
    return resolved


def get_team_appearances(matches: list[MatchInfo]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for m in matches:
        counts[m.home_team] += 1
        counts[m.away_team] += 1
    return counts


def load_squads(
    eligible_teams: set[str], path: Path = SQUADS_PATH
) -> list[PlayerCandidate]:
    with path.open(encoding="utf-8") as f:
        squads: dict = json.load(f)

    candidates: list[PlayerCandidate] = []
    for team, roles in squads.items():
        if team not in eligible_teams:
            continue
        for role_name, players in roles.items():
            role = SQUAD_ROLE_MAP.get(role_name)
            if role is None:
                continue
            for p in players:
                candidates.append(
                    PlayerCandidate(
                        name=p["ShortName"],
                        team=team,
                        role=role,
                        price=float(p["Value"]),
                        is_overseas=bool(p.get("isOverseasPlayer", False)),
                    )
                )
    return candidates


def _load_metric_csv(
    path: Path, value_column: str
) -> dict[str, float]:
    lookup: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["Player"].strip()
            raw = row[value_column].strip()
            if not raw:
                continue
            try:
                val = float(raw)
            except ValueError:
                continue
            lookup[name] = val
    return lookup


def load_batting_metrics(path: Path = BATTERS_PATH) -> dict[str, float]:
    return _load_metric_csv(path, "weighted_batting_impact_per_innings")


def load_bowling_metrics(path: Path = BOWLERS_PATH) -> dict[str, float]:
    return _load_metric_csv(path, "weighted_bowling_impact_per_match")


def build_candidate_pool(
    match_ids: list[int],
) -> tuple[list[PlayerCandidate], list[MatchInfo], Counter[str]]:
    schedule = load_schedule()
    matches = resolve_matches(schedule, match_ids)
    team_appearances = get_team_appearances(matches)
    eligible_teams = set(team_appearances.keys())

    candidates = load_squads(eligible_teams)
    bat_lookup = load_batting_metrics()
    bowl_lookup = load_bowling_metrics()

    statuses = load_all_statuses()

    for p in candidates:
        p.bat_ev = bat_lookup.get(p.name)
        p.bowl_ev = bowl_lookup.get(p.name)

        entry = statuses.get(p.name, {})
        p.availability = entry.get("availability", DEFAULT_AVAILABILITY)
        p.form = entry.get("form", DEFAULT_FORM)
        p.form_multiplier = get_form_multiplier(p.form)

    return candidates, matches, team_appearances
