import json
from pathlib import Path
from typing import Any, Dict, List


# ROOT_DIR = Path(__file__).resolve().parents[1]
# INPUT_PATH = ROOT_DIR / "data" / "raw_game_day_players.json"
# OUTPUT_PATH = ROOT_DIR / "data" / "clean_game_day_players.json"


def to_bool(value: Any) -> bool:
    """Normalize 0/1 and '0'/'1' style values to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip() in {"1", "true", "True", "yes", "YES"}
    return False


def extract_players(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    return raw.get("Data", {}).get("Value", {}).get("Players", [])


def build_hierarchy(players: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Build: team_short_name -> skill_name -> players list,
    with players sorted in each role by decreasing SelectedPer.
    """
    hierarchy: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for player in players:
        team_short_name = str(player.get("TeamShortName", "")).strip()
        skill_name = str(player.get("SkillName", "")).strip()

        if not team_short_name or not skill_name:
            continue

        cleaned_player = {
            "Id": player.get("Id"),
            "ShortName": player.get("ShortName"),
            "Value": player.get("Value"),
            "SelectedPer": player.get("SelectedPer"),
            "isInjured": to_bool(player.get("isInjured")),
            "IsActive": to_bool(player.get("IsActive")),
            "isOverseasPlayer": to_bool(player.get("IS_FP")),
            # "availability": "available", # [ruled_out, temporarily_injured, benced, available]
            # "form": None
        }

        hierarchy.setdefault(team_short_name, {}).setdefault(skill_name, []).append(cleaned_player)

    # Sort players in each team/role by decreasing SelectedPer
    for team_roles in hierarchy.values():
        for skill_players in team_roles.values():
            skill_players.sort(key=lambda p: (p["SelectedPer"] if p["SelectedPer"] is not None else -float("inf")), reverse=True)

    return hierarchy


def main() -> None:
    INPUT_PATH = Path("/home/surya/AgentXI/archive/raw_game_day_players.json")
    OUTPUT_PATH = Path("/home/surya/AgentXI/data/squads.json")
    
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    players = extract_players(raw_data)
    clean_data = build_hierarchy(players)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)

    print(f"Created: {OUTPUT_PATH}")
    print(f"Teams: {len(clean_data)}")
    print(f"Players parsed: {len(players)}")

if __name__ == "__main__":
    main()