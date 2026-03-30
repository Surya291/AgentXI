from __future__ import annotations

from collections import Counter

from .models import PlayerCandidate, Role
from ..player_status import is_available

REPEAT_FIXTURE_BONUS_PER_EXTRA = 0.05


def compute_base_ev(player: PlayerCandidate) -> float | None:
    bat = player.bat_ev
    bowl = player.bowl_ev

    if player.role in (Role.BAT, Role.WK):
        return bat

    if player.role == Role.BOWL:
        return bowl

    if player.role == Role.AR:
        if bat is not None and bowl is not None:
            mx = max(bat, bowl)
            mn = min(bat, bowl)
            return 0.8 * mx + 0.5 * mn
        if bat is not None:
            return 0.8 * bat
        if bowl is not None:
            return 0.8 * bowl
        return None

    return None


def apply_fixture_bonus(
    base_ev: float, team: str, team_appearances: Counter[str]
) -> float:
    appearances = team_appearances.get(team, 1)
    bonus = REPEAT_FIXTURE_BONUS_PER_EXTRA * (appearances - 1)
    return base_ev * (1.0 + bonus)


def score_and_filter(
    candidates: list[PlayerCandidate],
    team_appearances: Counter[str],
) -> list[PlayerCandidate]:
    usable: list[PlayerCandidate] = []
    dropped: list[PlayerCandidate] = []

    for p in candidates:
        if not is_available(p.availability):
            p.dropped = True
            p.drop_reason = f"unavailable ({p.availability})"
            dropped.append(p)
            continue

        ev = compute_base_ev(p)
        if ev is None:
            p.dropped = True
            p.drop_reason = f"missing metric for role {p.role.value}"
            dropped.append(p)
            continue

        p.base_ev = ev
        after_form = ev * p.form_multiplier
        p.adjusted_ev = apply_fixture_bonus(after_form, p.team, team_appearances)
        usable.append(p)

    if dropped:
        print(f"\n  Dropped {len(dropped)} players:")
        for d in dropped[:15]:
            print(f"    - {d.name:25s} | {d.team:4s} | {d.role.value:4s} | {d.drop_reason}")
        if len(dropped) > 15:
            print(f"    ... and {len(dropped) - 15} more")

    return usable
