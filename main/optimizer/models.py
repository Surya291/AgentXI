from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class Role(enum.Enum):
    WK = "WK"
    BAT = "BAT"
    AR = "AR"
    BOWL = "BOWL"


SQUAD_ROLE_MAP: dict[str, Role] = {
    "WICKET KEEPER": Role.WK,
    "BATSMAN": Role.BAT,
    "ALL ROUNDER": Role.AR,
    "BOWLER": Role.BOWL,
}


@dataclass
class MatchInfo:
    match_no: int
    date: str
    home_team: str
    away_team: str
    venue: str

    def teams(self) -> tuple[str, str]:
        return (self.home_team, self.away_team)


@dataclass
class PlayerCandidate:
    name: str
    team: str
    role: Role
    price: float
    is_overseas: bool

    bat_ev: Optional[float] = None
    bowl_ev: Optional[float] = None

    base_ev: float = 0.0
    adjusted_ev: float = 0.0

    availability: str = "available"
    form: Optional[str] = None
    form_multiplier: float = 1.0

    dropped: bool = False
    drop_reason: str = ""
