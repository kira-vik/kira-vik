#!/usr/bin/env python3
"""Scrape your public contribution calendar (no token needed) into data/contributions.json.

GitHub serves the calendar fragment at https://github.com/users/<user>/contributions.
Private contributions only appear if "Include private contributions on my profile"
is enabled in your profile settings.
"""
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import UTC, date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "kira-vik")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
COUNT_RE = re.compile(r"^\s*(No|\d[\d,]*)\s+contributions?\b", re.IGNORECASE)


def fetch_html() -> str:
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}, timeout=30)
    r.raise_for_status()
    return r.text


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # tooltips carry the real counts: <tool-tip for="cell-id">3 contributions on ...</tool-tip>
    tips = {}
    for tip in soup.find_all("tool-tip"):
        m = COUNT_RE.match(tip.get_text(strip=True))
        if m and tip.get("for"):
            tips[tip["for"]] = 0 if m.group(1).lower() == "no" else int(m.group(1).replace(",", ""))

    days = {}
    for cell in soup.select("[data-date]"):
        d = cell.get("data-date")
        if not d:
            continue
        # level = int(cell.get("data-level", 0) or 0)
        raw_level = cell.get("data-level", 0)

        if isinstance(raw_level, (str, int)):
            level = int(raw_level or 0)
        else:
            level = 0
        count = tips.get(cell.get("id"))
        if count is None:  # fallback: estimate from level
            count = 0 if level == 0 else level
        days[d] = {"date": d, "count": count, "level": level}

    return [days[k] for k in sorted(days)]


def stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # current streak: walk back from the latest day; an empty *today* doesn't break it
    cur = 0
    seq = list(days)
    today = date.today().isoformat()
    if seq and seq[-1]["count"] == 0 and seq[-1]["date"] >= today:
        seq = seq[:-1]
    for d in reversed(seq):
        if d["count"] > 0:
            cur += 1
        else:
            break

    best = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}
    months: OrderedDict[str, int] = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    return {
        "total": total,
        "current_streak": cur,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "months": months,
    }


def main():
    days = parse(fetch_html())
    if not days:
        sys.exit("No contribution cells found - GitHub's markup may have changed.")
    data = {
        "username": USERNAME,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **stats(days),
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{USERNAME}: {data['total']:,} contributions across {len(days)} days -> {OUT}")


if __name__ == "__main__":
    main()
