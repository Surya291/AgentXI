#!/usr/bin/env python3
"""CLI entry point: pass a list of match IDs and get the best fantasy XI."""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from .data_loader import build_candidate_pool
from .ilp_selector import select_best_xi
from .models import PlayerCandidate, MatchInfo, Role
from .scorer import score_and_filter


# --------------- name matching ---------------

def _match_partial(
    query: str,
    usable: list[PlayerCandidate],
) -> list[tuple[int, PlayerCandidate]]:
    q = query.strip().lower()
    return [(i, p) for i, p in enumerate(usable) if q in p.name.lower()]


def resolve_picks(
    queries: list[str],
    usable: list[PlayerCandidate],
) -> list[int]:
    """Match partial name queries against the usable pool. Returns indices to lock."""
    locked: list[int] = []

    for query in queries:
        matches = _match_partial(query, usable)

        if not matches:
            print(f"  [pick] No match for '{query}' in the usable pool -- skipping.")
            continue

        if len(matches) == 1:
            idx, p = matches[0]
            print(f"  [pick] '{query}' -> {p.name} ({p.team}, {p.role.value}, {p.price}cr)")
            locked.append(idx)
            continue

        print(f"  [pick] '{query}' matched {len(matches)} players:")
        best_idx, best_p = max(matches, key=lambda t: t[1].adjusted_ev)
        for i, p in matches:
            marker = "  <-- selected" if i == best_idx else ""
            print(f"         {p.name:<25s}  {p.team:4s}  {p.role.value:4s}  {p.adjusted_ev:7.2f}{marker}")
        print(f"  [pick] Auto-selected: {best_p.name} (highest adjusted EV)")
        locked.append(best_idx)

    return locked


def resolve_drops(
    queries: list[str],
    usable: list[PlayerCandidate],
) -> list[int]:
    """Match partial name queries against the usable pool. Returns indices to ban."""
    banned: list[int] = []

    for query in queries:
        matches = _match_partial(query, usable)

        if not matches:
            print(f"  [drop] No match for '{query}' in the usable pool -- skipping.")
            continue

        if len(matches) == 1:
            idx, p = matches[0]
            print(f"  [drop] '{query}' -> {p.name} ({p.team}, {p.role.value}, {p.price}cr)")
            banned.append(idx)
            continue

        print(f"  [drop] '{query}' matched {len(matches)} players:")
        best_idx, best_p = max(matches, key=lambda t: t[1].adjusted_ev)
        for i, p in matches:
            marker = "  <-- selected" if i == best_idx else ""
            print(f"         {p.name:<25s}  {p.team:4s}  {p.role.value:4s}  {p.adjusted_ev:7.2f}{marker}")
        print(f"  [drop] Auto-selected: {best_p.name} (highest adjusted EV)")
        banned.append(best_idx)

    return banned


# --------------- display helpers ---------------

def print_header(
    match_ids: list[int],
    matches: list[MatchInfo],
    team_appearances: Counter[str],
    n_candidates: int,
    n_usable: int,
) -> None:
    print("=" * 70)
    print("  AGENT XI  -  ILP FANTASY XI SELECTOR")
    print("=" * 70)

    print(f"\n  Match IDs : {match_ids}")
    print(f"  Fixtures  :")
    for m in matches:
        print(f"    #{m.match_no:2d}  {m.date:>10s}  {m.home_team} vs {m.away_team}  ({m.venue})")

    print(f"\n  Eligible teams & appearances:")
    for team, count in sorted(team_appearances.items(), key=lambda t: -t[1]):
        marker = " **" if count > 1 else ""
        print(f"    {team:4s} : {count}{marker}")

    print(f"\n  Candidates from squads : {n_candidates}")
    print(f"  Usable after filtering : {n_usable}")


def print_result(
    selected: list[PlayerCandidate],
    locked_names: set[str] | None = None,
) -> None:
    total_price = sum(p.price for p in selected)
    total_ev = sum(p.adjusted_ev for p in selected)
    overseas_count = sum(1 for p in selected if p.is_overseas)
    locked_names = locked_names or set()

    role_counts: Counter[str] = Counter(p.role.value for p in selected)

    print("\n" + "=" * 70)
    print("  OPTIMISED XI")
    print("=" * 70)

    header = f"  {'#':>2s}  {'Player':<25s}  {'Team':4s}  {'Role':4s}  {'Price':>5s}  {'BaseEV':>7s}  {'AdjEV':>7s}  {'OS':>2s}  {'Form':<9s}  {'Lock':<4s}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    sorted_xi = sorted(selected, key=lambda p: _role_order(p.role))
    for idx, p in enumerate(sorted_xi, 1):
        os_flag = "Y" if p.is_overseas else ""
        form_str = p.form if p.form else "-"
        lock_str = "Y" if p.name in locked_names else ""
        print(
            f"  {idx:2d}  {p.name:<25s}  {p.team:4s}  {p.role.value:4s}"
            f"  {p.price:5.1f}  {p.base_ev:7.2f}  {p.adjusted_ev:7.2f}  {os_flag:>2s}  {form_str:<9s}  {lock_str:<4s}"
        )

    print("  " + "-" * (len(header) - 2))
    print(f"  {'':2s}  {'TOTAL':<25s}  {'':4s}  {'':4s}  {total_price:5.1f}  {'':7s}  {total_ev:7.2f}")

    print(f"\n  Role breakdown : {dict(role_counts)}")
    print(f"  Budget used    : {total_price:.1f} / 100.0")
    print(f"  Overseas       : {overseas_count} / 4")
    print(f"  Objective      : {total_ev:.2f}")
    if locked_names:
        print(f"  Locked picks   : {', '.join(sorted(locked_names))}")
    print()


def _role_order(role: Role) -> int:
    return {Role.WK: 0, Role.BAT: 1, Role.AR: 2, Role.BOWL: 3}[role]


# --------------- main entry ---------------

def run(
    match_ids: list[int],
    pick_queries: list[str] | None = None,
    drop_queries: list[str] | None = None,
) -> list[PlayerCandidate] | None:
    candidates, matches, team_appearances = build_candidate_pool(match_ids)

    n_candidates = len(candidates)
    usable = score_and_filter(candidates, team_appearances)
    n_usable = len(usable)

    print_header(match_ids, matches, team_appearances, n_candidates, n_usable)

    locked_indices: list[int] = []
    locked_names: set[str] = set()
    banned_indices: list[int] = []
    banned_names: set[str] = set()

    if pick_queries:
        print()
        locked_indices = resolve_picks(pick_queries, usable)
        locked_names = {usable[i].name for i in locked_indices}
        if locked_indices:
            print(f"\n  Locking {len(locked_indices)} player(s) into the XI.")

    if drop_queries:
        print()
        banned_indices = resolve_drops(drop_queries, usable)
        banned_names = {usable[i].name for i in banned_indices}
        if banned_indices:
            print(f"\n  Banning {len(banned_indices)} player(s) from the XI.")

    overlap = locked_names & banned_names
    if overlap:
        print(f"\n  WARNING: {overlap} appear in both --pick and --drop. Drop wins.")
        locked_indices = [i for i in locked_indices if usable[i].name not in overlap]
        locked_names -= overlap

    selected = select_best_xi(
        usable,
        locked_indices=locked_indices,
        banned_indices=banned_indices,
    )
    if selected is None:
        print("\n  No feasible solution found.\n")
        return None

    print_result(selected, locked_names=locked_names)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Select best fantasy XI for given match IDs")
    parser.add_argument(
        "match_ids",
        nargs="+",
        type=int,
        help="One or more match numbers from the IPL schedule",
    )
    parser.add_argument(
        "--pick", "-p",
        nargs="+",
        default=None,
        metavar="NAME",
        help="Partial player names to hard-lock into the XI (e.g. 'virat' 'bumrah')",
    )
    parser.add_argument(
        "--drop", "-d",
        nargs="+",
        default=None,
        metavar="NAME",
        help="Partial player names to exclude from the XI (e.g. 'unadkat' 'pandey')",
    )
    args = parser.parse_args()
    result = run(args.match_ids, pick_queries=args.pick, drop_queries=args.drop)
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
