from __future__ import annotations

from collections import defaultdict

import pulp

from .models import PlayerCandidate, Role

BUDGET = 100.0
TEAM_SIZE = 11
MAX_PER_TEAM = 7
MAX_OVERSEAS = 4

ROLE_BOUNDS: dict[Role, tuple[int, int]] = {
    Role.WK:   (1, 4),
    Role.BAT:  (3, 6),
    Role.AR:   (1, 4),
    Role.BOWL: (3, 6),
}


def select_best_xi(
    candidates: list[PlayerCandidate],
    locked_indices: list[int] | None = None,
    banned_indices: list[int] | None = None,
) -> list[PlayerCandidate] | None:

    prob = pulp.LpProblem("FantasyXI", pulp.LpMaximize)

    x = {
        i: pulp.LpVariable(f"x_{i}", cat=pulp.LpBinary)
        for i in range(len(candidates))
    }

    # --- hard-lock picked players ---
    for idx in (locked_indices or []):
        prob += x[idx] == 1, f"lock_{idx}"

    # --- hard-ban dropped players ---
    for idx in (banned_indices or []):
        prob += x[idx] == 0, f"ban_{idx}"

    # --- objective: maximize total adjusted expected value ---
    prob += pulp.lpSum(
        candidates[i].adjusted_ev * x[i] for i in x
    ), "total_adjusted_ev"

    # --- exactly 11 players ---
    prob += pulp.lpSum(x[i] for i in x) == TEAM_SIZE, "team_size"

    # --- budget ---
    prob += (
        pulp.lpSum(candidates[i].price * x[i] for i in x) <= BUDGET,
        "budget",
    )

    # --- role bounds ---
    role_indices: dict[Role, list[int]] = defaultdict(list)
    for i, p in enumerate(candidates):
        role_indices[p.role].append(i)

    for role, (lo, hi) in ROLE_BOUNDS.items():
        indices = role_indices[role]
        prob += (
            pulp.lpSum(x[i] for i in indices) >= lo,
            f"min_{role.value}",
        )
        prob += (
            pulp.lpSum(x[i] for i in indices) <= hi,
            f"max_{role.value}",
        )

    # --- max players per team ---
    team_indices: dict[str, list[int]] = defaultdict(list)
    for i, p in enumerate(candidates):
        team_indices[p.team].append(i)

    for team, indices in team_indices.items():
        prob += (
            pulp.lpSum(x[i] for i in indices) <= MAX_PER_TEAM,
            f"max_team_{team}",
        )

    # --- max overseas ---
    overseas = [i for i, p in enumerate(candidates) if p.is_overseas]
    prob += (
        pulp.lpSum(x[i] for i in overseas) <= MAX_OVERSEAS,
        "max_overseas",
    )

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if prob.status != pulp.constants.LpStatusOptimal:
        print(f"  Solver status: {pulp.LpStatus[prob.status]}")
        return None

    selected = [
        candidates[i]
        for i in x
        if pulp.value(x[i]) > 0.5
    ]

    return selected
