#!/usr/bin/env python3
"""
Build a self-contained dashboard.html from the project's data files.

Reads, for every competition in config/competitions.json (registry order):
    <teams_file>                     (the 36 clubs: short code, country, flag)
    data/<comp>/predictions-*.json   (agent-written: picks, confidence, depth, rationale, market)
    data/<comp>/scores-*.json        (actual final scores, for grading)
    data/<comp>/standings-*.json     (the official 36-row league table)
    data/<comp>/outrights-*.json     (season-long markets: winner, top 8, ...)
Writes:
    dashboard.html            (one file, no dependencies — just open it;
                               a tab per competition, deep-linkable as #<comp>)
    index.html                (copy for GitHub Pages)

Everything is baked into the HTML, so it works from file:// with no server, no
CDN and no fonts to fetch. Stdlib only — no pip install required.

Usage:
    python3 scripts/build_dashboard.py && open dashboard.html
"""
from __future__ import annotations

import glob
import json
import os
import re
from datetime import datetime, timezone

REGISTRY_PATH = "config/competitions.json"
DATA_ROOT = "data"
NUMBER_WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve")


def load_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


CREST_PATTERNS = {"solid", "stripes", "halves", "hoops", "sash"}
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def load_registry() -> tuple[str, dict]:
    """config/competitions.json -> (season, {comp_key: {...}}) in registry (display) order."""
    doc = load_json(REGISTRY_PATH)
    comps = doc.get("competitions")
    return str(doc.get("season") or ""), (comps if isinstance(comps, dict) else {})


def load_teams(path: str) -> dict:
    """A competition's teams file -> {name: [short, flag, country, colors, pattern]}.

    The list shape is what the render code indexes into ([0] short, [1] flag,
    [2] country, [3] colors, [4] pattern). A missing, malformed or mid-edit
    file degrades gracefully: colors/pattern fall back to None/"solid" per
    club rather than raising, so the dashboard still builds and the JS crest
    helper falls back to a neutral badge.
    """
    raw = load_json(path).get("teams") or {}
    out: dict[str, list] = {}
    if not isinstance(raw, dict):
        return out
    for name, info in raw.items():
        if not isinstance(info, dict):
            info = {}
        colors = info.get("colors")
        if not (
            isinstance(colors, list)
            and len(colors) == 2
            and all(isinstance(c, str) and _HEX_RE.match(c) for c in colors)
        ):
            colors = None
        pattern = info.get("pattern")
        if pattern not in CREST_PATTERNS:
            pattern = "solid"
        out[name] = [
            info.get("short") or (name or "")[:3].upper(),
            info.get("flag") or "",
            info.get("country") or "",
            colors,
            pattern,
        ]
    return out


def data_files(data_dir: str, kind: str) -> list[str]:
    """data/<comp>/<kind>-*.json, oldest first (the date is in the name)."""
    return sorted(glob.glob(os.path.join(data_dir, f"{kind}-*.json")))


def latest_scores(data_dir: str) -> dict:
    """Merge every scores file (oldest -> newest) -> {home|away: {...}}.

    fetch_scores.py only writes a rolling window (--days-from), so the newest
    file drops matches that finished a few days ago. With matchdays weeks
    apart that window is guaranteed to miss earlier rounds, so we merge across
    all files and never let a later not-yet-completed snapshot clobber an
    already-completed result.
    """
    out = {}
    for path in data_files(data_dir, "scores"):
        for m in load_json(path).get("matches", []):
            key = f"{m.get('home_team')}|{m.get('away_team')}"
            prev = out.get(key)
            if prev and prev.get("completed") and not m.get("completed"):
                continue
            out[key] = m
    return out


def latest_outrights(data_dir: str) -> dict:
    """Most recent outrights file -> {lock_deadline, markets:[...]}."""
    files = data_files(data_dir, "outrights")
    return load_json(files[-1]) if files else {}


def latest_standings(data_dir: str) -> dict:
    """Most recent standings file -> {as_of, matchdays_played, table:[...]}."""
    files = data_files(data_dir, "standings")
    return load_json(files[-1]) if files else {}


def all_predictions(data_dir: str) -> list[dict]:
    """Every prediction we've ever made, newest day first, de-duped by match.

    The matchday label lives at file level (`matchday: "MD1"`); stamp it onto
    each prediction that doesn't carry its own, so the page can group by round
    without re-deriving it from dates.
    """
    days = []
    for path in reversed(data_files(data_dir, "predictions")):
        date = os.path.basename(path)[len("predictions-"):-len(".json")]
        data = load_json(path)
        preds = data.get("predictions") or data.get("matches") or []
        md = data.get("matchday")
        if not preds:
            continue
        for p in preds:
            if md and not p.get("matchday"):
                p["matchday"] = md
        days.append({"date": date, "matchday": md, "predictions": preds})
    return days


def implied_result(scoreline: str) -> str | None:
    """The 1X2 result a scoreline implies, in home-away order. None if unparseable."""
    try:
        h, a = (int(x) for x in (scoreline or "").split("-"))
    except (ValueError, AttributeError):
        return None
    return "home" if h > a else ("away" if a > h else "draw")


def scoreline_usable(p: dict) -> bool:
    """False when a prediction's scoreline contradicts its own pick.

    Scorelines are home-away order, so `pick: away` with `scoreline: "1-0"` is
    self-contradictory and we can't tell which half was meant. Such a scoreline
    must never be credited an exact hit just because the string happens to match
    the final score — that would reward a call that named the wrong winner.
    """
    imp = implied_result(p.get("scoreline"))
    return imp is not None and imp == p.get("pick")


def _bucket() -> dict:
    return {"graded": 0, "correct": 0, "exact": 0}


def _favourite(market: dict) -> str | None:
    """The result ('home'/'draw'/'away') the market rates most likely, or None.

    Used to separate research's contribution from a selection effect: deep
    picks are drawn from the tightest three-way lines, so their hit rate is
    never comparable to a blind bet on the market favourite unless that
    favourite is measured on the exact same matches.
    """
    probs = {k: v for k, v in (market or {}).items() if isinstance(v, (int, float))}
    return max(probs, key=probs.get) if probs else None


def grade(days: list[dict], scores: dict) -> dict:
    """Attach actual results to predictions and compute an accuracy summary.

    The deep/quick split answers the one question the headline number can't:
    are the researched cards actually beating the picks we derived from the
    market in thirty seconds? Both buckets are derived here, never hardcoded.

    Alongside it, `deep_fav_correct`/`deep_graded` answer the fairer question:
    on the matches that got research, did the researched pick beat a blind
    bet on the market favourite for those SAME matches — not quick picks,
    which are drawn from a different (easier) pool of matches entirely.
    `deep_deviations`/`deep_dev_correct` isolate the picks where research
    actually disagreed with the market, since agreement with the favourite
    can't demonstrate an edge either way.
    """
    seen = set()
    correct = exact = graded = 0
    conf_right, conf_wrong = [], []
    depth_split = {"deep": _bucket(), "quick": _bucket()}
    deep_graded = deep_fav_correct = deep_deviations = deep_dev_correct = 0

    for day in days:
        for p in day["predictions"]:
            key = f"{p.get('home_team')}|{p.get('away_team')}"
            sc = scores.get(key)
            p["actual"] = None
            if sc and sc.get("completed") and sc.get("result"):
                p["actual"] = {
                    "final_score": sc.get("final_score"),
                    "result": sc.get("result"),
                    "pick_hit": p.get("pick") == sc.get("result"),
                    "score_hit": scoreline_usable(p)
                    and (p.get("scoreline") or "").replace(" ", "")
                    == (sc.get("final_score") or "").replace(" ", ""),
                }
                if key not in seen:
                    seen.add(key)
                    graded += 1
                    # Only the pick we last published counts, and `days` is
                    # newest-first, so the first sighting is the live one.
                    bucket = depth_split.get(p.get("depth"))
                    if bucket is not None:
                        bucket["graded"] += 1
                    if p.get("depth") == "deep":
                        deep_graded += 1
                        fav = _favourite(p.get("market"))
                        if fav is not None:
                            if fav == sc.get("result"):
                                deep_fav_correct += 1
                            if p.get("pick") != fav:
                                deep_deviations += 1
                                if p["actual"]["pick_hit"]:
                                    deep_dev_correct += 1
                    if p["actual"]["pick_hit"]:
                        correct += 1
                        if bucket is not None:
                            bucket["correct"] += 1
                        if isinstance(p.get("confidence"), (int, float)):
                            conf_right.append(p["confidence"])
                    else:
                        if isinstance(p.get("confidence"), (int, float)):
                            conf_wrong.append(p["confidence"])
                    if p["actual"]["score_hit"]:
                        exact += 1
                        if bucket is not None:
                            bucket["exact"] += 1

    def avg(xs):
        return round(sum(xs) / len(xs), 1) if xs else None

    for b in depth_split.values():
        b["hit_rate"] = round(100 * b["correct"] / b["graded"]) if b["graded"] else None
    edge = None
    if depth_split["deep"]["hit_rate"] is not None and depth_split["quick"]["hit_rate"] is not None:
        edge = depth_split["deep"]["hit_rate"] - depth_split["quick"]["hit_rate"]

    return {
        "graded": graded,
        "correct": correct,
        "hit_rate": round(100 * correct / graded) if graded else None,
        "exact": exact,
        "conf_right": avg(conf_right),
        "conf_wrong": avg(conf_wrong),
        "depth": depth_split,
        "depth_edge": edge,
        "deep_graded": deep_graded,
        "deep_fav_correct": deep_fav_correct,
        "deep_deviations": deep_deviations,
        "deep_dev_correct": deep_dev_correct,
    }


def _int(v, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def league_table(standings: dict, teams: dict, preseason_note: str) -> dict:
    """The 36-row league phase table, ready to render.

    The official UEFA table is authoritative — we never recompute it from our
    partial score history. Before the first matchday there is no file yet, so
    fall back to the 36 clubs at zero rather than an empty box. With no teams
    file either, `rows` is empty and the note explains why.
    """
    raw = standings.get("table") or []
    rows = []
    for i, r in enumerate(raw):
        if not isinstance(r, dict):
            continue
        gf, ga = _int(r.get("gf")), _int(r.get("ga"))
        gd = r.get("gd")
        rows.append({
            "rank": _int(r.get("rank"), i + 1),
            "team": r.get("team"),
            "played": _int(r.get("played")),
            "won": _int(r.get("won")),
            "drawn": _int(r.get("drawn")),
            "lost": _int(r.get("lost")),
            "gf": gf,
            "ga": ga,
            "gd": gf - ga if gd is None else _int(gd),
            "points": _int(r.get("points")),
        })
    if rows:
        rows.sort(key=lambda r: r["rank"])
        return {
            "provisional": False,
            "as_of": standings.get("as_of"),
            "matchdays_played": _int(standings.get("matchdays_played")),
            "rows": rows,
            "note": None,
        }

    rows = [{"rank": None, "team": t, "played": 0, "won": 0, "drawn": 0,
             "lost": 0, "gf": 0, "ga": 0, "gd": 0, "points": 0}
            for t in sorted(teams)]
    return {"provisional": True, "as_of": None, "matchdays_played": 0,
            "rows": rows, "note": preseason_note}


def rounds(comp: dict) -> list[dict]:
    """The registry calendar as [{id, name, dates}] — league phase, then knockouts."""
    out = []
    for r in comp.get("league_phase") or []:
        m = re.fullmatch(r"MD(\d+)", str(r.get("id") or ""))
        out.append({"id": r.get("id"), "dates": sorted(r.get("dates") or []),
                    "name": f"Matchday {m.group(1)}" if m else r.get("id")})
    for r in comp.get("knockouts") or []:
        out.append({"id": r.get("id"), "dates": sorted(r.get("dates") or []),
                    "name": r.get("name") or r.get("id")})
    return out


def preseason_note(comp: dict, n_clubs: int, today: str) -> str:
    """The provisional table's caption, derived from the registry calendar."""
    phase = comp.get("league_phase") or []
    first = min((d for r in phase for d in (r.get("dates") or [])), default=None)
    try:
        day = datetime.strptime(first or "", "%Y-%m-%d")
        verb = "started" if first < today else "starts"
        start = f"League phase {verb} {day.day} {day.strftime('%B')}"
    except ValueError:
        start = "League phase dates not published yet"
    if not n_clubs:
        return (f"Club list not loaded yet ({comp.get('teams_file') or 'no teams file'} "
                f"is missing or empty). {start}.")
    count = NUMBER_WORDS[len(phase)] if len(phase) < len(NUMBER_WORDS) else str(len(phase))
    return f"{start} — {n_clubs} clubs, one table, {count} matchdays. Nothing played yet."


def postmortem(days: list[dict], scores: dict) -> dict | None:
    """Measure the method against itself.

    Two questions the headline hit rate can't answer: did deviating from the
    market favourite add anything, and did the scoreline guesses beat a
    brain-dead fixed guess? Everything here is derived, never hardcoded — if a
    late result lands, the numbers move with it.
    """
    rows = []
    for day in reversed(days):  # oldest first; keep the pick we actually stood on
        for p in day["predictions"]:
            key = f"{p.get('home_team')}|{p.get('away_team')}"
            sc = scores.get(key)
            if not (sc and sc.get("completed") and sc.get("result")):
                continue
            mkt = p.get("market") or {}
            if not mkt:
                continue
            try:
                ph, pa = (int(x) for x in (p.get("scoreline") or "").split("-"))
                ah, aa = (int(x) for x in (sc.get("final_score") or "").split("-"))
            except (ValueError, AttributeError):
                continue
            rows.append({
                "pick": p.get("pick"), "res": sc["result"],
                "fav": max(mkt, key=mkt.get), "favp": mkt[max(mkt, key=mkt.get)],
                "ph": ph, "pa": pa, "ah": ah, "aa": aa,
                "ok": scoreline_usable(p),
                "depth": p.get("depth"),
                "match": f"{p.get('home_team')} v {p.get('away_team')}",
            })
    # de-dupe: one row per fixture, keeping the last (final) pick we published
    dedup = {}
    for r in rows:
        dedup[r["match"]] = r
    rows = list(dedup.values())
    if not rows:
        return None

    def points(ph, pa, res, r, pick=None):
        """Kicktipp-style: 4 exact score / 3 goal difference / 2 correct winner.

        `pick` overrides the winner implied by the scoreline — used for our own
        rows, where the recorded pick is what we actually stood behind.
        """
        pr = pick or ("home" if ph > pa else ("away" if pa > ph else "draw"))
        exact = ph == r["ah"] and pa == r["aa"]
        gd = (ph - pa) == (r["ah"] - r["aa"])
        win = pr == res
        return (4 if exact else (3 if (gd and win) else (2 if win else 0)),
                exact, gd, win)

    # A scoreline that contradicts its own pick is unusable: it can't earn an
    # exact or goal-difference credit, and the pick decides the winner.
    ours = [points(r["ph"], r["pa"], r["res"], r, pick=r["pick"]) if r["ok"]
            else (2 if r["pick"] == r["res"] else 0, False, False,
                  r["pick"] == r["res"])
            for r in rows]
    baselines = []
    for gh, ga in ((2, 1), (1, 0), (2, 0), (1, 1)):
        b = [points(gh, ga, r["res"], r) for r in rows]
        baselines.append({
            "label": f"{gh}-{ga} every match",
            "pts": sum(x[0] for x in b), "exact": sum(x[1] for x in b),
            "gd": sum(x[2] for x in b), "win": sum(x[3] for x in b),
        })
    baselines.sort(key=lambda b: -b["pts"])

    devs = [r for r in rows if r["pick"] != r["fav"]]
    return {
        "n": len(rows),
        "ours": {"pts": sum(x[0] for x in ours), "exact": sum(x[1] for x in ours),
                 "gd": sum(x[2] for x in ours), "win": sum(x[3] for x in ours)},
        "baselines": baselines,
        "followed": sum(1 for r in rows if r["pick"] == r["fav"]),
        "blind_fav": sum(1 for r in rows if r["fav"] == r["res"]),
        "deviations": [{"match": r["match"], "pick": r["pick"], "fav": r["fav"],
                        "favp": r["favp"], "res": r["res"], "depth": r["depth"],
                        "hit": r["pick"] == r["res"]} for r in devs],
        "dev_hits": sum(1 for r in devs if r["pick"] == r["res"]),
        "draws_actual": sum(1 for r in rows if r["res"] == "draw"),
        "draws_picked": sum(1 for r in rows if r["pick"] == "draw"),
        "draws_hit": sum(1 for r in rows if r["pick"] == "draw" == r["res"]),
    }


def build_comp(key: str, comp: dict, teams: dict, today: str) -> dict:
    """One competition's whole page block, loaded from data/<key>/."""
    data_dir = os.path.join(DATA_ROOT, key)
    scores = latest_scores(data_dir)
    days = all_predictions(data_dir)
    return {
        "name": comp.get("name") or key.upper(),
        "short": comp.get("short") or key.upper(),
        "final": comp.get("final") or {},
        "rounds": rounds(comp),
        "days": days,
        "summary": grade(days, scores),
        "outrights": latest_outrights(data_dir),
        "table": league_table(latest_standings(data_dir), teams,
                              preseason_note(comp, len(teams), today)),
        "teams": teams,
        "postmortem": postmortem(days, scores),
    }


def build_data(season: str, registry: dict, teams_by_comp: dict) -> dict:
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    return {
        "generated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
        "season": season,
        "order": list(registry),
        "comps": {key: build_comp(key, comp, teams_by_comp[key], today)
                  for key, comp in registry.items()},
    }


HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prediction Desk</title>
<style>
  :root{
    --bg:#04060f; --bg2:#080b1b; --panel:#0d1229; --panel2:#131a3a;
    --line:#212a55; --line2:#2f3a72;
    --ink:#eef2ff; --muted:#98a2cf; --faint:#69719f;
    --star:#9dbcff; --star2:#4a7bf0; --silver:#cfd9f7;
    --star-rgb:157,188,255; --star2-rgb:74,123,240; --glow3-rgb:46,78,168; --starfield:.55;
    --home:#6ea8ff; --draw:#8b95c4; --away:#ff7fa3;
    --gold:#f2cd7a; --win:#57e0a5; --loss:#ff6f8e;
    --f-ui:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,system-ui,sans-serif;
    --f-mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,"Cascadia Mono",Consolas,monospace;
    --shadow:0 24px 55px -30px rgba(0,0,0,.95);
  }
  /* Per-competition identity: only the accent moves; ground, panels and layout
     stay put. The :root values above are the Champions League midnight look. */
  html[data-comp="uel"]{
    --star:#ffb46b; --star2:#e8741c; --silver:#f1dccb;
    --star-rgb:255,180,107; --star2-rgb:232,116,28; --glow3-rgb:150,70,20; --starfield:.2;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{margin:0; background:var(--bg); color:var(--ink); font-family:var(--f-ui);
    font-size:15px; line-height:1.55; -webkit-font-smoothing:antialiased; overflow-x:hidden;}
  /* stadium glow: floodlights over a midnight ground */
  body::before{content:""; position:fixed; inset:0; z-index:-2; pointer-events:none;
    background:
      radial-gradient(1100px 620px at 50% -14%, rgba(var(--star2-rgb),.20), transparent 62%),
      radial-gradient(760px 520px at 92% 6%, rgba(var(--star-rgb),.08), transparent 60%),
      radial-gradient(680px 460px at 2% 22%, rgba(var(--glow3-rgb),.12), transparent 62%),
      var(--bg);}
  /* starfield — pure CSS, tiles so it covers any page height */
  body::after{content:""; position:fixed; inset:0; z-index:-1; pointer-events:none; opacity:var(--starfield);
    background-repeat:repeat; background-size:820px 620px;
    background-image:
      radial-gradient(1.5px 1.5px at 6% 12%, rgba(255,255,255,.85), transparent 60%),
      radial-gradient(1.2px 1.2px at 23% 41%, rgba(207,217,247,.7), transparent 60%),
      radial-gradient(1px 1px at 38% 8%, rgba(255,255,255,.6), transparent 60%),
      radial-gradient(1.6px 1.6px at 52% 63%, rgba(var(--star-rgb),.75), transparent 60%),
      radial-gradient(1.1px 1.1px at 67% 26%, rgba(255,255,255,.55), transparent 60%),
      radial-gradient(1.4px 1.4px at 81% 71%, rgba(207,217,247,.6), transparent 60%),
      radial-gradient(1px 1px at 94% 34%, rgba(255,255,255,.5), transparent 60%),
      radial-gradient(1.3px 1.3px at 14% 78%, rgba(var(--star-rgb),.55), transparent 60%),
      radial-gradient(1px 1px at 45% 91%, rgba(255,255,255,.45), transparent 60%),
      radial-gradient(1.2px 1.2px at 73% 96%, rgba(207,217,247,.5), transparent 60%),
      radial-gradient(1px 1px at 88% 15%, rgba(255,255,255,.4), transparent 60%);}
  .wrap{max-width:1150px; margin:0 auto; padding:0 22px 96px;}
  a{color:inherit;}

  /* ---- header ---- */
  header{position:sticky; top:0; z-index:40; margin:0 -22px; padding:15px 22px 13px;
    background:linear-gradient(180deg, rgba(4,6,15,.97), rgba(4,6,15,.86) 68%, transparent);
    backdrop-filter:blur(9px); display:flex; align-items:center; justify-content:space-between;
    gap:16px; flex-wrap:wrap;}
  .brand{display:flex; align-items:center; gap:14px; min-width:0;}
  .crest{width:46px; height:46px; flex:none; filter:drop-shadow(0 6px 16px rgba(var(--star2-rgb),.5));}
  /* the starball mark is the Champions League's alone; everything else gets the neutral mark */
  html[data-comp="ucl"] .crest.neutral, html:not([data-comp="ucl"]) .crest.starball{display:none;}

  /* ---- competition tabs ---- */
  .comptabs{display:flex; gap:4px; padding:4px; border-radius:12px; background:var(--panel);
    border:1px solid var(--line);}
  .comptabs:empty{display:none;}
  .comptab{font-family:var(--f-ui); font-weight:700; font-size:13px; color:var(--muted);
    background:none; border:none; padding:7px 14px; border-radius:9px; cursor:pointer;
    display:flex; align-items:center; gap:8px; white-space:nowrap; transition:.18s;}
  .comptab:hover{color:var(--ink);}
  .comptab:focus-visible{outline:2px solid var(--star); outline-offset:1px;}
  .comptab.on{background:var(--panel2); color:var(--ink); box-shadow:inset 0 -2px 0 var(--star);}
  .comptab .abbr{display:none;}
  .comptab b{font-family:var(--f-mono); font-size:11px; font-weight:700; color:var(--star);}

  /* ---- club crests: generated colour badges, not real club emblems ---- */
  .crestbadge{width:28px; height:28px; flex:none; vertical-align:middle; overflow:visible;}
  .crestbadge.sm{width:20px; height:20px;}
  .crestbadge.lg{width:34px; height:34px;}
  .wordmark{line-height:1.05; min-width:0;}
  .wordmark .l1{font-family:var(--f-mono); font-size:10.5px; letter-spacing:3.2px;
    text-transform:uppercase; color:var(--star);}
  .wordmark .l2{font-size:25px; font-weight:800; letter-spacing:-.4px;}
  .hgen{font-family:var(--f-mono); font-size:11px; color:var(--muted); text-align:right;
    display:flex; flex-direction:column; align-items:flex-end; gap:6px;}
  .livepill{display:inline-flex; align-items:center; gap:8px; font-family:var(--f-mono);
    font-size:12px; color:var(--ink); background:var(--panel); border:1px solid var(--line);
    padding:5px 12px; border-radius:999px;}
  .livepill b{color:var(--star);}
  .dot{width:7px; height:7px; border-radius:50%; background:var(--star);
    box-shadow:0 0 0 0 rgba(var(--star-rgb),.6); animation:pulse 2.4s infinite;}
  @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(var(--star-rgb),.55)}70%{box-shadow:0 0 0 8px rgba(var(--star-rgb),0)}100%{box-shadow:0 0 0 0 rgba(var(--star-rgb),0)}}

  /* ---- stat ribbon ---- */
  .ribbon{display:flex; flex-wrap:wrap; margin:22px 0 12px; border:1px solid var(--line);
    border-radius:16px; overflow:hidden; box-shadow:var(--shadow);
    background:linear-gradient(180deg,var(--panel),var(--bg2));}
  .rcell{flex:1 1 0; min-width:132px; padding:16px 18px; border-right:1px solid var(--line);}
  .rcell:last-child{border-right:none;}
  .rcell .v{font-size:32px; font-weight:800; line-height:1; letter-spacing:-1px;}
  .rcell .v small{font-size:16px; font-weight:600; color:var(--muted); letter-spacing:0;}
  .rcell .k{font-family:var(--f-mono); font-size:10px; letter-spacing:1.5px; text-transform:uppercase;
    color:var(--muted); margin-top:8px;}
  .rcell.hero .v{color:var(--star);}

  /* ---- deep vs quick: is the research earning its keep? ---- */
  .splitwrap{border:1px solid var(--line); border-radius:16px; padding:16px 18px 18px;
    background:linear-gradient(180deg,var(--panel),var(--bg2)); box-shadow:var(--shadow); margin-bottom:12px;}
  .splith{font-family:var(--f-mono); font-size:10.5px; letter-spacing:1.6px; text-transform:uppercase;
    color:var(--star); margin-bottom:13px; display:flex; align-items:center; gap:11px;}
  .splith::after{content:""; flex:1; height:1px; background:var(--line);}
  .split{display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:11px;}
  .sp{background:var(--panel2); border:1px solid var(--line2); border-radius:13px; padding:14px 16px;}
  .sp .spk{font-family:var(--f-mono); font-size:10px; letter-spacing:1.3px; text-transform:uppercase;
    color:var(--muted); display:flex; align-items:center; gap:7px;}
  .sp .spv{font-size:33px; font-weight:800; letter-spacing:-1px; line-height:1.15;}
  .sp .spm{font-family:var(--f-mono); font-size:11px; color:var(--faint);}
  .sp.deep{border-color:rgba(var(--star-rgb),.42);}
  .sp.deep .spv{color:var(--star);}
  .sp.quick .spv{color:var(--silver);}
  .sp.edge .spv.up{color:var(--win);} .sp.edge .spv.down{color:var(--loss);}
  .sp.edge .spv.flat{color:var(--muted);}

  /* ---- outrights ---- */
  .outs{display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:11px; margin-bottom:6px;}
  .out{background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px 16px;
    display:flex; flex-direction:column; gap:7px; position:relative; overflow:hidden;}
  .out::before{content:""; position:absolute; inset:0 0 auto 0; height:1px;
    background:linear-gradient(90deg,transparent,rgba(var(--star-rgb),.5),transparent);}
  .out .ok{font-family:var(--f-mono); font-size:10px; letter-spacing:1.4px; text-transform:uppercase;
    color:var(--muted);}
  .out .op{font-size:21px; font-weight:800; letter-spacing:-.3px; line-height:1.15;}
  .out .oc{font-family:var(--f-mono); font-size:11px; color:var(--gold); letter-spacing:1.5px;}
  .out .onote{font-size:12px; color:var(--muted); line-height:1.5;}
  .out .oalt{font-family:var(--f-mono); font-size:10.5px; color:var(--faint);}
  .chips{display:flex; flex-wrap:wrap; gap:6px;}
  .chip{font-size:12px; font-weight:600; background:var(--panel2); border:1px solid var(--line2);
    border-radius:999px; padding:3px 10px; display:inline-flex; align-items:center; gap:5px;}
  .chip.hit{border-color:rgba(87,224,165,.45); color:var(--win); background:rgba(87,224,165,.1);}
  .chip.miss{border-color:rgba(255,111,142,.4); color:var(--loss); background:rgba(255,111,142,.08);}

  /* ---- view switch ---- */
  .switch{display:inline-flex; gap:4px; margin:30px 0 8px; padding:5px; border-radius:13px;
    background:var(--panel); border:1px solid var(--line);}
  .switch button{font-family:var(--f-ui); font-weight:700; font-size:13px; letter-spacing:.2px;
    color:var(--muted); background:none; border:none; padding:9px 18px; border-radius:9px;
    cursor:pointer; display:flex; align-items:center; gap:7px; transition:.18s;}
  .switch button:hover{color:var(--ink);}
  .switch button.on{background:linear-gradient(150deg,var(--star),var(--star2)); color:#050914;}

  .secline{display:flex; align-items:baseline; justify-content:space-between; gap:14px;
    flex-wrap:wrap; margin:24px 0 14px;}
  .secline h2{font-size:20px; font-weight:800; letter-spacing:-.3px; margin:0;}
  .sectools{display:flex; align-items:center; gap:18px;}
  .toolbtn{font-family:var(--f-mono); font-size:12px; color:var(--muted); cursor:pointer;
    border-bottom:1px dashed transparent; transition:.15s; white-space:nowrap;}
  .toolbtn:hover{color:var(--star); border-color:rgba(var(--star-rgb),.45);}

  /* ---- matchday rail ---- */
  .rail{display:flex; gap:8px; overflow-x:auto; padding:3px 2px 11px; margin:0 -2px;
    scrollbar-width:thin;}
  .rail::-webkit-scrollbar{height:5px;}
  .rail::-webkit-scrollbar-thumb{background:var(--line2); border-radius:9px;}
  .mdchip{flex:none; cursor:pointer; background:var(--panel); border:1px solid var(--line);
    border-radius:11px; padding:8px 13px; display:flex; flex-direction:column; gap:2px;
    transition:.16s; min-width:78px;}
  .mdchip:hover{border-color:var(--star2); transform:translateY(-2px);}
  .mdchip.on{border-color:var(--star); background:linear-gradient(180deg,rgba(var(--star2-rgb),.22),var(--panel));}
  .mdchip .cl{font-size:13px; font-weight:800; letter-spacing:.2px; white-space:nowrap;}
  .mdchip .cs{font-family:var(--f-mono); font-size:9.5px; color:var(--muted); white-space:nowrap;}
  .mdchip.on .cs{color:var(--star);}

  /* ---- matchday sections ---- */
  .mdsec{border:1px solid var(--line); border-radius:16px; margin-bottom:12px; overflow:hidden;
    background:linear-gradient(180deg,rgba(19,26,58,.55),rgba(8,11,27,.35));}
  .mdsec>summary{list-style:none; cursor:pointer; padding:14px 18px; display:flex;
    align-items:center; gap:13px; flex-wrap:wrap;}
  .mdsec>summary::-webkit-details-marker{display:none;}
  .mdsec>summary:hover{background:rgba(var(--star-rgb),.04);}
  .mdsec>summary:focus-visible{outline:2px solid var(--star); outline-offset:-3px;}
  .mdsec .mdname{font-size:18px; font-weight:800; letter-spacing:-.2px;}
  .mdsec .mdsub{font-family:var(--f-mono); font-size:11px; color:var(--muted);}
  .mdsec .mdcount{font-family:var(--f-mono); font-size:10px; letter-spacing:1.2px; text-transform:uppercase;
    color:var(--faint); border:1px solid var(--line2); border-radius:999px; padding:2px 9px;}
  .mdsec .chev{margin-left:auto; color:var(--muted); font-size:12px; font-family:var(--f-mono);
    transition:.2s;}
  .mdsec[open] .chev{transform:rotate(90deg);}
  .mdsec[open]>summary{border-bottom:1px solid var(--line);}
  .mdbody{padding:14px 16px 18px; display:flex; flex-direction:column; gap:12px;}
  .daydiv{font-family:var(--f-mono); font-size:10.5px; letter-spacing:1.6px; text-transform:uppercase;
    color:var(--star); display:flex; align-items:center; gap:11px; margin:6px 2px 0;}
  .daydiv:first-child{margin-top:0;}
  .daydiv::after{content:""; flex:1; height:1px; background:var(--line);}

  /* ---- deep match cards ---- */
  .match{background:linear-gradient(180deg,var(--panel),var(--bg2)); border:1px solid var(--line);
    border-radius:17px; overflow:hidden; box-shadow:var(--shadow);
    opacity:0; transform:translateY(9px); animation:rise .45s cubic-bezier(.2,.7,.3,1) forwards;}
  @keyframes rise{to{opacity:1; transform:none;}}
  .sb{display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:12px;
    padding:18px 20px 16px;
    background:radial-gradient(130% 150% at 50% -50%, rgba(var(--star2-rgb),.16), transparent 62%);}
  .side{display:flex; flex-direction:column; gap:4px; min-width:0;}
  .side.away{align-items:flex-end; text-align:right;}
  .side .fl{font-size:26px; line-height:1;}
  .side .name{font-size:21px; font-weight:800; letter-spacing:-.4px; line-height:1.1;}
  .side .sub{font-family:var(--f-mono); font-size:10px; color:var(--muted); letter-spacing:1.1px;}
  .mid{text-align:center; display:flex; flex-direction:column; align-items:center; gap:6px; padding:0 4px;}
  .mid .vs{font-family:var(--f-mono); font-size:12px; color:var(--faint); letter-spacing:2px;}
  .mid .fin{font-size:30px; font-weight:800; letter-spacing:-.5px;}
  .mid .kick{font-family:var(--f-mono); font-size:10px; color:var(--muted); white-space:nowrap;}
  .mdchipsm{font-family:var(--f-mono); font-size:9.5px; letter-spacing:1.2px; color:var(--star);
    border:1px solid rgba(var(--star-rgb),.32); border-radius:6px; padding:1px 7px; cursor:default;}

  .callrow{display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;
    padding:11px 20px; background:var(--panel2); border-top:1px solid var(--line);
    border-bottom:1px solid var(--line);}
  .call{display:flex; align-items:center; gap:10px; font-size:13px;}
  .call .lab{font-family:var(--f-mono); font-size:9.5px; letter-spacing:1.5px; color:var(--faint);
    text-transform:uppercase;}
  .call .pk{font-size:16px; font-weight:800; letter-spacing:-.2px;}
  .call .sl{font-family:var(--f-mono); font-size:13px; color:var(--ink); background:var(--bg);
    border:1px solid var(--line2); border-radius:6px; padding:2px 8px;}
  .conf{display:flex; gap:3px; align-items:center;}
  .conf .lab{font-family:var(--f-mono); font-size:9.5px; letter-spacing:1px; color:var(--faint); margin-right:3px;}
  .conf i{width:11px; height:11px; border-radius:3px; background:var(--line2); display:inline-block;}
  .conf i.f{background:var(--gold); box-shadow:0 0 7px -1px rgba(242,205,122,.5);}

  .tag{font-family:var(--f-mono); font-size:9px; letter-spacing:1.4px; text-transform:uppercase;
    border-radius:5px; padding:2px 7px; white-space:nowrap;}
  .tag.deep{color:var(--star); border:1px solid rgba(var(--star-rgb),.4); background:rgba(var(--star2-rgb),.14);}
  .tag.quick{color:var(--faint); border:1px solid var(--line2);}

  .body{padding:15px 20px 18px;}
  .bar{display:flex; height:29px; border-radius:9px; overflow:hidden; border:1px solid var(--line);
    background:var(--bg);}
  .bar>div{display:flex; align-items:center; justify-content:center; font-family:var(--f-mono);
    font-size:11px; font-weight:700; color:#050914; min-width:0; transition:.3s;}
  .bar .h{background:var(--home);} .bar .d{background:var(--draw);} .bar .a{background:var(--away);}
  .leg{display:flex; justify-content:space-between; gap:10px; margin:9px 1px 0; font-family:var(--f-mono);
    font-size:10.5px; color:var(--muted);}
  .leg i{width:9px; height:9px; border-radius:2px; display:inline-block; margin-right:5px; vertical-align:1px;}
  .rat{color:#d3dbf5; margin:15px 0 0; font-size:14px;}
  .flag{margin-top:12px; font-size:13px; color:#f8ead0; background:rgba(242,205,122,.07);
    border-left:3px solid var(--gold); padding:9px 12px; border-radius:0 8px 8px 0;}
  .flag b{color:var(--gold); font-family:var(--f-mono); font-size:10px; letter-spacing:1px;
    display:block; margin-bottom:2px;}
  .result{display:flex; align-items:center; gap:9px; margin-top:13px; flex-wrap:wrap;
    padding-top:13px; border-top:1px dashed var(--line2);}
  .result .rl{font-family:var(--f-mono); font-size:11px; color:var(--muted); letter-spacing:.5px;}
  .result .rs{font-size:18px; font-weight:800; letter-spacing:-.2px;}
  .badge{font-family:var(--f-mono); font-weight:700; padding:3px 9px; border-radius:7px; font-size:11px;
    letter-spacing:.5px; white-space:nowrap;}
  .hit{background:rgba(87,224,165,.14); color:var(--win); border:1px solid rgba(87,224,165,.35);}
  .miss{background:rgba(255,111,142,.14); color:var(--loss); border:1px solid rgba(255,111,142,.35);}
  .src{margin-top:14px; display:flex; flex-wrap:wrap; gap:8px;}
  .src a{font-family:var(--f-mono); font-size:11px; color:var(--home); text-decoration:none;
    border:1px solid var(--line2); border-radius:7px; padding:4px 9px; transition:.15s; background:var(--bg);}
  .src a:hover{border-color:var(--home); color:var(--ink);}
  .why{margin-top:13px; border-top:1px dashed var(--line2); padding-top:11px;}
  .why>summary{list-style:none; cursor:pointer; display:inline-flex; align-items:center; gap:8px;
    font-family:var(--f-mono); font-size:11px; letter-spacing:1px; text-transform:uppercase;
    color:var(--muted); user-select:none; transition:.15s;}
  .why>summary::-webkit-details-marker{display:none;}
  .why>summary:hover{color:var(--star);}
  .why[open]>summary{color:var(--ink);}
  .why>summary .chev{color:var(--star); transition:transform .2s; display:inline-block;}
  .why[open]>summary .chev{transform:rotate(90deg);}

  /* ---- quick picks: compact, deliberately quieter ---- */
  .qcard{display:grid; grid-template-columns:minmax(0,1.6fr) minmax(96px,.85fr) auto;
    gap:14px; align-items:center; padding:11px 16px; border:1px solid var(--line);
    border-left:3px solid var(--line2); border-radius:12px; background:rgba(13,18,41,.55);
    opacity:0; transform:translateY(9px); animation:rise .45s cubic-bezier(.2,.7,.3,1) forwards;}
  .qcard .qt{display:flex; align-items:center; gap:8px; min-width:0; flex-wrap:wrap;}
  .qcard .qt .nm{font-size:14.5px; font-weight:700; white-space:nowrap; overflow:hidden;
    text-overflow:ellipsis;}
  .qcard .qt .v{font-family:var(--f-mono); font-size:10px; color:var(--faint);}
  .qcard .qmeta{font-family:var(--f-mono); font-size:10px; color:var(--faint); width:100%;}
  .qbar{display:flex; height:8px; border-radius:99px; overflow:hidden; border:1px solid var(--line);
    background:var(--bg);}
  .qbar .h{background:var(--home);} .qbar .d{background:var(--draw);} .qbar .a{background:var(--away);}
  .qbarw{display:flex; flex-direction:column; gap:5px;}
  .qbarw .qlg{font-family:var(--f-mono); font-size:9.5px; color:var(--faint);
    display:flex; justify-content:space-between; gap:6px;}
  .qcall{display:flex; align-items:center; gap:9px; flex-wrap:wrap; justify-content:flex-end;}
  .qcall .pk{font-size:13.5px; font-weight:800;}
  .qcall .sl{font-family:var(--f-mono); font-size:12px; background:var(--bg);
    border:1px solid var(--line2); border-radius:6px; padding:1px 7px;}

  /* ---- league table ---- */
  .lt{border:1px solid var(--line); border-radius:17px; overflow:hidden; box-shadow:var(--shadow);
    background:linear-gradient(180deg,var(--panel),var(--bg2));}
  .lthdr{padding:16px 18px 13px; display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;
    border-bottom:1px solid var(--line);}
  .lthdr .t{font-size:19px; font-weight:800; letter-spacing:-.3px;}
  .lthdr .s{font-family:var(--f-mono); font-size:11px; color:var(--muted);}
  .ltlegend{display:flex; flex-wrap:wrap; gap:8px; padding:12px 18px; border-bottom:1px solid var(--line);}
  .ltlegend span{font-family:var(--f-mono); font-size:10px; letter-spacing:.8px; color:var(--muted);
    display:inline-flex; align-items:center; gap:6px;}
  .ltlegend i{width:10px; height:10px; border-radius:3px; display:inline-block;}
  .ltnote{padding:13px 18px; font-size:13px; color:var(--gold); background:rgba(242,205,122,.06);
    border-bottom:1px solid var(--line);}
  table.ltbl{width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums;}
  table.ltbl th{font-family:var(--f-mono); font-size:9.5px; letter-spacing:1.2px; text-transform:uppercase;
    color:var(--faint); text-align:right; padding:10px 8px; font-weight:400;
    border-bottom:1px solid var(--line);}
  table.ltbl th.l{text-align:left;}
  table.ltbl td{padding:9px 8px; text-align:right; font-size:13.5px; border-bottom:1px solid rgba(33,42,85,.55);}
  table.ltbl td.rk{font-family:var(--f-mono); font-size:12px; color:var(--muted); text-align:center;
    width:42px; border-left:3px solid transparent;}
  table.ltbl td.club{text-align:left; font-weight:600;}
  table.ltbl td.club .fl{margin-right:9px; font-size:15px;}
  table.ltbl td.club .short{display:none; font-family:var(--f-mono); font-size:12.5px;}
  table.ltbl td.pts{font-weight:800; font-size:15px; padding-right:16px;}
  table.ltbl tr[data-t]{cursor:pointer; transition:.13s;}
  table.ltbl tr[data-t]:hover td{background:rgba(var(--star-rgb),.08);}
  table.ltbl tr.b1 td{background:linear-gradient(90deg, rgba(var(--star2-rgb),.17), rgba(var(--star2-rgb),.03));}
  table.ltbl tr.b1 td.rk{border-left-color:var(--star); color:var(--star);}
  table.ltbl tr.b2 td{background:rgba(255,255,255,.014);}
  table.ltbl tr.b2 td.rk{border-left-color:var(--line2);}
  table.ltbl tr.b3 td{background:rgba(255,111,142,.055);}
  table.ltbl tr.b3 td.rk{border-left-color:rgba(255,111,142,.55); color:rgba(255,143,168,.85);}
  table.ltbl tr.cut td{padding:0; background:none; border-bottom:none;}
  .cutline{display:flex; align-items:center; gap:11px; padding:9px 14px; flex-wrap:wrap;
    border-top:2px solid var(--star2); border-bottom:1px solid var(--line);
    background:linear-gradient(90deg, rgba(var(--star2-rgb),.16), transparent);}
  .cutline.out{border-top:2px dashed rgba(255,111,142,.6);
    background:linear-gradient(90deg, rgba(255,111,142,.12), transparent);}
  .cutline .cw{font-family:var(--f-mono); font-size:10px; letter-spacing:1.5px; text-transform:uppercase;
    color:var(--star); font-weight:700;}
  .cutline.out .cw{color:var(--loss);}
  .cutline .cx{font-family:var(--f-mono); font-size:10px; color:var(--faint); letter-spacing:.6px;}

  .focusbar{display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:14px;
    padding:12px 16px; border:1px solid var(--line2); border-radius:13px; background:var(--panel2);}
  .focusbar .fname{font-size:17px; font-weight:800; letter-spacing:-.3px;}
  .focusbar .frec{font-family:var(--f-mono); font-size:11px; color:var(--muted);}
  .focusbar .fclear{margin-left:auto; font-family:var(--f-mono); font-size:11px; color:var(--star);
    cursor:pointer; border-bottom:1px dashed rgba(var(--star-rgb),.45);}

  .empty{text-align:center; color:var(--muted); padding:56px 20px; border:1px dashed var(--line2);
    border-radius:17px; font-family:var(--f-mono); font-size:13px;}
  .hidden{display:none !important;}

  /* ---- post-mortem ---- */
  .pm{border:1px solid var(--line); border-radius:17px; margin:14px 0 4px;
    background:linear-gradient(180deg,var(--panel),var(--bg2)); box-shadow:var(--shadow); overflow:hidden;}
  .pm summary{list-style:none; cursor:pointer; padding:18px 22px; display:flex;
    align-items:center; gap:14px; flex-wrap:wrap;}
  .pm summary::-webkit-details-marker{display:none;}
  .pm summary:focus-visible{outline:2px solid var(--star); outline-offset:-3px;}
  .pm .pmttl{font-size:20px; font-weight:800; letter-spacing:-.3px;}
  .pm .pmsub{font-family:var(--f-mono); font-size:11.5px; color:var(--muted);}
  .pm .chev{margin-left:auto; color:var(--muted); font-size:13px; font-family:var(--f-mono); transition:.2s;}
  .pm[open] .chev{transform:rotate(90deg);}
  .pmbody{padding:2px 22px 24px; display:flex; flex-direction:column; gap:22px;}
  .pmbody p{margin:0; color:var(--muted); font-size:14px; max-width:64ch;}
  .pmbody p b{color:var(--ink); font-weight:700;}
  .pmh{font-family:var(--f-mono); font-size:10.5px; letter-spacing:1.6px; text-transform:uppercase;
    color:var(--star); margin:0 0 10px; padding-bottom:8px; border-bottom:1px solid var(--line);}
  .verdict{display:flex; align-items:center; gap:20px; flex-wrap:wrap;
    background:var(--panel2); border:1px solid var(--line2); border-radius:14px; padding:17px 20px;}
  .verdict .big{font-size:44px; font-weight:800; line-height:.95; letter-spacing:-1.5px;}
  .verdict .big.good{color:var(--win);} .verdict .big.bad{color:var(--loss);}
  .verdict .vtx{font-size:14px; color:var(--muted); max-width:48ch;}
  .verdict .vtx b{color:var(--ink);}
  .ab{display:flex; flex-direction:column; gap:11px;}
  .abrow{display:grid; grid-template-columns:minmax(120px,1.3fr) 1fr auto; gap:14px; align-items:center;}
  .abrow .abl{font-size:13px; color:var(--muted);}
  .abrow.win .abl{color:var(--ink); font-weight:600;}
  .abtrack{height:9px; border-radius:999px; background:var(--panel2); border:1px solid var(--line);
    overflow:hidden;}
  .abfill{height:100%; border-radius:999px; background:var(--faint);}
  .abrow.win .abfill{background:linear-gradient(90deg,var(--star2),var(--star));}
  .abv{font-family:var(--f-mono); font-size:12.5px; color:var(--muted);
    font-variant-numeric:tabular-nums; white-space:nowrap;}
  .abrow.win .abv{color:var(--star);}
  .devs{display:flex; flex-direction:column;}
  .devrow{display:flex; gap:12px; align-items:baseline; flex-wrap:wrap; padding:9px 0;
    border-bottom:1px solid var(--line); font-family:var(--f-mono); font-size:12px;}
  .devrow:first-child{border-top:1px solid var(--line);}
  .devrow .dm{flex:1 1 200px; color:var(--ink);}
  .devrow .dv{font-weight:700;}
  .devrow .dv.miss{color:var(--loss);} .devrow .dv.hit{color:var(--win);}
  .devrow .dd{flex:1 1 100%; color:var(--faint); font-size:11.5px;}
  .pmnote{font-family:var(--f-mono); font-size:11px; color:var(--faint); line-height:1.65;
    border-top:1px solid var(--line); padding-top:14px; max-width:72ch;}

  footer{margin-top:34px; padding-top:18px; border-top:1px solid var(--line);
    font-family:var(--f-mono); font-size:11px; color:var(--faint); line-height:1.7;}

  @media (max-width:760px){
    .comptabs{order:3; width:100%;}
    .comptab{flex:1; justify-content:center;}
    .comptab .full{display:none;} .comptab .abbr{display:inline;}
    table.ltbl .opt{display:none;}
    table.ltbl td.club .full{display:none;}
    table.ltbl td.club .short{display:inline;}
    .qcard{grid-template-columns:1fr; gap:9px;}
    .qcall{justify-content:flex-start;}
  }
  @media (max-width:560px){
    .wrap{padding:0 14px 70px;} header{margin:0 -14px; padding:13px 14px 11px;}
    .wordmark .l2{font-size:20px;} .crest{width:38px; height:38px;}
    .rcell .v{font-size:26px;} .rcell{min-width:110px; padding:13px 14px;}
    .side .name{font-size:16px;} .side .fl{font-size:21px;} .mid .fin{font-size:24px;}
    .sb{padding:15px 14px 13px; gap:8px;} .callrow{padding:10px 14px;} .body{padding:13px 14px 15px;}
    .verdict .big{font-size:34px;}
    .abrow{grid-template-columns:1fr auto;}
    .abrow .abtrack{grid-column:1/-1; order:3;}
    .mdbody{padding:12px 10px 15px;}
    table.ltbl td{padding:8px 5px; font-size:12.5px;} table.ltbl th{padding:9px 5px;}
  }
</style></head>
<body><div class="wrap">
  <header>
    <div class="brand">
      <svg class="crest starball" viewBox="0 0 64 64" aria-hidden="true">
        <defs>
          <radialGradient id="cg" cx="50%" cy="28%" r="78%">
            <stop offset="0" stop-color="#2b3f8f"/><stop offset="1" stop-color="#070b1c"/>
          </radialGradient>
          <polygon id="st" fill="#dbe6ff"
            points="0,-5 1.18,-1.62 4.76,-1.55 1.9,0.62 2.94,4.05 0,2 -2.94,4.05 -1.9,0.62 -4.76,-1.55 -1.18,-1.62"/>
        </defs>
        <circle cx="32" cy="32" r="30" fill="url(#cg)" stroke="#4a7bf0" stroke-opacity=".6"/>
        <circle cx="32" cy="32" r="24" fill="none" stroke="#9dbcff" stroke-opacity=".18"/>
        <use href="#st" x="32" y="11"/><use href="#st" x="46.85" y="17.15"/>
        <use href="#st" x="53" y="32"/><use href="#st" x="46.85" y="46.85"/>
        <use href="#st" x="32" y="53"/><use href="#st" x="17.15" y="46.85"/>
        <use href="#st" x="11" y="32"/><use href="#st" x="17.15" y="17.15"/>
      </svg>
      <!-- neutral mark: a plain dial in the active accent, deliberately not any competition's logo -->
      <svg class="crest neutral" viewBox="0 0 64 64" aria-hidden="true">
        <circle cx="32" cy="32" r="30" fill="#0b0f22" style="stroke:var(--star2)" stroke-opacity=".7"/>
        <circle cx="32" cy="32" r="21" fill="none" style="stroke:var(--star)" stroke-opacity=".35"
          stroke-width="1.5" stroke-dasharray="3 4.33"/>
        <circle cx="32" cy="32" r="11" fill="none" style="stroke:var(--star)" stroke-width="2.5"/>
        <circle cx="32" cy="32" r="3.5" style="fill:var(--star)"/>
      </svg>
      <div class="wordmark">
        <div class="l1" id="wordmark">&#8203;</div>
        <div class="l2">Prediction Desk</div>
      </div>
    </div>
    <nav class="comptabs" id="comptabs" role="tablist" aria-label="Competition"></nav>
    <div class="hgen">
      <span class="livepill"><span class="dot"></span>HIT RATE <b id="hr">&#8212;</b></span>
      <span id="gen"></span>
    </div>
  </header>

  <div class="ribbon" id="stats"></div>
  <div id="splitwrap"></div>
  <div class="outs" id="outrights"></div>
  <div id="pmwrap"></div>

  <div class="switch" id="switch">
    <button data-v="fixtures" class="on">Fixtures</button>
    <button data-v="table">League table</button>
  </div>

  <div id="tableView" class="hidden">
    <div class="lt" id="ltable"></div>
  </div>

  <div id="fixturesView">
    <div class="rail" id="rail"></div>
    <div class="secline">
      <h2 id="mhdr">Match predictions</h2>
      <div class="sectools">
        <a class="toolbtn" id="expandall">&#10530; expand analysis</a>
        <a class="toolbtn" id="openall">&#9776; open every matchday</a>
      </div>
    </div>
    <div id="mdwrap"></div>
  </div>

  <footer>
    Built from the prediction, score, standings and outright files in this repo &#183; every number
    on this page is recomputed on each build, nothing is hardcoded.<br>
    Predictions for fun, not betting advice.
  </footer>
</div>
<script>
const DATA = __DATA__;
const ORDER = (DATA.order||[]).filter(k => DATA.comps && DATA.comps[k]);
const PICK = {home:"Home win", draw:"Draw", away:"Away win"};
const MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const DOW = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
const pct = x => Math.round((x||0)*100);
const pad = n => String(n).padStart(2,"0");
// Every team lookup is scoped to one competition (C = DATA.comps[key]); the
// clubs registries are never merged.
const teamInfo = (C, t) => (C.teams||{})[t] || [];
const code = (C, t) => teamInfo(C, t)[0] || (t||"").slice(0,3).toUpperCase();
const flag = (C, t) => teamInfo(C, t)[1] || "";
const esc = s => String(s==null?"":s).replace(/[&<>"]/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

/* ---------- club crest: a generated colour badge, not a real emblem ----------
   Two kit colours plus the 3-letter club code, filled per a simple pattern.
   Deliberately abstract — no attempt to reproduce any club's actual crest. */
const CREST_HEX = /^#[0-9a-f]{6}$/i;
const CREST_SLATE = ["#2a3358", "#171d38"];
let crestSeq = 0;

function crestColors(C, t){
  const c = teamInfo(C, t)[3];
  if(Array.isArray(c) && c.length===2 && CREST_HEX.test(c[0]) && CREST_HEX.test(c[1])) return c;
  return null;
}
const CREST_PATTERNS = new Set(["solid","stripes","halves","hoops","sash"]);
const crestPattern = (C, t) => { const p = teamInfo(C, t)[4]; return CREST_PATTERNS.has(p) ? p : "solid"; };

// relative luminance (WCAG), 0 (black) .. 1 (white)
function crestLuminance(hex){
  const n = parseInt(hex.slice(1), 16);
  const chan = v => { const c = v/255; return c<=0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4); };
  return 0.2126*chan((n>>16)&255) + 0.7152*chan((n>>8)&255) + 0.0722*chan(n&255);
}
// pick near-black or near-white text for contrast against a given fill colour
const crestTextColor = hex => crestLuminance(hex) > 0.5 ? "#0a0e1f" : "#f5f7ff";

function crestFill(pattern, c1, c2){
  const S = 28;
  switch(pattern){
    case "stripes": {
      const n = 5, w = S/n; let s = "";
      for(let i=0;i<n;i++) s += `<rect x="${(i*w).toFixed(2)}" y="0" width="${w.toFixed(2)}" height="${S}" fill="${i%2?c2:c1}"/>`;
      return s;
    }
    case "halves":
      return `<rect x="0" y="0" width="${S/2}" height="${S}" fill="${c1}"/>` +
             `<rect x="${S/2}" y="0" width="${S/2}" height="${S}" fill="${c2}"/>`;
    case "hoops": {
      const n = 4, h = S/n; let s = "";
      for(let i=0;i<n;i++) s += `<rect x="0" y="${(i*h).toFixed(2)}" width="${S}" height="${h.toFixed(2)}" fill="${i%2?c2:c1}"/>`;
      return s;
    }
    case "sash":
      return `<rect x="0" y="0" width="${S}" height="${S}" fill="${c1}"/>` +
             `<polygon points="0,0 11,0 ${S},17 ${S},${S} 17,${S} 0,11" fill="${c2}"/>`;
    case "solid":
    default:
      return `<rect x="0" y="0" width="${S}" height="${S}" fill="${c1}"/>`;
  }
}

function crest(C, name, sizeCls){
  const label = esc(name || code(C, name) || "?");
  const short = esc((code(C, name) || "?").slice(0,3).toUpperCase());
  const colors = crestColors(C, name);
  const [c1, c2] = colors || CREST_SLATE;
  const pattern = colors ? crestPattern(C, name) : "solid";
  const uid = "crc" + (crestSeq++);
  // Multi-tone patterns (stripes/hoops/halves/sash) put the monogram across
  // alternating light/dark bands, so it needs its own solid backing plate —
  // the darker club colour at high opacity — with the text contrast picked
  // against THAT plate, not against c1. Solid badges stay plate-free.
  const patterned = pattern !== "solid";
  const plateColor = crestLuminance(c1) <= crestLuminance(c2) ? c1 : c2;
  const textFill = patterned ? crestTextColor(plateColor) : crestTextColor(c1);
  const plate = patterned
    ? `<rect x="1" y="7" width="26" height="14" rx="3" fill="${plateColor}" fill-opacity=".92"/>`
    : "";
  // The .sm badge (20px) shrinks the whole viewBox proportionally, so a
  // font-size tuned for the 28px default becomes too small to read. Bump the
  // font-size and tighten letter-spacing for .sm so three letters stay legible.
  const sm = sizeCls === "sm";
  const fontSize = sm ? "12.5" : "9.5";
  const letterSpacing = sm ? "0" : ".2";
  return `<svg class="crestbadge ${sizeCls||''}" viewBox="0 0 28 28" width="28" height="28"
    role="img" aria-label="${label}" focusable="false">
    <clipPath id="${uid}"><rect x="1" y="1" width="26" height="26" rx="6"/></clipPath>
    <g clip-path="url(#${uid})">${crestFill(pattern, c1, c2)}${plate}</g>
    <rect x="1" y="1" width="26" height="26" rx="6" fill="none" stroke="rgba(255,255,255,.24)"/>
    <text x="14" y="18" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,'SF Mono',Menlo,monospace"
      font-size="${fontSize}" font-weight="800" letter-spacing="${letterSpacing}" fill="${textFill}">${short}</text>
  </svg>`;
}

// local calendar date (YYYY-MM-DD) of a kickoff, so the day headings agree
// with the local kick times shown on the cards.
const localDate = iso => { const dt = new Date(iso);
  return `${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}`; };

function prettyDate(ds){
  const [y,m,d] = String(ds||"").split("-").map(Number);
  if(!y || !m || !d) return String(ds||"");
  const dt = new Date(y, m-1, d);
  return `${DOW[dt.getDay()]} ${d} ${MON[m-1]}`;
}

// Per competition, derived once at boot and stored on the block as C._matches
// and C._groups.
function prepare(C){
  // one entry per real fixture (latest forecast wins — C.days is newest-first),
  // tagged with the local calendar date it is played on, sorted chronologically.
  const seen = {};
  const matches = [];
  (C.days||[]).forEach(d => (d.predictions||[]).forEach(p => {
    const k = p.home_team + "|" + p.away_team;
    if(seen[k]) return; seen[k] = 1;
    const o = {...p, _pub:d.date};
    o._date = o.commence_time ? localDate(o.commence_time) : d.date;
    o._deep = o.depth !== "quick";
    matches.push(o);
  }));
  matches.sort((a,b) => (a.commence_time||a._date).localeCompare(b.commence_time||b._date));

  // matchday -> section. A league phase round is played over a few days, then
  // goes quiet for weeks, so the round is the unit that matters; fall back to
  // the date when a predictions file carries no matchday label.
  const groups = [];
  const idx = {};
  matches.forEach(p => {
    const key = p.matchday || ("date:" + p._date);
    if(idx[key] == null){ idx[key] = groups.length;
      groups.push({key, md:p.matchday || null, items:[], dates:[]}); }
    groups[idx[key]].items.push(p);
  });
  groups.forEach(g => {
    g.dates = [...new Set(g.items.map(x => x._date))].sort();
    g.start = g.dates[0]; g.end = g.dates[g.dates.length-1];
    g.label = g.md || prettyDate(g.start);
    g.span = g.dates.length > 1 ? `${prettyDate(g.start)} \\u2013 ${prettyDate(g.end)}`
                                : prettyDate(g.start);
    g.graded = g.items.filter(p => p.actual).length;
    g.hits = g.items.filter(p => p.actual && p.actual.pick_hit).length;
  });
  C._matches = matches;
  C._groups = groups;
}

// The registry round that is under way or next up, as human copy for the
// empty fixtures board, e.g. "Matchday 1 starts Wednesday 16 September".
function roundCopy(C){
  const today = localDate(Date.now());
  const r = (C.rounds||[]).find(x => (x.dates||[]).length && x.dates[x.dates.length-1] >= today);
  const long = ds => { const [y,m,d] = ds.split("-").map(Number);
    return new Date(y, m-1, d).toLocaleDateString("en-GB", {weekday:"long", day:"numeric", month:"long"}); };
  if(!r){
    const f = (C.final||{}).date;
    return f ? `The season is over \\u2014 the final was played on ${long(f)}.` : "";
  }
  return r.dates[0] > today ? `${r.name} starts ${long(r.dates[0])}.`
                            : `${r.name} is under way (until ${long(r.dates[r.dates.length-1])}).`;
}

const confBlocks = (c, lab) => {
  const n = c||0;
  let s = lab ? `<span class="lab">CONF</span>` : "";
  for(let i=1;i<=5;i++) s += `<i class="${i<=n?'f':''}"></i>`;
  return `<span class="conf" title="confidence ${n}/5">${s}</span>`;
};
const pickColor = p => p==="home" ? "var(--home)" : p==="away" ? "var(--away)" : "var(--draw)";

/* ---------- summary ribbon ---------- */
function renderStats(s){
  const hrEl = document.getElementById("hr");
  if(!s.graded){
    document.getElementById("stats").innerHTML =
      '<div class="rcell"><div class="v">\\u2014</div><div class="k">No graded matches yet</div></div>';
    hrEl.textContent = "\\u2014"; return;
  }
  hrEl.textContent = (s.hit_rate!=null ? s.hit_rate+"%" : "\\u2014");
  const cells = [
    ["hero", (s.hit_rate!=null ? s.hit_rate : "\\u2014"), "%", "Hit rate"],
    ["", s.correct, "<small>/"+s.graded+"</small>", "Correct picks"],
    ["", s.exact, "", "Exact scores"],
    ["", (s.conf_right ?? "\\u2014"), "", "Avg conf \\u00b7 right"],
    ["", (s.conf_wrong ?? "\\u2014"), "", "Avg conf \\u00b7 wrong"],
  ];
  document.getElementById("stats").innerHTML = cells.map(([cls,v,suf,k]) =>
    `<div class="rcell ${cls}"><div class="v">${v}${suf||""}</div><div class="k">${k}</div></div>`).join("");
}

/* ---------- deep vs quick: is the research earning its keep? ----------
   The fair test is not deep-vs-quick (quick picks are drawn from a
   different, easier pool \\u2014 the market's 85%+ favourites). It's: on the
   SAME matches that got research, did the researched pick beat a blind bet
   on the market favourite? That comparison lives in deep_graded /
   deep_fav_correct / deep_deviations / deep_dev_correct, computed once in
   Python (grade()) and never re-derived here. */
function renderSplit(s){
  const el = document.getElementById("splitwrap");
  const dg = s.deep_graded || 0;
  const q = (s.depth||{}).quick || {};
  if(!dg && !q.graded){ el.innerHTML = ""; return; }

  const deep = (s.depth||{}).deep || {};
  const researchedRate = dg ? Math.round(100*(deep.correct||0)/dg) : null;
  const favCorrect = s.deep_fav_correct || 0;
  const favRate = dg ? Math.round(100*favCorrect/dg) : null;
  const edge = (researchedRate!=null && favRate!=null) ? researchedRate - favRate : null;
  const devN = s.deep_deviations || 0;
  const devHits = s.deep_dev_correct || 0;

  const cell = (cls, key, rate, meta, sub) => `<div class="sp ${cls}"><div class="spk">${key}</div>
    <div class="spv">${rate==null ? "\\u2014" : rate+"%"}</div>
    <div class="spm">${dg ? meta : "nothing graded yet"}</div>
    <div class="spm">${sub}</div></div>`;

  const researched = cell("deep", "Researched picks", researchedRate,
    `${deep.correct||0}/${dg} correct`, "full preview, team news, sources");
  const favourite = cell("quick", "Market favourite, same matches", favRate,
    `${favCorrect}/${dg} correct`, "blind bet on the shortest price, no research");

  const edgeCls = edge==null ? "flat" : (edge>0 ? "up" : (edge<0 ? "down" : "flat"));
  const edgeVal = edge==null ? "\\u2014" : (edge>0 ? "+"+edge : String(edge));
  const trend = edge>0 ? "the reading is paying for itself"
    : edge<0 ? "the market-derived picks are ahead" : "dead level so far";
  const caption = !dg ? ""
    : devN === 0
      ? "Research hasn't moved a pick off the favourite yet, so the edge is zero by "
        + "construction \\u2014 it only becomes measurable when a researched pick "
        + "disagrees with the market."
      : `Research changed ${devN} pick${devN===1?"":"s"}; ${devHits} of them were right. ${trend}.`;
  const edgeHtml = `<div class="sp edge"><div class="spk">Research edge</div>
    <div class="spv ${edgeCls}">${edgeVal}${edge==null?"":"<span style='font-size:15px'>pts</span>"}</div>
    <div class="spm">${dg ? "researched minus favourite, percentage points" : "needs a graded deep pick"}</div>
    <div class="spm">${caption}</div></div>`;

  const quickLine = q.graded
    ? `<div class="spm" style="margin-top:11px">Quick picks: ${q.hit_rate}% (${q.correct}/${q.graded})
       \\u2014 not a fair benchmark: researched matches are chosen from the tightest lines.</div>`
    : "";

  el.innerHTML = `<div class="splitwrap">
    <div class="splith">Is the research earning its keep?</div>
    <div class="split">${researched}${favourite}${edgeHtml}</div>
    ${quickLine}</div>`;
}

/* ---------- season-long outright markets ---------- */
// A single-pick outright can hold a club ("winner", "dark_horse") or a
// player ("top_scorer", e.g. "Kylian Mbapp\\u00e9 (Real Madrid)"). Only render a
// crest when the pick IS a club, or names one in parentheses \\u2014 never derive
// a fake club code from an arbitrary player string.
function outrightCrest(C, pick){
  if(!pick) return "";
  if(teamInfo(C, pick).length) return crest(C, pick, 'sm');
  const m = /\\(([^()]+)\\)\\s*$/.exec(pick);
  if(m && teamInfo(C, m[1]).length) return crest(C, m[1], 'sm');
  return "";
}

function renderOutrights(C){
  const o = C.outrights || {};
  const el = document.getElementById("outrights");
  const ms = (o.markets||[]).filter(m => m && (m.pick || (m.picks||[]).length));
  if(!ms.length){ el.innerHTML = ""; return; }
  el.innerHTML = ms.map(m => {
    const r = m.result || null;
    const multi = Array.isArray(m.picks);
    const actual = r && Array.isArray(r.actual) ? r.actual : null;
    let pickHtml, res = "";
    if(multi){
      pickHtml = `<div class="chips">${m.picks.map(p => {
        let cls = "";
        if(actual) cls = actual.indexOf(p) >= 0 ? "hit" : "miss";
        const mark = cls ? (cls==="hit" ? " \\u2713" : " \\u2717") : "";
        return `<span class="chip ${cls}">${crest(C,p,'sm')} ${esc(p)}${mark}</span>`;
      }).join("")}</div>`;
      if(r){
        const of = r.of != null ? r.of : m.picks.length;
        const hits = r.hits != null ? r.hits
          : (actual ? m.picks.filter(p => actual.indexOf(p) >= 0).length : 0);
        const good = of ? hits/of >= 0.5 : false;
        res = `<div><span class="badge ${good?'hit':'miss'}">${hits}/${of} right</span></div>`;
      }
    } else {
      pickHtml = `<div class="op">${outrightCrest(C,m.pick)} ${esc(m.pick)}</div>`;
      if(r){
        const hit = !!r.correct;
        res = `<div><span class="badge ${hit?'hit':'miss'}">${hit?'\\u2713':'\\u2717'} ${esc(r.actual)}</span></div>`;
      }
    }
    const stars = m.confidence
      ? `<div class="oc">${"\\u2605".repeat(m.confidence)}${"\\u2606".repeat(Math.max(0,5-m.confidence))}</div>`
      : "";
    const alt = (m.alternatives||[]).length
      ? `<div class="oalt">also considered: ${esc(m.alternatives.join(" \\u00b7 "))}</div>` : "";
    return `<div class="out">
      <div class="ok">${esc(m.question || m.key || "market")}</div>
      ${pickHtml}${stars}
      ${m.note ? `<div class="onote">${esc(m.note)}</div>` : ""}
      ${alt}${res}</div>`;
  }).join("");
}

/* ---------- post-mortem: honest audit of the method ---------- */
function renderPostmortem(pm){
  const el = document.getElementById("pmwrap");
  if(!pm || !pm.n){ el.innerHTML = ""; return; }

  // Did overruling the betting market pay?
  const devN = pm.deviations.length;
  const devGood = devN ? (pm.dev_hits / devN) >= 0.5 : false;
  const verdict = devN
    ? `<div class="verdict">
         <div class="big ${devGood?'good':'bad'}">${pm.dev_hits}/${devN}</div>
         <div class="vtx">Times the research overruled the betting market &mdash; and how
           often that was <b>right</b>. The other <b>${pm.followed}</b> picks simply backed
           the market favourite.</div>
       </div>`
    : "";

  // Blind-favourite control: what if we'd never read a preview?
  const diff = pm.blind_fav - pm.ours.win;
  const ctrl = `<p>Backing the market favourite in all <b>${pm.n}</b> matches without reading a
    single preview would have returned <b>${pm.blind_fav}</b> correct winners.
    We got <b>${pm.ours.win}</b> &mdash; ${diff>0 ? `<b>${diff} fewer</b>. The qualitative layer
    was a net cost.` : diff===0 ? `exactly the same. The qualitative layer added nothing.`
    : `<b>${-diff} more</b>.`}</p>`;

  // Scoreline craft vs fixed-guess baselines
  const all = [{label:"Our submitted picks", ...pm.ours, us:true}, ...pm.baselines];
  const max = Math.max(...all.map(b => b.pts)) || 1;
  const bars = all.map(b => `
    <div class="abrow ${b.us?'win':''}">
      <div class="abl">${esc(b.label)}</div>
      <div class="abtrack"><div class="abfill" style="width:${100*b.pts/max}%"></div></div>
      <div class="abv">${b.pts} pts \\u00b7 ${b.exact} exact</div>
    </div>`).join("");

  const devs = devN ? `
    <div>
      <div class="pmh">Every deviation, in full</div>
      <div class="devs">${pm.deviations.map(d => `
        <div class="devrow">
          <span class="dm">${esc(d.match)}</span>
          <span class="tag ${d.depth==='quick'?'quick':'deep'}">${d.depth==='quick'?'quick':'deep'}</span>
          <span class="dv ${d.hit?'hit':'miss'}">${d.hit?'\\u2713 hit':'\\u2717 miss'}</span>
          <span class="dd">picked ${PICK[d.pick]||d.pick} \\u00b7 market said ${PICK[d.fav]||d.fav}
            ${Math.round((d.favp||0)*100)}% \\u00b7 finished ${PICK[d.res]||d.res}</span>
        </div>`).join("")}</div>
    </div>` : "";

  el.innerHTML = `
  <details class="pm">
    <summary>
      <span class="pmttl">Did any of this work?</span>
      <span class="pmsub">an honest audit of ${pm.n} predictions</span>
      <span class="chev">\\u276F</span>
    </summary>
    <div class="pmbody">
      ${verdict}
      ${ctrl}
      <div>
        <div class="pmh">Where the points actually came from</div>
        ${bars}
        <p style="margin-top:12px">Scored 4 / 3 / 2 for exact score, goal difference and correct
          winner &mdash; highest tier only. The gap over a fixed guess is <b>scoreline craft</b>:
          matching the shape of the score to how strong the market made the favourite.</p>
      </div>
      ${devs}
      <div>
        <div class="pmh">The draw blind spot that wasn't</div>
        <p><b>${pm.draws_actual}</b> matches finished level. We predicted a draw
          <b>${pm.draws_picked}</b> times and got <b>${pm.draws_hit}</b>. That looks like a flaw,
          but a draw is rarely the single most likely outcome even when it is a common result
          overall &mdash; so under-picking draws is correct, and feels wrong all season.</p>
      </div>
      <div class="pmnote">
        All figures recomputed from the prediction and score files on every build &mdash; nothing here
        is hardcoded. The 4/3/2 scheme is an assumption for comparison; other weightings move the
        totals but not the direction. Predictions for fun, not betting advice.
      </div>
    </div>
  </details>`;
}

/* ---------- league table ---------- */
function renderTable(C){
  const t = C.table || {};
  const rows = t.rows || [];
  const el = document.getElementById("ltable");
  if(!rows.length){
    el.innerHTML = `<div class="empty">${esc(t.note || "No league table yet.")}</div>`; return;
  }
  const prov = !!t.provisional;
  // Bands/cutlines only mean something once a full round is complete. A
  // missing/non-numeric matchdays_played (hand-written file) must degrade to
  // "round in progress", never be treated as complete.
  const mdPlayed = Number(t.matchdays_played);
  const mdValid = Number.isInteger(mdPlayed) && mdPlayed >= 0;
  const roundComplete = !prov && mdValid && mdPlayed >= 1;
  const cut = (cls, word, tail) =>
    `<tr class="cut"><td colspan="10"><div class="cutline ${cls}">
       <span class="cw">${word}</span><span class="cx">${tail}</span></div></td></tr>`;

  let body = "";
  rows.forEach((r, i) => {
    const rank = r.rank != null ? r.rank : i+1;
    const band = roundComplete ? (rank<=8 ? "b1" : (rank<=24 ? "b2" : "b3")) : "";
    const gd = (r.gd>0 ? "+" : "") + r.gd;
    body += `<tr class="${band}" data-t="${esc(r.team)}" title="show this club's predictions">
      <td class="rk">${prov ? "\\u00b7" : rank}</td>
      <td class="club">${crest(C,r.team,'sm')} <span class="fl">${flag(C,r.team)}</span
        ><span class="full">${esc(r.team)}</span><span class="short">${esc(code(C,r.team))}</span></td>
      <td>${r.played}</td>
      <td class="opt">${r.won}</td><td class="opt">${r.drawn}</td><td class="opt">${r.lost}</td>
      <td class="opt">${r.gf}</td><td class="opt">${r.ga}</td>
      <td>${gd}</td><td class="pts">${r.points}</td></tr>`;
    if(roundComplete && rank===8)  body += cut("", "Round of 16",
      "\\u2191 top 8 go straight through \\u00b7 \\u2193 knockout play-off");
    if(roundComplete && rank===24) body += cut("out", "Eliminated below",
      "\\u2191 9\\u201324 into the two-legged play-off \\u00b7 \\u2193 no European football after January");
  });

  const sub = prov ? "not started"
    : `after ${t.matchdays_played||0} matchday${(t.matchdays_played||0)===1?'':'s'}`
      + (t.as_of ? ` \\u00b7 as of ${esc(t.as_of)}` : "");

  // The band legend only applies once ranks mean something: either the
  // preseason placeholder (prov, unchanged — bands/cutlines already suppressed
  // above) or a completed round. Mid-round with real data gets a plain,
  // data-derived progress note instead, never the band tints.
  const showBandLegend = roundComplete || prov;
  const bandLegend = `
    <div class="ltlegend">
      <span><i style="background:var(--star)"></i>1\\u20138 round of 16</span>
      <span><i style="background:var(--line2)"></i>9\\u201324 knockout play-off</span>
      <span><i style="background:rgba(255,111,142,.6)"></i>25\\u201336 eliminated</span>
    </div>`;
  let progressNote = "";
  if(!showBandLegend){
    const played = rows.filter(r => (r.played||0) > 0).length;
    const md = (mdValid ? mdPlayed : 0) + 1;
    progressNote = `<div class="ltnote">Matchday ${md} in progress \\u2014 ${played} of ${rows.length}`
      + ` clubs have played. Qualification cutlines appear once the round is complete.</div>`;
  }
  el.innerHTML = `
    <div class="lthdr"><span class="t">League phase</span><span class="s">${sub}</span></div>
    ${showBandLegend ? bandLegend : progressNote}
    ${t.note ? `<div class="ltnote">${esc(t.note)}</div>` : ""}
    <table class="ltbl">
      <thead><tr>
        <th>#</th><th class="l">Club</th><th>P</th>
        <th class="opt">W</th><th class="opt">D</th><th class="opt">L</th>
        <th class="opt">GF</th><th class="opt">GA</th><th>GD</th><th>Pts</th>
      </tr></thead>
      <tbody>${body}</tbody>
    </table>`;
  el.querySelectorAll("tr[data-t]").forEach(tr =>
    tr.onclick = () => focusClub(C, tr.dataset.t));
}

/* ---------- match cards ---------- */
function marketBar(m){
  const h = pct(m.home), d = pct(m.draw), a = pct(m.away);
  return {h, d, a};
}

function deepCard(C, p, i){
  const {h, d, a} = marketBar(p.market||{});
  const kick = p.commence_time ? new Date(p.commence_time).toLocaleString([], {
    weekday:"short", month:"short", day:"numeric", hour:"2-digit", minute:"2-digit"}) : "";
  const graded = p.actual;
  const mid = graded ? `<div class="fin">${esc(graded.final_score)}</div>`
                     : `<div class="vs">V</div>`;
  let result = "";
  if(graded){
    const b = graded.pick_hit ? '<span class="badge hit">PICK \\u2713</span>'
                              : '<span class="badge miss">PICK \\u2717</span>';
    const sb = graded.score_hit ? ' <span class="badge hit">EXACT \\u2713</span>' : '';
    result = `<div class="result"><span class="rl">FULL TIME</span>
      <span class="rs">${esc(graded.final_score)}</span>
      <span class="rl">${PICK[graded.result]||""}</span>${b}${sb}</div>`;
  }
  const fl = p.disagreement ? `<div class="flag"><b>TIPSTER WATCH</b>${esc(p.disagreement)}</div>` : "";
  const src = (p.sources||[]).map(s =>
    `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title||"source")} \\u2197</a>`).join("");
  const rat = p.rationale ? `<p class="rat">${esc(p.rationale)}</p>` : "";
  const why = rat + fl + (src ? `<div class="src">${src}</div>` : "");
  const nsrc = (p.sources||[]).length;
  const srcN = nsrc ? ` \\u00b7 ${nsrc} source${nsrc>1?'s':''}` : "";
  const details = why ? `<details class="why"><summary><span class="chev">\\u25B8</span>
    Analysis${srcN}</summary><div class="whybody">${why}</div></details>` : "";
  return `<div class="match" style="animation-delay:${Math.min(i*45,400)}ms">
    <div class="sb">
      <div class="side home">
        <div class="fl">${crest(C,p.home_team,'lg')}</div>
        <div class="name">${esc(p.home_team)}</div>
        <div class="sub">${esc(code(C,p.home_team))} \\u00b7 HOME</div>
      </div>
      <div class="mid">
        ${mid}
        ${kick ? `<div class="kick">${esc(kick)}</div>` : ""}
        ${p.matchday ? `<div class="mdchipsm">${esc(p.matchday)}</div>` : ""}
      </div>
      <div class="side away">
        <div class="fl">${crest(C,p.away_team,'lg')}</div>
        <div class="name">${esc(p.away_team)}</div>
        <div class="sub">AWAY \\u00b7 ${esc(code(C,p.away_team))}</div>
      </div>
    </div>
    <div class="callrow">
      <div class="call"><span class="lab">Our call</span>
        <span class="pk" style="color:${pickColor(p.pick)}">${PICK[p.pick]||p.pick||"\\u2014"}</span>
        ${p.scoreline ? `<span class="sl">${esc(p.scoreline)}</span>` : ""}
        <span class="tag deep">deep</span></div>
      ${confBlocks(p.confidence, true)}
    </div>
    <div class="body">
      <div class="bar">
        <div class="h" style="width:${h}%">${h>=10?h+"%":""}</div>
        <div class="d" style="width:${d}%">${d>=10?d+"%":""}</div>
        <div class="a" style="width:${a}%">${a>=10?a+"%":""}</div>
      </div>
      <div class="leg">
        <span><i style="background:var(--home)"></i>${esc(code(C,p.home_team))} ${h}%</span>
        <span><i style="background:var(--draw)"></i>Draw ${d}%</span>
        <span><i style="background:var(--away)"></i>${esc(code(C,p.away_team))} ${a}%</span>
      </div>
      ${result}
      ${details}
    </div>
  </div>`;
}

function quickCard(C, p, i){
  const {h, d, a} = marketBar(p.market||{});
  const kick = p.commence_time ? new Date(p.commence_time).toLocaleString([], {
    hour:"2-digit", minute:"2-digit"}) : "";
  const graded = p.actual;
  let res = "";
  if(graded){
    const b = graded.pick_hit ? '<span class="badge hit">\\u2713</span>'
                              : '<span class="badge miss">\\u2717</span>';
    const sb = graded.score_hit ? '<span class="badge hit">EXACT</span>' : '';
    res = `<span class="sl">${esc(graded.final_score)}</span>${b}${sb}`;
  }
  return `<div class="qcard" style="animation-delay:${Math.min(i*35,320)}ms">
    <div class="qt">
      <span>${crest(C,p.home_team,'sm')}</span><span class="nm">${esc(p.home_team)}</span>
      <span class="v">v</span>
      <span>${crest(C,p.away_team,'sm')}</span><span class="nm">${esc(p.away_team)}</span>
      <span class="qmeta">${kick ? esc(kick)+" \\u00b7 " : ""}${p.matchday ? esc(p.matchday)+" \\u00b7 " : ""}quick pick</span>
    </div>
    <div class="qbarw">
      <div class="qbar">
        <div class="h" style="width:${h}%"></div>
        <div class="d" style="width:${d}%"></div>
        <div class="a" style="width:${a}%"></div>
      </div>
      <div class="qlg"><span>${h}%</span><span>${d}%</span><span>${a}%</span></div>
    </div>
    <div class="qcall">
      <span class="pk" style="color:${pickColor(p.pick)}">${PICK[p.pick]||p.pick||"\\u2014"}</span>
      ${p.scoreline ? `<span class="sl">${esc(p.scoreline)}</span>` : ""}
      ${confBlocks(p.confidence, false)}
      <span class="tag quick">quick</span>
      ${res}
    </div>
  </div>`;
}

const card = (C, p, i) => p._deep ? deepCard(C, p, i) : quickCard(C, p, i);

/* ---------- fixtures view ---------- */
let allOpen = false;
let focusTeam = null;
function applyFold(){ document.querySelectorAll("#mdwrap .why").forEach(x => x.open = allOpen); }
function setExpandAll(open){
  allOpen = open; applyFold();
  document.getElementById("expandall").innerHTML =
    open ? "\\u2715 collapse analysis" : "\\u2922 expand analysis";
}

function sectionsHtml(C){
  const today = (DATA.generated_at||"").slice(0,10);
  const groups = C._groups;
  // open the round being played now, else the next one up, else the last played
  let cur = groups.findIndex(g => g.start <= today && today <= g.end);
  if(cur < 0) cur = groups.findIndex(g => g.start >= today);
  if(cur < 0) cur = groups.length - 1;
  let i = 0;
  return groups.map((g, gi) => {
    const byDate = {}; const order = [];
    g.items.forEach(p => { if(!byDate[p._date]){ byDate[p._date] = []; order.push(p._date); }
      byDate[p._date].push(p); });
    let inner = "";
    order.forEach(ds => {
      if(order.length > 1 || g.md) inner += `<div class="daydiv">${prettyDate(ds)}</div>`;
      byDate[ds].forEach(p => { inner += card(C, p, i++); });
    });
    const rec = g.graded
      ? `<span class="mdcount">${g.hits}/${g.graded} correct</span>` : "";
    return `<details class="mdsec" data-k="${esc(g.key)}"${gi===cur?" open":""}>
      <summary>
        <span class="mdname">${esc(g.label)}</span>
        <span class="mdsub">${g.span}</span>
        <span class="mdcount">${g.items.length} match${g.items.length===1?'':'es'}</span>
        ${rec}
        <span class="chev">\\u276F</span>
      </summary>
      <div class="mdbody">${inner}</div>
    </details>`;
  }).join("");
}

function renderFixtures(C){
  const el = document.getElementById("mdwrap");
  const hdr = document.getElementById("mhdr");
  const matches = C._matches;
  if(!matches.length){
    hdr.textContent = "Match predictions";
    el.innerHTML = `<div class="empty">No ${esc(C.short)} predictions yet. ${esc(roundCopy(C))}</div>`;
    return;
  }
  if(focusTeam){
    const list = matches.filter(p => p.home_team===focusTeam || p.away_team===focusTeam);
    const g = list.filter(p => p.actual).length;
    const c = list.filter(p => p.actual && p.actual.pick_hit).length;
    hdr.textContent = "Club focus";
    el.innerHTML = `<div class="focusbar">
        <span>${crest(C,focusTeam)}</span><span class="fname">${esc(focusTeam)}</span>
        <span class="frec">${list.length} fixture${list.length===1?'':'s'} predicted${
          g ? ` \\u00b7 ${c}/${g} calls right` : ""}</span>
        <span class="fclear" id="fclear">\\u21BA back to matchdays</span>
      </div>` + (list.length ? list.map((p,i) => card(C,p,i)).join("")
        : '<div class="empty">No predictions for this club yet.</div>');
    document.getElementById("fclear").onclick = () => { focusTeam = null; renderFixtures(C); renderRail(C); };
    applyFold();
    return;
  }
  hdr.textContent = `Match predictions \\u00b7 ${matches.length}`;
  el.innerHTML = sectionsHtml(C);
  applyFold();
}

function renderRail(C){
  const el = document.getElementById("rail");
  if(!C._groups.length){ el.innerHTML = ""; return; }
  el.innerHTML = C._groups.map(g => {
    const sub = g.graded ? `${g.hits}/${g.graded} \\u2713` : `${g.items.length} matches`;
    return `<div class="mdchip" data-k="${esc(g.key)}">
      <span class="cl">${esc(g.label)}</span><span class="cs">${sub}</span></div>`;
  }).join("");
  el.querySelectorAll(".mdchip").forEach(c => c.onclick = () => openMatchday(C, c.dataset.k));
  syncRail();
}

function eachSection(fn){ document.querySelectorAll("#mdwrap .mdsec").forEach(fn); }

function syncRail(){
  const open = {};
  eachSection(s => { if(s.open) open[s.dataset.k] = 1; });
  document.querySelectorAll(".mdchip").forEach(c =>
    c.classList.toggle("on", !focusTeam && !!open[c.dataset.k]));
}

function openMatchday(C, key){
  if(focusTeam){ focusTeam = null; renderFixtures(C); }
  showView("fixtures");
  let target = null;
  eachSection(s => { const on = s.dataset.k === key; s.open = on; if(on) target = s; });
  syncRail();
  if(target) target.scrollIntoView({behavior:"smooth", block:"start"});
}

function focusClub(C, name){
  focusTeam = name;
  showView("fixtures");
  renderFixtures(C);
  syncRail();
  document.getElementById("mhdr").scrollIntoView({behavior:"smooth", block:"start"});
}

/* ---------- view switch ---------- */
function showView(v){
  document.querySelectorAll("#switch button").forEach(b =>
    b.classList.toggle("on", b.dataset.v === v));
  document.getElementById("fixturesView").classList.toggle("hidden", v !== "fixtures");
  document.getElementById("tableView").classList.toggle("hidden", v !== "table");
}
document.querySelectorAll("#switch button").forEach(b => b.onclick = () => showView(b.dataset.v));

/* ---------- competition switcher ---------- */
let activeComp = null;

function renderTabs(){
  const el = document.getElementById("comptabs");
  el.innerHTML = ORDER.map(k => {
    const C = DATA.comps[k], s = C.summary || {};
    const on = k === activeComp;
    const hr = s.graded && s.hit_rate != null ? `<b>${s.hit_rate}%</b>` : "";
    return `<button class="comptab${on ? " on" : ""}" role="tab" data-k="${esc(k)}"
      aria-selected="${on}" tabindex="${on ? 0 : -1}" title="${esc(C.name)}"><span class="full"
      >${esc(C.name)}</span><span class="abbr">${esc(C.short)}</span>${hr}</button>`;
  }).join("");
  el.querySelectorAll(".comptab").forEach(b => b.onclick = () => goComp(b.dataset.k));
}

function selectComp(k){
  const C = DATA.comps[k];
  activeComp = k;
  focusTeam = null;
  document.documentElement.dataset.comp = k;  // CSS swaps accent + mark on this
  const title = `${C.name} ${DATA.season||""}`.trim();
  document.title = `${title} \\u2014 Predictions`;
  document.getElementById("wordmark").textContent = title;
  renderTabs();
  renderStats(C.summary||{});
  renderSplit(C.summary||{});
  renderOutrights(C);
  renderPostmortem(C.postmortem);
  renderTable(C);
  renderFixtures(C);
  renderRail(C);
  document.getElementById("openall").innerHTML = "\\u2630 open every matchday";
}

// Tabs rewrite the hash without adding history entries; a typed or pasted
// hash is picked up by the hashchange listener below. Some browsers refuse
// replaceState on file:// pages, so fall back to a plain hash assignment
// (selectComp runs first, so the resulting hashchange is a no-op).
function goComp(k){
  if(k !== activeComp) selectComp(k);
  try { history.replaceState(null, "", "#" + k); } catch(_) { location.hash = k; }
}

const compFromHash = () => { const k = location.hash.slice(1); return ORDER.includes(k) ? k : null; };

// No hash: open the competition whose next unplayed predicted fixture is
// soonest (a kick-off within the last LIVE_MS still counts as unplayed);
// with none anywhere, the first competition in registry order.
const LIVE_MS = 3 * 3600 * 1000;
function defaultComp(){
  const from = Date.now() - LIVE_MS;
  let best = null, bestT = Infinity;
  ORDER.forEach(k => DATA.comps[k]._matches.forEach(p => {
    const t = Date.parse(p.commence_time || "");
    if(!p.actual && t >= from && t < bestT){ bestT = t; best = k; }
  }));
  return best || ORDER[0];
}

document.getElementById("comptabs").addEventListener("keydown", e => {
  const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
  const i = ORDER.indexOf(activeComp);
  if(!step || i < 0) return;
  e.preventDefault();
  goComp(ORDER[(i + step + ORDER.length) % ORDER.length]);
  const on = document.querySelector("#comptabs .comptab.on");
  if(on) on.focus();
});
window.addEventListener("hashchange", () => {
  const k = compFromHash();
  if(k && k !== activeComp) selectComp(k);
});

/* ---------- boot ---------- */
document.getElementById("gen").textContent = "updated " + (DATA.generated_at||"");
ORDER.forEach(k => prepare(DATA.comps[k]));
if(ORDER.length) selectComp(compFromHash() || defaultComp());
else document.getElementById("mdwrap").innerHTML =
  '<div class="empty">No competitions configured yet (config/competitions.json).</div>';
document.getElementById("expandall").onclick = () => setExpandAll(!allOpen);
document.getElementById("openall").onclick = () => {
  const anyClosed = [...document.querySelectorAll("#mdwrap .mdsec")].some(s => !s.open);
  eachSection(s => s.open = anyClosed);
  document.getElementById("openall").innerHTML =
    anyClosed ? "\\u2716 collapse matchdays" : "\\u2630 open every matchday";
  syncRail();
};
document.addEventListener("toggle", e => {
  if(e.target && e.target.classList && e.target.classList.contains("mdsec")) syncRail();
}, true);
</script></body></html>
"""


def validate_predictions(data_dir: str, teams_path: str, teams: dict) -> list[str]:
    """Sanity-check one competition's newest predictions file before it goes on the board.

    Checked against THAT competition's teams file only — the registries are
    never merged. Three classes of bug, all of which have actually happened:
      * a team name that isn't in the teams file — the name is the join key
        across odds, scores and predictions, so a typo silently un-grades the
        match forever;
      * a `depth` that is neither deep nor quick — it drops out of the
        deep-vs-quick accuracy split without a trace;
      * a scoreline that contradicts its own pick. Scorelines are ALWAYS
        home-away order, so a 'home' pick needs home>away goals, 'away' needs
        away>home, 'draw' needs equal. An away pick written '2-1' is a
        data-entry bug — catch it every build, loudly.

    Only the newest predictions file is checked: that's the current run, the
    one place the error is introduced. Past files are immutable and stay put.
    """
    problems = []
    files = data_files(data_dir, "predictions")
    for path in files[-1:]:
        base = os.path.basename(path)
        preds = load_json(path).get("predictions", [])
        if preds and not teams:
            problems.append(f"{base} — {teams_path} is missing or empty; "
                            f"team names were not checked")
        for p in preds:
            home, away = p.get("home_team"), p.get("away_team")
            where = f"{base}: {home} vs {away}"
            if teams:
                for t in (home, away):
                    if t not in teams:
                        problems.append(
                            f"{where} — unknown team {t!r}; not in {teams_path} "
                            f"(names must match the odds feed byte-for-byte)")
            depth = p.get("depth")
            if depth not in ("deep", "quick"):
                problems.append(
                    f"{where} — depth={depth!r} (expected 'deep' or 'quick'); "
                    f"it will be missing from the deep-vs-quick split")
            pick = p.get("pick")
            score = (p.get("scoreline") or "").strip()
            imp = implied_result(score)
            if pick not in ("home", "draw", "away"):
                problems.append(f"{where} — pick={pick!r} (expected home/draw/away)")
            elif not score:
                continue
            elif imp is None:
                problems.append(f"{where} — scoreline={score!r} is unparseable "
                                f"(expected 'H-A', e.g. '2-1')")
            elif imp != pick:
                problems.append(
                    f"{where} — pick={pick} scoreline={score} "
                    f"(home-away order — pick and scoreline disagree)")
    return problems


def summary_line(comp: dict) -> str:
    """One stdout line: predictions, hit rate, deep/quick split, table state."""
    s, table = comp["summary"], comp["table"]
    n = sum(len(d["predictions"]) for d in comp["days"])
    deep, quick = s["depth"]["deep"], s["depth"]["quick"]
    parts = [f"{n} prediction(s) in {len(comp['days'])} file(s)",
             f"hit rate {s['hit_rate']}% ({s['correct']}/{s['graded']})"
             if s["graded"] else "nothing graded yet"]
    if s["graded"]:
        parts.append(f"deep {deep['correct']}/{deep['graded']}"
                     f" · quick {quick['correct']}/{quick['graded']}")
    if table["provisional"]:
        parts.append("table provisional (no standings file yet"
                     + ("" if table["rows"] else ", no club list") + ")")
    elif table["matchdays_played"] >= 1:
        parts.append(f"table {len(table['rows'])} clubs after MD{table['matchdays_played']}")
    else:
        parts.append(f"table {len(table['rows'])} clubs, MD1 in progress")
    return f"   {comp['short']:<4} " + " · ".join(parts)


def main():
    season, registry = load_registry()
    if not registry:
        print(f"!! {REGISTRY_PATH} is missing or has no competitions — the page will be empty.")
    teams_by_comp = {key: load_teams(comp.get("teams_file") or "")
                     for key, comp in registry.items()}
    problems = [f"[{comp.get('short') or key.upper()}] {msg}"
                for key, comp in registry.items()
                for msg in validate_predictions(os.path.join(DATA_ROOT, key),
                                                comp.get("teams_file") or "",
                                                teams_by_comp[key])]
    if problems:
        print("\n!! PREDICTION FILE PROBLEMS — fix before publishing:")
        for msg in problems:
            print(f"   - {msg}")
        print()
    data = build_data(season, registry, teams_by_comp)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = HTML.replace("__DATA__", payload)
    # Write both: dashboard.html (local convention) and index.html (Pages root).
    for name in ("dashboard.html", "index.html"):
        with open(name, "w", encoding="utf-8") as f:
            f.write(html)
    print(f"Wrote dashboard.html — {len(data['order'])} competition(s)")
    for key in data["order"]:
        print(summary_line(data["comps"][key]))
    print("Open it with:  open dashboard.html")


if __name__ == "__main__":
    main()
