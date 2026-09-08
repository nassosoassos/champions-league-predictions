#!/usr/bin/env python3
"""
Email a SHORT daily digest: link to the dashboard + what changed since the
previous day's run. It does not dump the full report — the dashboard has detail.

Computes changes by diffing today's structured files against the most recent
earlier ones:
    data/predictions-YYYY-MM-DD.json   (pick / scoreline / confidence per match)
    data/outrights-YYYY-MM-DD.json     (outright picks)

If the agent wrote a funny Greek round-up for the day at
    data/digest-el-YYYY-MM-DD.md
it is embedded in the digest under a "Το αγωνιστικό μενού της ημέρας" heading.

The Champions League league phase runs in tight 3-day matchday clusters with
weeks of nothing in between. On a day with no fixtures and no changes, this
script sends nothing at all rather than mailing an empty digest — it just
says so on stdout and exits 0.

Sends via SMTP (Gmail by default). Configure with environment variables:
    UCL_SMTP_PASSWORD   (required) — a Gmail App Password for the FROM account
    UCL_EMAIL_FROM      (default: nkatsam@gmail.com)
    UCL_EMAIL_TO        (default: nkatsam@gmail.com)
    UCL_SMTP_HOST       (default: smtp.gmail.com)
    UCL_SMTP_PORT       (default: 587)
    UCL_DASHBOARD_URL   (default: the GitHub Pages URL)

Usage:
    python3 scripts/send_email.py                 # today (UTC), auto-diff
    python3 scripts/send_email.py --date 2026-09-10 --dry-run

Stdlib only — no pip install required.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import smtplib
import ssl
import sys
from datetime import datetime, timezone
from email.message import EmailMessage

DASHBOARD_DEFAULT = "https://nassosoassos.github.io/champions-league-predictions/"
PICK_LABEL = {"home": "Home", "draw": "Draw", "away": "Away"}
MAX_SECTION_LINES = 8


def load_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def dated_files(prefix: str) -> list[tuple[str, str]]:
    """Sorted [(date, path)] for data/<prefix>-YYYY-MM-DD.json."""
    out = []
    for p in glob.glob(f"data/{prefix}-*.json"):
        d = os.path.basename(p)[len(prefix) + 1:-len(".json")]
        out.append((d, p))
    return sorted(out)


def pick_today_and_prev(prefix: str, today: str) -> tuple[str | None, str | None]:
    files = dated_files(prefix)
    if not files:
        return None, None
    # today's file (or the latest available if today's isn't there yet)
    today_path = next((p for d, p in files if d == today), None)
    if today_path is None:
        today, today_path = files[-1]
    prev = [p for d, p in files if d < today]
    return today_path, (prev[-1] if prev else None)


def greek_blurb(today: str) -> str | None:
    """The agent's funny Greek round-up for the day, if it wrote one.

    Reads data/digest-el-YYYY-MM-DD.{md,txt} for *today's* date only — the blurb
    is date-specific prose about that day's fixtures, so we never fall back to an
    earlier day's text. Returns the trimmed text, or None if today's file is absent.
    """
    for ext in (".md", ".txt"):
        path = f"data/digest-el-{today}{ext}"
        try:
            with open(path) as f:
                text = f.read().strip()
        except OSError:
            continue
        if text:
            return text
    return None


def stars(c) -> str:
    try:
        c = int(c)
    except (TypeError, ValueError):
        return "?"
    return "●" * c + "○" * max(0, 5 - c)


def _is_bullet(line: str) -> bool:
    return line.lstrip()[:1] in ("•", "+")


def cap_section(lines: list[str], max_lines: int = MAX_SECTION_LINES) -> list[str]:
    """Cap a diff section at ~max_lines, keeping whole bullet blocks intact
    and appending '...and N more' for anything cut. With 18 matches per
    matchday the raw diff can run long, so this keeps the email short."""
    if len(lines) <= max_lines:
        return lines

    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _is_bullet(line) and current:
            blocks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append(current)

    kept: list[str] = []
    kept_blocks = 0
    for block in blocks:
        if kept and len(kept) + len(block) > max_lines:
            break
        kept += block
        kept_blocks += 1

    remaining = len(blocks) - kept_blocks
    if remaining > 0:
        kept.append(f"  ...and {remaining} more")
    return kept


def diff_predictions(today_path, prev_path) -> tuple[list[str], int]:
    cur = {f"{p.get('home_team')} v {p.get('away_team')}": p
           for p in load_json(today_path).get("predictions", [])}
    old = {f"{p.get('home_team')} v {p.get('away_team')}": p
           for p in load_json(prev_path).get("predictions", [])} if prev_path else {}
    lines = []
    for name, p in cur.items():
        o = old.get(name)
        if o is None:
            lines.append(f"  + NEW  {name} — {PICK_LABEL.get(p.get('pick'), p.get('pick'))} "
                         f"{p.get('scoreline','')} ({stars(p.get('confidence'))})")
            if p.get("rationale"):
                lines.append(f"        ↳ {p['rationale']}")
            lines.append("")
            continue
        deltas = []
        if p.get("pick") != o.get("pick"):
            deltas.append(f"pick {PICK_LABEL.get(o.get('pick'), o.get('pick'))}→"
                          f"{PICK_LABEL.get(p.get('pick'), p.get('pick'))}")
        if p.get("scoreline") != o.get("scoreline"):
            deltas.append(f"score {o.get('scoreline')}→{p.get('scoreline')}")
        if p.get("confidence") != o.get("confidence"):
            deltas.append(f"conf {o.get('confidence')}→{p.get('confidence')}")
        if deltas:
            lines.append(f"  • {name} — {', '.join(deltas)}")
            if p.get("rationale"):
                lines.append(f"        ↳ {p['rationale']}")
            lines.append("")
    return lines, len(cur)


def diff_outrights(today_path, prev_path) -> list[str]:
    """Diff outright markets. A market has either a single `pick` (string) or
    a `picks` array (e.g. top_8) — handle both shapes without crashing."""
    cur = {m.get("key"): m for m in load_json(today_path).get("markets", [])} if today_path else {}
    old = {m.get("key"): m for m in load_json(prev_path).get("markets", [])} if prev_path else {}
    lines = []
    for key, m in cur.items():
        o = old.get(key)
        if not o:
            continue
        deltas = []
        if "picks" in m or "picks" in o:
            cur_picks = m.get("picks") or []
            old_picks = o.get("picks") or []
            if cur_picks != old_picks:
                added = [t for t in cur_picks if t not in old_picks]
                removed = [t for t in old_picks if t not in cur_picks]
                if added:
                    deltas.append(f"+{', '.join(added)}")
                if removed:
                    deltas.append(f"-{', '.join(removed)}")
        elif m.get("pick") != o.get("pick"):
            deltas.append(f"pick {o.get('pick')}→{m.get('pick')}")
        if m.get("confidence") != o.get("confidence"):
            deltas.append(f"conf {o.get('confidence')}→{m.get('confidence')}")
        if deltas:
            lines.append(f"  • {m.get('question', key)} — {', '.join(deltas)}")
            if m.get("note"):
                lines.append(f"        ↳ {m['note']}")
            lines.append("")
    return lines


def next_match(today_path) -> str | None:
    now = datetime.now(timezone.utc)
    upcoming = []
    for p in load_json(today_path).get("predictions", []):
        ct = p.get("commence_time")
        if not ct:
            continue
        try:
            t = datetime.fromisoformat(ct.replace("Z", "+00:00"))
        except ValueError:
            continue
        if t >= now:
            upcoming.append((t, p))
    if not upcoming:
        return None
    t, p = min(upcoming, key=lambda x: x[0])
    return (f"{p.get('home_team')} v {p.get('away_team')} — "
            f"{t.strftime('%Y-%m-%d %H:%M UTC')} "
            f"({PICK_LABEL.get(p.get('pick'), p.get('pick'))} {p.get('scoreline','')})")


def build_body(today: str, dashboard: str) -> tuple[str, str, bool]:
    """Returns (body, subject_suffix, quiet). `quiet` means no fixtures and no
    changes — the caller should send nothing on a live run in that case."""
    p_today, p_prev = pick_today_and_prev("predictions", today)
    o_today, o_prev = pick_today_and_prev("outrights", today)

    match_changes, n_matches = diff_predictions(p_today, p_prev) if p_today else ([], 0)
    out_changes = diff_outrights(o_today, o_prev)
    # count actual changes (bullet/NEW lines), not the explanation/blank lines
    count = lambda ls: sum(1 for l in ls if _is_bullet(l))
    n_changes = count(match_changes) + count(out_changes)

    quiet = n_matches == 0 and n_changes == 0

    prev_date = None
    if p_prev:
        prev_date = os.path.basename(p_prev)[len("predictions-"):-len(".json")]

    parts = ["Champions League 2026-27 — matchday update", "",
             f"📊 Dashboard: {dashboard}", ""]

    if quiet:
        parts.append("No fixtures and no changes since the last update — quiet "
                     "day between matchdays. Full detail on the dashboard.")
    elif not p_prev:
        parts.append(f"First daily digest — {n_matches} matches predicted. "
                     "See the dashboard for all picks, rationale and the outrights.")
    elif n_changes == 0:
        parts.append(f"No changes since {prev_date}. Picks unchanged — full detail on the dashboard.")
    else:
        parts.append(f"Updates since {prev_date} ({n_changes}):")
        if match_changes:
            parts += ["", "Matches:"] + cap_section(match_changes)
        if out_changes:
            parts += ["", "Outrights:"] + cap_section(out_changes)

    blurb = greek_blurb(today)
    if blurb:
        parts += ["", "🇬🇷 Το αγωνιστικό μενού της ημέρας:", "", blurb]

    nxt = next_match(p_today) if p_today else None
    if nxt:
        parts += ["", f"⏭️  Next up: {nxt}"]

    parts += ["", f"Full picks, rationale & accuracy → {dashboard}",
              "— Automated Champions League agent. Predictions for fun, not betting advice."]

    if quiet:
        suffix = "quiet day"
    elif not p_prev:
        suffix = "first digest"
    elif n_changes == 0:
        suffix = "no changes"
    else:
        suffix = f"{n_changes} update" + ("s" if n_changes != 1 else "")
    return "\n".join(parts), suffix, quiet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="digest date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--dashboard", default=os.environ.get("UCL_DASHBOARD_URL", DASHBOARD_DEFAULT))
    ap.add_argument("--subject", default=None)
    ap.add_argument("--dry-run", action="store_true", help="print the email; don't send")
    args = ap.parse_args()

    today = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body, suffix, quiet = build_body(today, args.dashboard)
    subject = args.subject or f"Champions League 2026-27 — matchday update — {today} ({suffix})"

    if args.dry_run:
        print(f"SUBJECT: {subject}\n\n{body}")
        return

    if quiet:
        print(f"[email] no fixtures and no changes for {today} — nothing to send.")
        return

    sender = os.environ.get("UCL_EMAIL_FROM", "nkatsam@gmail.com")
    recipient = os.environ.get("UCL_EMAIL_TO", "nkatsam@gmail.com")
    host = os.environ.get("UCL_SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("UCL_SMTP_PORT", "587"))
    password = os.environ.get("UCL_SMTP_PASSWORD")
    if not password:
        sys.exit("UCL_SMTP_PASSWORD is not set — add it to your shell profile.")

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, recipient, subject
    msg.set_content(body)

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls(context=ctx)
            server.login(sender, password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        sys.exit("[email] auth failed — check UCL_EMAIL_FROM and the App Password.")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"[email] send failed: {e}")
    print(f"[email] sent '{subject}' to {recipient}")


if __name__ == "__main__":
    main()
