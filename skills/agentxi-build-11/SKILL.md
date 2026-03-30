---
name: agentxi-build-11
description: Standard operating procedure for Agent XI - generating fantasy XI for IPL using local python scripts and formatting for Telegram.
---

# Agent XI - Build 11 Generation Rules

This skill defines how to generate and format a playing XI for the user, acting as Agent XI.

## Prerequisites
- Run all commands from the **AgentXI project root**: `/home/surya/AgentXI`

## 1. Updating Player Status
If the user provides news (injury, benching, form) about a player, update it before running the optimizer:
```bash
python -m main.player_status update "Player Name" -a <availability> -f <form>
```
- `<availability>`: `available`, `benched`, `temporarily_injured`, `ruled_out`
- `<form>`: `bad`, `average`, `good`, `excellent`

## 2. Generating the XI
To generate an XI for specific matches:
```bash
python -m main.optimizer.run_match_ids <match_id_1> <match_id_2> ... [-p pick_name] [-d drop_name]
```
- `-p`: Force pick a player (partial name match)
- `-d`: Drop a player (partial name match)

## 3. Output Formatting (CRITICAL)
When outputting a generated fantasy XI, strictly follow this format as your **final text response**. 

**CRITICAL:** If the user is chatting with you directly on Telegram, do NOT use the `send_message` tool. Just return the formatted text as your normal reply. Using `send_message` plus a text reply causes duplicate messages.

#### Structure
Start with the **Fixture Window**, clearly defining the match-ups.
Output the players grouped by role in ALL CAPS (`WICKET-KEEPER`, `BATTERS`, `ALL-ROUNDERS`, `BOWLERS`).
Each player must be on a single line in this exact format:
`Player Name [Team] | V: <Price> | E[P]: <AdjEV>`

**CRITICAL:** Do NOT mention internal signals like form, availability, or lock status.

Below the XI, include a divider `---`.
Following the divider, provide a brief, punchy tactical overview using short forms.
End with the value paid and the expected ceiling.

### Example Output
```
Fixture Window
#1: RCB v SRH 
#2 MI v KKR

WICKET-KEEPER
Phil Salt [RCB] | V: 9.5 | E[P]: 35.71

BATTERS
Suryakumar Yadav [MI] | V: 10.5 | E[P]: 39.57
Virat Kohli [RCB] | V: 11.0 | E[P]: 51.17

ALL-ROUNDERS
Sunil Narine [KKR] | V: 10.5 | E[P]: 39.15
Romario Shepherd [RCB] | V: 8.5 | E[P]: 31.27

BOWLERS
Jasprit Bumrah [MI] | V: 11.0 | E[P]: 48.54

---
Heavy top-order bat power. Elite death bowl depth. Core 3D players locking in floor points. 

Value Paid: 100.0/100.0 | Expected Ceiling: 389.58. Lock it in.
```