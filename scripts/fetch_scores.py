#!/usr/bin/env python3
"""
Fetch ACTUAL final (and live) scores from The Odds API, so the agent can
grade past predictions and update tracking/<comp>/accuracy.md — for every
competition in config/competitions.json (or just the ones named with --comp).

Zero completed matches is the normal state between matchdays — league
phases run in tight clusters with weeks of nothing after, so a quiet day is
not a failure. Before spending a paid /scores credit, this script checks
LOCALLY whether any prediction on disk actually needs grading (kickoff
inside the --days-from window, no completed result recorded yet) and skips
the call entirely when there's nothing to grade.

Usage:
    THE_ODDS_API_KEY=xxxx python3 scripts/fetch_scores.py --days-from 3
    THE_ODDS_API_KEY=xxxx python3 scripts/fetch_scores.py --comp uel

Outputs:
    - data/<comp>/scores-YYYY-MM-DD.json   (structured, for the agent to read)
    - prints a human-readable summary to stdout

Stdlib only — no pip install required.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common


def parse_event(ev: dict) -> dict | None:
    home, away = ev.get("home_team"), ev.get("away_team")
    if not home or not away:
        return None
    scores = {s["name"]: s["score"] for s in (ev.get("scores") or [])}
    hs, as_ = scores.get(home), scores.get(away)

    result = None
    if ev.get("completed") and hs is not None and as_ is not None:
        try:
            h, a = int(hs), int(as_)
            result = "home" if h > a else "away" if a > h else "draw"
        except ValueError:
            pass

    return {
        "match": f"{home} vs {away}",
        "home_team": home,
        "away_team": away,
        "commence_time": ev.get("commence_time"),
        "completed": bool(ev.get("completed")),
        "home_score": hs,
        "away_score": as_,
        "final_score": f"{hs}-{as_}" if hs is not None and as_ is not None else None,
        "result": result,  # home / draw / away, only when completed
        "last_update": ev.get("last_update"),
    }


def needs_grading(comp: str, days_from: int, now: datetime) -> bool:
    """LOCAL check (no API call): is there a prediction whose kickoff falls
    inside the days-from window and has no completed result on disk yet?"""
    cutoff = now - timedelta(days=days_from)
    completed = {(s.get("home_team"), s.get("away_team"))
                 for s in common.load_all_records(comp, "scores", "matches")
                 if s.get("completed")}
    for p in common.load_all_records(comp, "predictions", "predictions"):
        ct = p.get("commence_time")
        if not ct:
            continue
        try:
            t = datetime.fromisoformat(ct.replace("Z", "+00:00"))
        except ValueError:
            continue
        if t > now or t < cutoff:
            continue  # not yet kicked off, or older than the days-from window
        pair = (p.get("home_team"), p.get("away_team"))
        if pair not in completed:
            return True
    return False


def fetch_scores_for(comp: str, cfg: dict, api_key: str, args, now: datetime) -> None:
    short = cfg["short"]
    today = now.strftime("%Y-%m-%d")

    if not needs_grading(comp, args.days_from, now):
        print(f"\n{short}: nothing to grade — 0 credits spent")
        return

    events, _ = common.api_get(
        f"sports/{cfg['sport_key']}/scores", api_key, daysFrom=args.days_from,
    )
    out = [p for ev in events if (p := parse_event(ev))]
    out.sort(key=lambda x: x.get("commence_time") or "")

    os.makedirs(common.data_dir(comp), exist_ok=True)
    path = common.data_path(comp, "scores", today)

    if common.refuse_to_shrink(path, len(out), args.force):
        return

    with open(path, "w") as f:
        json.dump({"generated_at": now.isoformat(), "matches": out}, f, indent=2)

    done = [m for m in out if m["completed"]]
    live = [m for m in out if not m["completed"] and m["home_score"] is not None]

    if not done and not live:
        print(f"\n{short}: no completed or in-play matches — normal between matchdays.")
        print(f"{short}: wrote {path} ({len(out)} matches written; 0 completed/in-play)")
        return

    print(f"\n{short}: {len(done)} completed, {len(live)} in-play:\n")
    for m in done:
        print(f"  FT   {m['match']}: {m['final_score']}  ({m['result']})")
    for m in live:
        print(f"  LIVE {m['match']}: {m['final_score']}")
    print(f"{short}: wrote {path} ({len(out)} matches written)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days-from", type=int, default=3, choices=[1, 2, 3],
                    help="also include games completed within the last N days")
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
            print(f"[fetch_scores] unknown competition '{comp}' — skipping", file=sys.stderr)
            continue
        fetch_scores_for(comp, registry[comp], api_key, args, now)


if __name__ == "__main__":
    main()
