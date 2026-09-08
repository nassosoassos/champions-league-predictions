#!/usr/bin/env python3
"""
Fetch Champions League match odds from The Odds API, de-vig them, and emit a
clean market-consensus probability per upcoming match.

The market (especially sharp books like Pinnacle) is the strongest single
predictor we have. This script turns raw bookmaker prices into fair, vig-free
probabilities so the agent can reason about them.

The UEFA Champions League league phase runs in tight 3-day matchday clusters
(Tue/Wed/Thu) with weeks of nothing in between — a quiet window is normal,
not a sign the pipeline is broken.

Usage:
    THE_ODDS_API_KEY=xxxx python3 scripts/fetch_odds.py --days 4

Outputs:
    - data/odds-YYYY-MM-DD.json   (structured, for the agent to read)
    - prints a human-readable summary to stdout

Stdlib only — no pip install required.
"""
from __future__ import annotations  # allow `X | None` hints on older Python

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

API_BASE = "https://api.the-odds-api.com/v4"
SPORT = "soccer_uefa_champs_league"  # The Odds API key for the UEFA Champions League

# Books we trust most get more weight in the consensus. Pinnacle is the
# canonical "sharp" book; its line is the closest thing to a true probability.
SHARP_WEIGHTS = {
    "pinnacle": 3.0,
    "betfair_ex_eu": 2.0,  # exchange = real money, low margin
    "smarkets": 2.0,
}
DEFAULT_WEIGHT = 1.0

# 2026-27 league-phase matchday calendar (verified from UEFA.com). Used only
# to give a friendly "next matchday" message when the window is quiet — the
# actual fixture list always comes live from the API.
MATCHDAY_CALENDAR = [
    ("MD1", "8-10 Sep 2026"),
    ("MD2", "13-14 Oct 2026"),
    ("MD3", "20-21 Oct 2026"),
    ("MD4", "3-4 Nov 2026"),
    ("MD5", "24-25 Nov 2026"),
    ("MD6", "8-9 Dec 2026"),
    ("MD7", "19-20 Jan 2027"),
    ("MD8", "27 Jan 2027"),
]


def next_matchday(now: datetime) -> tuple[str, str] | None:
    """First calendar entry whose start date hasn't passed yet."""
    for label, date_range in MATCHDAY_CALENDAR:
        # date_range looks like "8-10 Sep 2026" (multi-day) or "27 Jan 2027"
        # (single day, MD8's all-simultaneous kickoff). Either way the first
        # token's leading number is the start day, and the last two tokens
        # are the month and year.
        tokens = date_range.split()  # e.g. ["8-10", "Sep", "2026"]
        start_day = tokens[0].split("-")[0]
        month, year = tokens[-2], tokens[-1]
        try:
            start = datetime.strptime(f"{start_day} {month} {year}", "%d %b %Y").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        if start >= now.replace(hour=0, minute=0, second=0, microsecond=0):
            return label, date_range
    return None


def existing_match_count(path: str) -> int | None:
    """Match count currently on disk at path, or None if absent/unreadable."""
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return len(data.get("matches", []))
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def fetch(api_key: str, regions: str) -> list:
    url = (
        f"{API_BASE}/sports/{SPORT}/odds/"
        f"?apiKey={api_key}&regions={regions}&markets=h2h&oddsFormat=decimal"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "ucl-predictor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            remaining = resp.headers.get("x-requests-remaining")
            used = resp.headers.get("x-requests-used")
            if remaining is not None:
                print(f"[odds-api] requests remaining: {remaining} (used: {used})",
                      file=sys.stderr)
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"[odds-api] HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        sys.exit(f"[odds-api] network error: {e.reason}")


def devig_book(outcomes: dict) -> dict:
    """outcomes: {name: decimal_odds} -> vig-free probabilities summing to 1."""
    implied = {k: 1.0 / v for k, v in outcomes.items() if v and v > 1.0}
    total = sum(implied.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in implied.items()}


def consensus(event: dict) -> dict | None:
    """Weighted-average vig-free probabilities across all books for one match."""
    home, away = event.get("home_team"), event.get("away_team")
    if not home or not away:
        return None

    # accumulate weighted probabilities keyed by outcome label
    agg: dict[str, float] = {}
    weight_sum = 0.0
    book_count = 0

    for bookmaker in event.get("bookmakers", []):
        key = bookmaker.get("key", "")
        weight = SHARP_WEIGHTS.get(key, DEFAULT_WEIGHT)
        for market in bookmaker.get("markets", []):
            if market.get("key") != "h2h":
                continue
            outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
            fair = devig_book(outcomes)
            if not fair:
                continue
            for name, p in fair.items():
                agg[name] = agg.get(name, 0.0) + p * weight
            weight_sum += weight
            book_count += 1

    if weight_sum == 0 or not agg:
        return None

    probs = {k: round(v / weight_sum, 4) for k, v in agg.items()}
    # normalize labels into home / draw / away
    draw_p = probs.get("Draw", 0.0)
    return {
        "match": f"{home} vs {away}",
        "home_team": home,
        "away_team": away,
        "commence_time": event.get("commence_time"),
        "books_counted": book_count,
        "prob": {
            "home": probs.get(home, 0.0),
            "draw": round(draw_p, 4),
            "away": probs.get(away, 0.0),
        },
        "market_favorite": max(
            [("home", probs.get(home, 0.0)),
             ("draw", draw_p),
             ("away", probs.get(away, 0.0))],
            key=lambda x: x[1],
        )[0],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=4,
                    help="only include matches kicking off within N days "
                         "(a UCL matchday is a 3-day Tue/Wed/Thu cluster)")
    ap.add_argument("--regions", default="eu,uk",
                    help="comma-separated odds regions (eu,uk,us,au)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite the existing file even if the new fetch "
                         "has fewer matches than what's already on disk")
    args = ap.parse_args()

    api_key = os.environ.get("THE_ODDS_API_KEY")
    if not api_key:
        sys.exit("Set THE_ODDS_API_KEY in the environment first.")

    events = fetch(api_key, args.regions)
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=args.days)

    out = []
    for ev in events:
        ct = ev.get("commence_time")
        if ct:
            t = datetime.fromisoformat(ct.replace("Z", "+00:00"))
            if t < now or t > horizon:
                continue
        c = consensus(ev)
        if c:
            out.append(c)

    out.sort(key=lambda x: x.get("commence_time") or "")

    today = now.strftime("%Y-%m-%d")
    os.makedirs("data", exist_ok=True)
    path = f"data/odds-{today}.json"

    existing_count = existing_match_count(path)
    if existing_count is not None and len(out) < existing_count and not args.force:
        print(f"\nrefusing to overwrite {path}: {existing_count} matches on "
              f"disk, {len(out)} fetched — keeping existing file\n"
              f"(re-run with --force to overwrite)")
        return

    with open(path, "w") as f:
        json.dump({"generated_at": now.isoformat(), "matches": out}, f, indent=2)

    # human-readable summary
    if not out:
        nxt = next_matchday(now)
        print(f"\nNo fixtures in the next {args.days} days — that's normal between "
              "Champions League matchdays.")
        if nxt:
            label, date_range = nxt
            print(f"Next matchday: {label} ({date_range}).")
        print(f"\nWrote {path} (0 matches)")
        return

    print(f"\nMarket consensus for {len(out)} matches (next {args.days} days, "
          f"~{round(sum(m['books_counted'] for m in out) / len(out))} books/match avg):\n")
    for m in out:
        p = m["prob"]
        print(f"  {m['commence_time'][:16]}  {m['match']}")
        print(f"      home {p['home']:.0%} | draw {p['draw']:.0%} | "
              f"away {p['away']:.0%}   ({m['books_counted']} books)")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
