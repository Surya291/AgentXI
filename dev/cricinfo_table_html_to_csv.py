"""
Parse ESPNcricinfo Design System (ds-table) HTML exports to CSV.
Works with saved page snippets that contain a single <table>...</table>.

Supports the usual series leaderboards:
- Most impactful **bowlers** (Bowling Impact, wickets, …)
- Most impactful **batters** (Batting Impact, BI/Inn, Runs, Impact Runs, …)
- **MVP** / total-impact tables (Total Impact, Impact/Mat, Matches, Runs, Wkts)

Headers are taken from <thead> when possible; if that does not match the row
width, defaults are chosen from the table kind inferred from header text.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


def _iter_td_inner_html(tr_html: str):
    """Yield inner HTML for each <td>...</td> in a <tr>, handling nested <td>."""
    idx = 0
    n = len(tr_html)
    while idx < n:
        start = tr_html.find("<td", idx)
        if start == -1:
            break
        gt = tr_html.find(">", start)
        if gt == -1:
            break
        inner_start = gt + 1
        depth = 1
        pos = inner_start
        while pos < n and depth:
            next_td = tr_html.find("<td", pos)
            next_close = tr_html.find("</td>", pos)
            if next_close == -1:
                break
            if next_td != -1 and next_td < next_close:
                depth += 1
                pos = next_td + 3
            else:
                depth -= 1
                if depth == 0:
                    yield tr_html[inner_start:next_close]
                    idx = next_close + len("</td>")
                    break
                pos = next_close + len("</td>")


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def _player_cell(td_html: str) -> tuple[str, str]:
    """Return (rank, player_name) from first column."""
    rank_m = re.search(
        r'ds-min-w-\[1\.5em\][^>]*>(\d+)\s*</span>', td_html
    ) or re.search(r">(\d+)\s*</span>\s*<div", td_html)
    rank = rank_m.group(1) if rank_m else ""

    # Player link: title on cricketers anchor (not empty title on image wrapper)
    for m in re.finditer(
        r'href="/cricketers/[^"]+"\s+title="([^"]+)"', td_html
    ):
        name = m.group(1).strip()
        if name:
            return rank, name

    # Fallback: visible medium-weight name span
    text = _strip_tags(td_html)
    text = re.sub(r"\s+", " ", text).strip()
    return rank, text


def _team_cell(td_html: str) -> str:
    m = re.search(r'href="/team/[^"]+"\s+title="([^"]*)"', td_html)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return _strip_tags(td_html).strip()


def _numeric_cell(td_html: str) -> str:
    return _strip_tags(td_html).strip()


def _default_headers_eight_col(
    thead_titles: list[str],
    *,
    html_context: str = "",
) -> list[str]:
    """
    When <thead> could not be aligned to data, pick column names for the
    standard 8-column export: Rank, Player, Team, plus five metrics.
    """
    base = ["Rank", "Player", "Team"]
    blob = (" ".join(thead_titles) + " " + html_context).lower()

    if "batting impact" in blob or "bi/inn" in blob or "impact runs" in blob:
        return base + [
            "Batting Impact",
            "BI/Inn",
            "Inns",
            "Runs",
            "Impact Runs",
        ]
    if "bowling impact" in blob or "impact wickets" in blob or "bol/mat" in blob:
        return base + [
            "Bowling Impact",
            "Bol/Mat",
            "Inns",
            "Wkts",
            "Impact Wickets",
        ]
    if "total impact" in blob:
        return base + [
            "Total Impact",
            "Impact/Mat",
            "Matches",
            "Runs",
            "Wkts",
        ]

    ctx = html_context.lower()
    if "impactful batters" in ctx or "most-impactful-batters" in ctx:
        return base + [
            "Batting Impact",
            "BI/Inn",
            "Inns",
            "Runs",
            "Impact Runs",
        ]
    if "impactful bowlers" in ctx or "most-impactful-bowlers" in ctx:
        return base + [
            "Bowling Impact",
            "Bol/Mat",
            "Inns",
            "Wkts",
            "Impact Wickets",
        ]
    if "most valuable" in ctx or "most-valuable-players" in ctx:
        return base + [
            "Total Impact",
            "Impact/Mat",
            "Matches",
            "Runs",
            "Wkts",
        ]

    return base + [f"metric_{i}" for i in range(5)]


def cricinfo_table_html_to_csv(
    html_source: str | Path,
    csv_path: str | Path,
    *,
    encoding: str = "utf-8",
) -> list[list[str]]:
    """
    Read HTML from a file path or raw string, find the first ds-table, write CSV.

    Header row is taken from <thead> title="..." on column headers when present,
    otherwise generic names. Returns the rows written (including header).
    """
    if isinstance(html_source, Path):
        html = html_source.read_text(encoding=encoding)
    elif isinstance(html_source, str):
        head = html_source.lstrip()[:800]
        if head.startswith("<") and ("<table" in head or "<TABLE" in head):
            html = html_source
        else:
            p = Path(html_source).expanduser()
            html = p.read_text(encoding=encoding) if p.is_file() else html_source
    else:
        html = str(html_source)

    # Optional: isolate first table
    t_start = html.find("<table")
    if t_start == -1:
        raise ValueError("No <table> found in HTML")
    t_end = html.find("</table>", t_start)
    if t_end == -1:
        table_html = html[t_start:]
    else:
        table_html = html[t_start : t_end + len("</table>")]

    thead_m = re.search(r"<thead[^>]*>(.*?)</thead>", table_html, re.DOTALL | re.IGNORECASE)
    thead_titles: list[str] = []
    if thead_m:
        for th in re.finditer(
            r'<th[^>]*>.*?title="([^"]*)"', thead_m.group(1), re.DOTALL | re.IGNORECASE
        ):
            h = th.group(1).strip()
            if h:
                thead_titles.append(h)
        if not thead_titles:
            for th in re.finditer(
                r"<th[^>]*>(.*?)</th>", thead_m.group(1), re.DOTALL | re.IGNORECASE
            ):
                t = _strip_tags(th.group(1)).strip()
                if t:
                    thead_titles.append(t)

    # First thead column is "Player" but includes rank in the cell — CSV uses Rank + Player.
    if thead_titles and thead_titles[0].lower() == "player":
        headers = ["Rank", "Player"] + thead_titles[1:]
    elif thead_titles:
        headers = thead_titles[:]
    else:
        headers = []

    tbody_m = re.search(r"<tbody[^>]*>(.*)</tbody>", table_html, re.DOTALL | re.IGNORECASE)
    if not tbody_m:
        raise ValueError("No <tbody> found in table")

    tbody = tbody_m.group(1)
    rows_out: list[list[str]] = []

    for tr_m in re.finditer(r"<tr[^>]*>(.*?)</tr>", tbody, re.DOTALL | re.IGNORECASE):
        tr_inner = tr_m.group(1)
        cells = list(_iter_td_inner_html(tr_inner))
        if len(cells) < 2:
            continue

        rank, player = _player_cell(cells[0])
        team = _team_cell(cells[1])
        rest = [_numeric_cell(c) for c in cells[2:]]
        row = [rank, player, team, *rest]
        rows_out.append(row)

    if not rows_out:
        raise ValueError("No data rows found in <tbody>")

    ncols = len(rows_out[0])
    if len(headers) != ncols:
        if ncols == 8:
            ctx_start = max(0, t_start - 8000)
            html_context = html[ctx_start : t_start + min(len(table_html), 12000)]
            headers = _default_headers_eight_col(thead_titles, html_context=html_context)
        else:
            headers = [f"col_{i}" for i in range(ncols)]

    for i, row in enumerate(rows_out):
        if len(row) < ncols:
            row.extend([""] * (ncols - len(row)))
            rows_out[i] = row
        elif len(row) > ncols:
            rows_out[i] = row[:ncols]
    out_rows = [headers] + rows_out
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding=encoding) as f:
        w = csv.writer(f)
        w.writerows(out_rows)

    return out_rows


if __name__ == "__main__":
    import sys

    base = Path(__file__).resolve().parents[1]
    inp = base / "data" / "2025-bowlers.html"

    default_out = inp.with_suffix(".csv")
    resp = input(f"Enter output CSV file name (leave blank for '{default_out.name}'): ").strip()
    if resp:
        out = Path(resp)
        if not out.is_absolute():
            out = default_out.parent / out
    else:
        out = default_out

    data = cricinfo_table_html_to_csv(inp, out)
    print(f"Wrote {out} ({len(data) - 1} data rows)")
