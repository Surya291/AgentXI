---
name: agentxi-news
description: >-
  Polls Agent XI IPL RSS news, classifies articles for player form or availability,
  fetches article text when needed, and updates player_status only after explicit user
  consent. Use when the user asks for news checks, injury updates, hourly IPL news
  polling, RSS monitoring, or syncing player status from CricTracker-style headlines.
---

# Agent XI — News poll, fetch, and player status (Build 2)

Standard procedure for Hermes when running the **news → relevance → consent → status** loop. Complements **agentxi-build-11** (XI generation uses `player_status.json` automatically).

## Prerequisites

- **Working directory:** `/home/surya/AgentXI` (all `python -m` commands below assume this cwd).
- **Player names** in `update` commands must match **squads** `ShortName` strings exactly once resolved (no guessing abbreviations if ambiguous).

## When to use this skill

- Scheduled or on-demand **hourly** (or similar) news checks.
- User asks whether anything new dropped for IPL / fantasy-relevant news.
- After surfacing news, user agrees to **reflect** it in availability or form.

## Automated Cron Setup (Strict Token-Saving Rule)

When the user requests scheduling news polling via the `cronjob` tool:
- **Rule:** Do NOT instruct the cron job to autonomously analyze the news for player form/availability. The user explicitly prefers to save tokens here.
- **Cron Prompt Template:** "Run `cd /home/surya/AgentXI && python -m main.news poll`. If output contains 'No new items.', reply strictly with 'No new IPL news this hour.' Otherwise, list the new Titles and Descriptions. End by asking the user: 'Do you want to update any player statuses based on this news?'"

## Commands (run from shell)

| Step | Command | Notes |
|------|---------|--------|
| New since last poll | `python -m main.news poll` | Persists seen links in `data/rss_feed_state.json`. Empty output = nothing new. |
| Peek without marking seen | `python -m main.news latest -n 10` | Or `latest-json -n 10` for machine parsing. |
| Full article body | `python -m main.news fetch "<url>"` | Plain text, ~8k cap; use when title/description are not enough. |
| After long downtime | `python -m main.news reset-state` | Next `poll` re-emits entire feed; use sparingly. |

## Workflow (follow in order)

```
1. Poll
     run: python -m main.news poll

2. If no new items → tell user briefly and stop (unless they asked for latest peek).

3. For each new item (title + description, and link):
     a. Decide if it implies a concrete player + availability or form signal
        (injury, ruled out, benching, strong/weak recent form, etc.).
     b. If not fantasy-relevant → skip (no Telegram noise).

4. If relevant:
     a. Optionally compare against player_status: use last_updated / current row
        to avoid re-proposing the same update.
     b. Notify user (e.g. Telegram): title, one-line summary, link.
     c. Ask explicitly: whether to update status for named player(s).

5. Only after user says yes (consent):
     run: python -m main.player_status update "<Player Name>" -a <availability> [-f <form>]
     -a: available | benched | temporarily_injured | ruled_out
     -f: bad | average | good | excellent
     (Omit flags that should stay unchanged.)

6. If consent and headline is vague:
     run fetch first, then decide availability/form from body text, then update.

7. Log / audit: player_status changelog is updated automatically; do not edit
     data/squads.json for status (overlay file only).
```

## Output and UX rules

- **One notification per actionable item** (or one batched message with clear bullets); avoid duplicate channel + reply patterns if the runtime would double-send.
- Prefer **short quotes** from title/description in the user message; paste `fetch` excerpts only when they change the conclusion.
- If multiple players are mentioned, list each proposed `update` line before running commands.

## Deep reference (optional read)

- User-facing commands: `AgentXI/markdowns/BUILD2_NEWS_USE.md`
- Architecture, state file, pseudocode: `AgentXI/markdowns/BUILD2_NEWS_INTERNAL.md`

## Coordination with Build 11

After status updates, the next XI run (`python -m main.optimizer.run_match_ids ...`) picks up new **availability** (non-`available` excluded) and **form** multipliers. No extra step beyond running the optimizer skill when the user wants a new team.
