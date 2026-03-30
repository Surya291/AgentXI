#!/usr/bin/env python3
"""
Persistent player status store (news / form overlay).

Tracks two signals per player:
  - availability: ruled_out | temporarily_injured | benched | available (default)
  - form:         bad | average | good | excellent | None (default)

IMPORTANT
---------
- Updates are written to data/player_status.json only.
- data/squads.json is NEVER modified here. Squads are the official roster snapshot
  (names, prices, overseas flag). Availability and form are ephemeral and live in the
  overlay file so you do not churn git on squads.json every time news changes.

Where the ILP uses this
-----------------------
- main/optimizer/data_loader.py loads player_status.json and sets each
  PlayerCandidate's availability, form, and form_multiplier.
- main/optimizer/scorer.py drops non-available players and multiplies EV by form
  before the fixture bonus; that adjusted_ev is what PuLP optimizes.

Only non-default rows are kept in player_status.json.

Batch apply
-----------
``python -m main.player_status batch FILE.json`` (or ``batch -`` for stdin) applies
many rows; each object needs ``player`` plus ``availability`` and/or ``form``.
See markdowns/BUILD3_SET_PLAYERS_STATUS_USE.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
STATUS_PATH = DATA_DIR / "player_status.json"
LOG_PATH = DATA_DIR / "player_status_changelog.log"


class Availability(str, Enum):
    AVAILABLE = "available"
    BENCHED = "benched"
    TEMPORARILY_INJURED = "temporarily_injured"
    RULED_OUT = "ruled_out"


class Form(str, Enum):
    BAD = "bad"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


FORM_MULTIPLIER: dict[Optional[str], float] = {
    None:               1.00,
    Form.BAD.value:     0.75,
    Form.AVERAGE.value: 0.90,
    Form.GOOD.value:    1.10,
    Form.EXCELLENT.value: 1.25,
}

DEFAULT_AVAILABILITY = Availability.AVAILABLE.value
DEFAULT_FORM: Optional[str] = None


def _load_raw(path: Path = STATUS_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _save_raw(data: dict[str, dict], path: Path = STATUS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _log(message: str, path: Path = LOG_PATH) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}]  {message}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def load_all_statuses(
    path: Path = STATUS_PATH,
) -> dict[str, dict[str, Optional[str]]]:
    return _load_raw(path)


def get_player_status(
    name: str, path: Path = STATUS_PATH
) -> tuple[str, Optional[str], Optional[str]]:
    """Returns (availability, form, last_updated_utc_iso)."""
    data = _load_raw(path)
    entry = data.get(name, {})
    return (
        entry.get("availability", DEFAULT_AVAILABILITY),
        entry.get("form", DEFAULT_FORM),
        entry.get("last_updated", None),
    )


def update_player(
    name: str,
    availability: Optional[str] = None,
    form: Optional[str] = None,
    path: Path = STATUS_PATH,
) -> None:
    data = _load_raw(path)
    old_entry = data.get(name, {})
    old_avail = old_entry.get("availability", DEFAULT_AVAILABILITY)
    old_form = old_entry.get("form", DEFAULT_FORM)

    entry = dict(old_entry)

    if availability is not None:
        Availability(availability)
        entry["availability"] = availability

    if form is not None:
        Form(form)
        entry["form"] = form

    is_default = (
        entry.get("availability", DEFAULT_AVAILABILITY) == DEFAULT_AVAILABILITY
        and entry.get("form", DEFAULT_FORM) == DEFAULT_FORM
    )
    if is_default and name in data:
        del data[name]
    elif not is_default:
        entry["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data[name] = entry

    _save_raw(data, path)

    new_avail = entry.get("availability", DEFAULT_AVAILABILITY)
    new_form = entry.get("form", DEFAULT_FORM)

    parts: list[str] = []
    if availability is not None and old_avail != new_avail:
        parts.append(f"availability: {old_avail} -> {new_avail}")
    if form is not None and old_form != new_form:
        parts.append(f"form: {old_form} -> {new_form}")

    if parts:
        _log(f"UPDATE  {name:30s}  {' | '.join(parts)}")
    else:
        _log(f"UPDATE  {name:30s}  (no change)")

    print(f"  Updated: {name} -> availability={new_avail}, form={new_form}")


def reset_player(name: str, path: Path = STATUS_PATH) -> None:
    data = _load_raw(path)
    if name in data:
        old = data.pop(name)
        _save_raw(data, path)
        old_avail = old.get("availability", DEFAULT_AVAILABILITY)
        old_form = old.get("form", DEFAULT_FORM)
        _log(f"RESET   {name:30s}  was availability={old_avail}, form={old_form}")
        print(f"  Reset: {name} -> defaults (available, form=None)")
    else:
        print(f"  {name} already at defaults.")


def show_all(path: Path = STATUS_PATH) -> None:
    data = _load_raw(path)
    if not data:
        print("  No status overrides. All players at defaults (available, form=None).")
        return

    print(f"  {'Player':<30s}  {'Availability':<22s}  {'Form':<10s}  {'Last Updated'}")
    print("  " + "-" * 85)
    for name, entry in sorted(data.items()):
        avail = entry.get("availability", DEFAULT_AVAILABILITY)
        form = entry.get("form", DEFAULT_FORM) or "-"
        last_updated = entry.get("last_updated", "-")
        print(f"  {name:<30s}  {avail:<22s}  {form:<10s}  {last_updated}")


def get_form_multiplier(form_value: Optional[str]) -> float:
    return FORM_MULTIPLIER.get(form_value, 1.0)


def is_available(availability_value: str) -> bool:
    return availability_value == Availability.AVAILABLE.value


# --------------- CLI ---------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage player availability and form status"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_update = sub.add_parser("update", help="Update a player's status")
    p_update.add_argument("player", help="Player name (as in squads.json ShortName)")
    p_update.add_argument(
        "--availability", "-a",
        choices=[a.value for a in Availability],
        help="Set availability status",
    )
    p_update.add_argument(
        "--form", "-f",
        choices=[f.value for f in Form],
        help="Set form level",
    )

    p_reset = sub.add_parser("reset", help="Reset a player to defaults")
    p_reset.add_argument("player", help="Player name")

    sub.add_parser("show", help="Show all non-default player statuses")

    p_log = sub.add_parser("log", help="Print the status changelog")
    p_log.add_argument(
        "-n", type=int, default=20,
        help="Number of most recent entries to show (default 20)",
    )

    p_batch = sub.add_parser(
        "batch",
        help="Apply many updates from JSON (array of {player, availability?, form?})",
    )
    p_batch.add_argument(
        "json_file",
        help="Path to JSON file, or - for stdin",
    )

    args = parser.parse_args()

    if args.command == "update":
        if args.availability is None and args.form is None:
            print("  Nothing to update. Pass --availability and/or --form.")
            sys.exit(1)
        update_player(args.player, availability=args.availability, form=args.form)
    elif args.command == "reset":
        reset_player(args.player)
    elif args.command == "show":
        show_all()
    elif args.command == "log":
        if not LOG_PATH.exists():
            print("  No changelog entries yet.")
        else:
            lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
            tail = lines[-args.n:]
            for line in tail:
                print(f"  {line}")
    elif args.command == "batch":
        try:
            updates = load_batch_json(args.json_file)
        except FileNotFoundError as e:
            print(f"  {e}", file=sys.stderr)
            sys.exit(1)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  Invalid batch JSON: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"  Batch: {len(updates)} row(s)")
        applied, skipped = bulk_update(updates)
        print(f"  Summary: applied={applied}, skipped={skipped}")


def bulk_update(updates: list[dict]) -> tuple[int, int]:
    """
    Update multiple players from a list of dictionaries.
    Each dict must have a 'player' key (squads ShortName) and at least one of
    'availability' or 'form'.

    Returns:
        (applied_count, skipped_count)

    Example:
        updates = [
            {"player": "X", "availability": "ruled_out"},
            {"player": "Y", "availability": "available", "form": "good"},
        ]
    """
    applied = 0
    skipped = 0
    for entry in updates:
        if not isinstance(entry, dict):
            print(f"  Skipping non-object entry: {entry!r}")
            skipped += 1
            continue

        player_name = entry.get("player")
        if not player_name:
            print(f"  Skipping entry without 'player' key: {entry}")
            skipped += 1
            continue

        availability = entry.get("availability")
        form = entry.get("form")

        if availability is None and form is None:
            print(f"  Skipping {player_name}: no availability or form specified")
            skipped += 1
            continue

        update_player(player_name, availability=availability, form=form)
        applied += 1

    return applied, skipped


def load_batch_json(path_or_dash: str) -> list[dict]:
    """Load JSON array from a file path or '-' for stdin."""
    if path_or_dash.strip() == "-":
        raw = sys.stdin.read()
    else:
        p = Path(path_or_dash)
        if not p.is_file():
            raise FileNotFoundError(f"Not a file: {p}")
        raw = p.read_text(encoding="utf-8")

    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("JSON root must be an array of objects")
    return data


if __name__ == "__main__":
    main()
