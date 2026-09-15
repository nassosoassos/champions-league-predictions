#!/usr/bin/env python3
"""
Shared helpers for the multi-competition prediction pipeline
(config/competitions.json is the registry of competitions).

Import from the other scripts via:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import common

so `python3 scripts/x.py` keeps working when run from the repo root.

Stdlib only.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

API_BASE = "https://api.the-odds-api.com/v4"
COMPETITIONS_PATH = "config/competitions.json"


def load_competitions() -> dict:
    """The competitions registry, keyed by short id ('ucl', 'uel', ...), in
    the order config/competitions.json lists them (its declared display
    order — never hardcode a competition list in a script)."""
    with open(COMPETITIONS_PATH) as f:
        data = json.load(f)
    return data["competitions"]


def data_dir(comp: str) -> str:
    return f"data/{comp}"


def data_path(comp: str, prefix: str, date: str) -> str:
    """e.g. data_path('uel', 'odds', '2026-09-16') -> 'data/uel/odds-2026-09-16.json'"""
    return f"{data_dir(comp)}/{prefix}-{date}.json"


def teams_path(comp: str, registry: dict | None = None) -> str:
    reg = registry if registry is not None else load_competitions()
    return reg[comp]["teams_file"]


def load_all_records(comp: str, prefix: str, key: str) -> list[dict]:
    """Every record under `key` across all data/<comp>/<prefix>-*.json files
    on disk, e.g. load_all_records('uel', 'predictions', 'predictions') or
    load_all_records('uel', 'scores', 'matches')."""
    out: list[dict] = []
    for path in sorted(glob.glob(f"{data_dir(comp)}/{prefix}-*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        out.extend(data.get(key, []))
    return out


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


def refuse_to_shrink(path: str, new_count: int, force: bool) -> bool:
    """True if the caller should skip writing `path` because the new fetch
    has fewer matches than what's already on disk and --force wasn't passed.
    Prints the same explanation the fetchers have always printed."""
    existing_count = existing_match_count(path)
    if existing_count is not None and new_count < existing_count and not force:
        print(f"\nrefusing to overwrite {path}: {existing_count} matches on "
              f"disk, {new_count} fetched — keeping existing file\n"
              f"(re-run with --force to overwrite)")
        return True
    return False


def api_get(path: str, api_key: str, **params) -> tuple[object, dict]:
    """GET {API_BASE}/{path}?apiKey=...&... -> (parsed_json, headers).

    `headers` carries the rate-limit fields The Odds API returns on every
    call (free or paid): x-requests-remaining, x-requests-used, x-requests-last.
    Prints the same "requests remaining" stderr line the fetchers have
    always printed, and exits (non-zero) with a clear message on HTTP/network
    errors — callers that must never exit non-zero (e.g. whats_on.py) should
    catch SystemExit around this call.
    """
    query = {"apiKey": api_key, **{k: v for k, v in params.items() if v is not None}}
    url = f"{API_BASE}/{path}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": "uefa-predictor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            headers = {
                "x-requests-remaining": resp.headers.get("x-requests-remaining"),
                "x-requests-used": resp.headers.get("x-requests-used"),
                "x-requests-last": resp.headers.get("x-requests-last"),
            }
            if headers["x-requests-remaining"] is not None:
                print(f"[odds-api] requests remaining: {headers['x-requests-remaining']} "
                      f"(used: {headers['x-requests-used']})", file=sys.stderr)
            return json.loads(resp.read().decode("utf-8")), headers
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"[odds-api] HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        sys.exit(f"[odds-api] network error: {e.reason}")


def list_events(sport_key: str, api_key: str) -> tuple[list, dict]:
    """FREE /v4/sports/{sport}/events endpoint — costs 0 credits regardless
    of how often it's called. Returns (events, headers); headers['x-requests-last']
    should read '0', proving no credits were spent."""
    return api_get(f"sports/{sport_key}/events", api_key)


def format_date_range(dates: list[str]) -> str:
    """['2026-09-08', '2026-09-09', '2026-09-10'] -> '8-10 Sep 2026';
    a single-date list formats as '27 Jan 2027'."""
    parsed = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    first, last = parsed[0], parsed[-1]
    if first.day == last.day and first.month == last.month and first.year == last.year:
        return first.strftime("%-d %b %Y")
    if first.month == last.month and first.year == last.year:
        return f"{first.day}-{last.day} {first.strftime('%b %Y')}"
    return f"{first.strftime('%-d %b')}-{last.strftime('%-d %b %Y')}"


def calendar_entries(comp_cfg: dict) -> list[tuple[str, list[str]]]:
    """All (id, dates) entries for a competition — league phase, knockouts,
    then the final — in chronological order."""
    entries = [(p["id"], p["dates"]) for p in comp_cfg.get("league_phase", [])]
    entries += [(k["id"], k["dates"]) for k in comp_cfg.get("knockouts", [])]
    final = comp_cfg.get("final")
    if final:
        entries.append(("Final", [final["date"]]))
    return entries


def current_or_next_matchday(comp_cfg: dict, today: str) -> tuple[str, str, bool]:
    """(id, formatted_date_range, is_today) for `today` (YYYY-MM-DD) against a
    competition's calendar: the entry containing today, or else the next
    upcoming one. ("", "", False) if the configured calendar has nothing left."""
    entries = calendar_entries(comp_cfg)
    for entry_id, dates in entries:
        if today in dates:
            return entry_id, format_date_range(dates), True
    for entry_id, dates in entries:
        if any(d >= today for d in dates):
            return entry_id, format_date_range(dates), False
    return "", "", False
