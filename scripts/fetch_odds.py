#!/usr/bin/env python3
"""
Fetch match odds from The Odds API, de-vig them, and emit a clean
market-consensus probability per upcoming match — for every competition in
config/competitions.json (or just the ones named with --comp).

The market (especially sharp books like Pinnacle) is the strongest single
predictor we have. This script turns raw bookmaker prices into fair, vig-free
probabilities so the agent can reason about them.

UEFA's league phases run in tight clusters of matchdays with weeks of
nothing in between — a quiet window is normal, not a sign the pipeline is
broken. config/competitions.json is the source of truth for each
competition's calendar; before spending a credit on the paid /odds call,
this script checks the FREE /events endpoint for fixtures in the window and
skips the paid call entirely when there are none.

Usage:
    THE_ODDS_API_KEY=xxxx python3 scripts/fetch_odds.py --days 4
    THE_ODDS_API_KEY=xxxx python3 scripts/fetch_odds.py --comp uel

Outputs:
    - data/<comp>/odds-YYYY-MM-DD.json   (structured, for the agent to read)
    - prints a human-readable summary to stdout

Stdlib only — no pip install required.
"""
from __future__ import annotations  # allow `X | None` hints on older Python

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

# Books we trust most get more weight in the consensus. Pinnacle is the
# canonical "sharp" book; its line is the closest thing to a true probability.
SHARP_WEIGHTS = {
    "pinnacle": 3.0,
    "betfair_ex_eu": 2.0,  # exchange = real money, low margin
    "smarkets": 2.0,
}
DEFAULT_WEIGHT = 1.0


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


def has_fixtures_in_window(sport_key: str, api_key: str, now: datetime, horizon: datetime) -> bool:
    """FREE pre-check: is there anything worth spending a paid /odds call on?"""
    events, _ = common.list_events(sport_key, api_key)
    for ev in events:
        ct = ev.get("commence_time")
        if not ct:
            continue
        t = datetime.fromisoformat(ct.replace("Z", "+00:00"))
        if now <= t <= horizon:
            return True
    return False


def fetch_odds_for(comp: str, cfg: dict, api_key: str, args, now: datetime) -> None:
    short = cfg["short"]
    horizon = now + timedelta(days=args.days)
    today = now.strftime("%Y-%m-%d")

    if not has_fixtures_in_window(cfg["sport_key"], api_key, now, horizon):
        print(f"\n{short}: no fixtures in the next {args.days} days — 0 credits spent")
        entry_id, date_range, is_today = common.current_or_next_matchday(cfg, today)
        if entry_id and not is_today:
            print(f"{short}: next matchday {entry_id} ({date_range}).")
        return

    events, _ = common.api_get(
        f"sports/{cfg['sport_key']}/odds", api_key,
        regions=args.regions, markets="h2h", oddsFormat="decimal",
    )

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

    os.makedirs(common.data_dir(comp), exist_ok=True)
    path = common.data_path(comp, "odds", today)

    if common.refuse_to_shrink(path, len(out), args.force):
        return

    with open(path, "w") as f:
        json.dump({"generated_at": now.isoformat(), "matches": out}, f, indent=2)

    if not out:
        print(f"\n{short}: no fixtures in the next {args.days} days — that's normal "
              "between matchdays.")
        print(f"{short}: wrote {path} (0 matches)")
        return

    print(f"\n{short}: market consensus for {len(out)} matches (next {args.days} days, "
          f"~{round(sum(m['books_counted'] for m in out) / len(out))} books/match avg):\n")
    for m in out:
        p = m["prob"]
        print(f"  {m['commence_time'][:16]}  {m['match']}")
        print(f"      home {p['home']:.0%} | draw {p['draw']:.0%} | "
              f"away {p['away']:.0%}   ({m['books_counted']} books)")
    print(f"{short}: wrote {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=4,
                    help="only include matches kicking off within N days "
                         "(a matchday is typically a multi-day cluster)")
    ap.add_argument("--regions", default="eu,uk",
                    help="comma-separated odds regions (eu,uk,us,au)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite the existing file even if the new fetch "
                         "has fewer matches than what's already on disk")
    ap.add_argument("--comp", action="append", dest="comps",
                    help="competition key from config/competitions.json "
                         "(repeatable; default: all)")
    args = ap.parse_args()

    api_key = os.environ.get("THE_ODDS_API_KEY")
    if not api_key:
        sys.exit("Set THE_ODDS_API_KEY in the environment first.")

    registry = common.load_competitions()
    comps = args.comps or list(registry.keys())
    now = datetime.now(timezone.utc)

    for comp in comps:
        if comp not in registry:
            print(f"[fetch_odds] unknown competition '{comp}' — skipping", file=sys.stderr)
            continue
        fetch_odds_for(comp, registry[comp], api_key, args, now)


if __name__ == "__main__":
    main()
