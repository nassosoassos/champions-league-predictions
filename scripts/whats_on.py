#!/usr/bin/env python3
"""
Zero-credit oracle for the daily run.

Run this FIRST, before anything that spends API credits. For every
competition in config/competitions.json (registry order) it reports:
  - where today falls on the competition's calendar;
  - fixtures in the next N hours (default 48) that have no prediction yet;
  - ungraded predictions (kickoff in the past, no completed result on disk
    yet), split into API-gradeable (<=3 days old) and needs-web (older —
    the scores API's own daysFrom ceiling can't reach that far back);
  - whether outrights are on disk yet, and whether the outrights lock has
    passed.

It ends with one verdict line: "ACTION: full run for <comps>",
"ACTION: maintenance only", or "ACTION: nothing to do".

Only ever calls The Odds API's FREE /v4/sports/{sport}/events endpoint —
never /odds or /scores — so it costs 0 credits no matter how often it runs.
Always exits 0: this is a read-only report, never a hard failure.

Usage:
    THE_ODDS_API_KEY=xxxx python3 scripts/whats_on.py
    THE_ODDS_API_KEY=xxxx python3 scripts/whats_on.py --hours 72 --json

Stdlib only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

GRADE_WINDOW_DAYS = 3  # matches fetch_scores.py's --days-from ceiling


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def calendar_line(cfg: dict, today: str) -> str:
    entry_id, date_range, is_today = common.current_or_next_matchday(cfg, today)
    if is_today:
        return f"{cfg['short']} {entry_id}"
    if entry_id:
        return f"quiet — next: {entry_id} on {date_range}"
    return f"{cfg['short']}: no more calendar entries configured"


def fetch_events(sport_key: str, api_key: str) -> tuple[list, str | None]:
    """(events, x-requests-last) via the free events endpoint. Never raises —
    catches the SystemExit common.api_get would otherwise raise on an API
    error, since this script must always exit 0."""
    try:
        events, headers = common.list_events(sport_key, api_key)
        return events, headers.get("x-requests-last")
    except SystemExit as e:
        print(f"  [warn] events lookup failed: {e}", file=sys.stderr)
        return [], None


def upcoming_fixtures(events: list, now: datetime, hours: int) -> list:
    horizon = now + timedelta(hours=hours)
    out = [ev for ev in events
           if (t := _parse_dt(ev.get("commence_time"))) and now <= t <= horizon]
    out.sort(key=lambda e: e["commence_time"])
    return out


def missing_predictions(comp: str, fixtures: list) -> list:
    predicted = {(p.get("home_team"), p.get("away_team"))
                 for p in common.load_all_records(comp, "predictions", "predictions")}
    return [ev for ev in fixtures
            if (ev.get("home_team"), ev.get("away_team")) not in predicted]


def ungraded_predictions(comp: str, now: datetime) -> tuple[list, list]:
    """(api_gradeable, needs_web) — past-kickoff predictions with no completed
    result recorded locally yet, split by how old the kickoff is."""
    completed = {(s.get("home_team"), s.get("away_team"))
                 for s in common.load_all_records(comp, "scores", "matches")
                 if s.get("completed")}
    gradeable, needs_web = [], []
    for p in common.load_all_records(comp, "predictions", "predictions"):
        t = _parse_dt(p.get("commence_time"))
        if not t or t >= now:
            continue
        pair = (p.get("home_team"), p.get("away_team"))
        if pair in completed:
            continue
        age_days = (now - t).total_seconds() / 86400
        (gradeable if age_days <= GRADE_WINDOW_DAYS else needs_web).append(p)
    return gradeable, needs_web


def outrights_status(comp: str, cfg: dict, now: datetime) -> dict:
    present = bool(glob.glob(f"{common.data_dir(comp)}/outrights-*.json"))
    lock = _parse_dt(cfg.get("outrights_lock"))
    return {
        "present": present,
        "lock": cfg.get("outrights_lock"),
        "lock_passed": bool(lock and now >= lock),
    }


def build_report(comp: str, cfg: dict, now: datetime, hours: int, api_key: str | None) -> dict:
    today = now.strftime("%Y-%m-%d")
    calendar = calendar_line(cfg, today)
    outrights = outrights_status(comp, cfg, now)

    if not api_key:
        return {
            "comp": comp, "short": cfg["short"], "calendar": calendar,
            "fixtures_in_window": 0, "fixtures_missing_predictions": [],
            "ungraded_api_gradeable": 0, "ungraded_needs_web": 0,
            "outrights": outrights, "needs_full_run": False, "needs_maintenance": False,
            "credits_used": 0, "x_requests_last": None,
        }

    events, credits_last = fetch_events(cfg["sport_key"], api_key)
    fixtures = upcoming_fixtures(events, now, hours)
    missing = missing_predictions(comp, fixtures)
    gradeable, needs_web = ungraded_predictions(comp, now)

    return {
        "comp": comp,
        "short": cfg["short"],
        "calendar": calendar,
        "fixtures_in_window": len(fixtures),
        "fixtures_missing_predictions": [
            f"{ev.get('home_team')} vs {ev.get('away_team')} ({ev.get('commence_time')})"
            for ev in missing
        ],
        "ungraded_api_gradeable": len(gradeable),
        "ungraded_needs_web": len(needs_web),
        "outrights": outrights,
        "needs_full_run": bool(missing) or (not outrights["present"] and not outrights["lock_passed"]),
        "needs_maintenance": bool(gradeable) or bool(needs_web),
        "credits_used": 0,
        "x_requests_last": credits_last,
    }


def print_report(r: dict) -> None:
    print(f"\n=== {r['short']} ===")
    print(f"Calendar: {r['calendar']}")
    print(f"Fixtures in window: {r['fixtures_in_window']} "
          f"({len(r['fixtures_missing_predictions'])} without a prediction yet)")
    for line in r["fixtures_missing_predictions"]:
        print(f"  - {line}")
    print(f"Ungraded predictions: {r['ungraded_api_gradeable'] + r['ungraded_needs_web']} "
          f"({r['ungraded_api_gradeable']} API-gradeable, {r['ungraded_needs_web']} need web sources)")
    o = r["outrights"]
    state = "present" if o["present"] else "missing"
    if o["lock"]:
        lock_note = f"{'lock passed' if o['lock_passed'] else 'lock not yet passed'}, closes {o['lock']}"
    else:
        lock_note = "no lock configured"
    print(f"Outrights: {state} ({lock_note})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=48,
                     help="look-ahead window for upcoming fixtures (default 48)")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON output")
    args = ap.parse_args()

    api_key = os.environ.get("THE_ODDS_API_KEY")
    now = datetime.now(timezone.utc)
    if not api_key:
        print("THE_ODDS_API_KEY not set — cannot query even the free events "
              "endpoint; reporting calendar/local state only.", file=sys.stderr)

    registry = common.load_competitions()
    reports = [build_report(comp, cfg, now, args.hours, api_key) for comp, cfg in registry.items()]

    full_run = [r["short"] for r in reports if r["needs_full_run"]]
    maintenance = any(r["needs_maintenance"] for r in reports)
    if full_run:
        verdict = f"ACTION: full run for {', '.join(full_run)}"
    elif maintenance:
        verdict = "ACTION: maintenance only"
    else:
        verdict = "ACTION: nothing to do"

    last_values = [r["x_requests_last"] for r in reports if r["x_requests_last"] is not None]
    proof = f"credits used: 0 (x-requests-last={','.join(last_values) if last_values else 'n/a'})"
    print(proof, file=sys.stderr)

    if args.json:
        print(json.dumps({"generated_at": now.isoformat(), "competitions": reports,
                           "verdict": verdict}, indent=2))
    else:
        for r in reports:
            print_report(r)
        print(f"\n{verdict}")
        print(proof)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — this script must always exit 0
        print(f"[whats_on] unexpected error: {e}", file=sys.stderr)
    sys.exit(0)
