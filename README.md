# European football prediction agent (UCL + UEL, 2026-27)

A daily agent that predicts upcoming matches in two UEFA club competitions —
the **Champions League (UCL)** and the **Europa League (UEL)** — by
combining the betting market (quantitative backbone) with tipster/preview
intel (qualitative layer), then writes a markdown report per competition and
tracks its own accuracy. It is a port of a World Cup 2026 prediction agent,
adapted for competitions that play in bursts of matches followed by weeks of
nothing, then extended to a second competition inside the same system: same
method, same dashboard (with a competition switch), same daily email, one
scheduled task.

## How it works

```
                 ┌──────────────────────────────┐
  daily          │  scripts/whats_on.py          │  → zero-credit calendar
  scheduled  ──▶ │  (free /events, /sports)      │    check per competition
  task           └──────────────┬───────────────┘
                                │
                 ┌──────────────▼───────────────┐
                 │  scripts/fetch_odds.py        │  → vig-free market
                 │  --comp <comp> (The Odds API) │    probabilities
                 └──────────────┬───────────────┘    (the PRIOR)
                                │
                 ┌──────────────▼───────────────┐
                 │  Agent runs prompts/          │  → quick pick for the
                 │  daily-run.md: obey the       │    full card, deep
                 │  verdict, tiered depth,       │    research on a few
                 │  web-searches, per competition│    (lineups, tipsters)
                 └──────────────┬───────────────┘
                                │
                 ┌──────────────▼───────────────┐
                 │  Synthesis: start from market,│  → pick, scoreline,
                 │  nudge for unpriced news      │    confidence, rationale
                 └──────────────┬───────────────┘
                                │
    reports/<comp>/*.md + data/<comp>/predictions-*.json + tracking/<comp>/accuracy.md
                                │
                 ┌──────────────▼───────────────┐
                 │  scripts/build_dashboard.py   │  → dashboard.html
                 │  (both competitions, with a   │    (open in any browser)
                 │   UCL/UEL switch)              │
                 └──────────────────────────────┘
```

On most days there is nothing to predict — each competition plays a batch of
matches on a matchday and then goes quiet for weeks, and the two
competitions' matchdays don't line up. `scripts/whats_on.py` is a zero-credit
command (it only calls The Odds API's free `/events` and `/sports`
endpoints) that checks, per competition, the real fixture list rather than a
hardcoded calendar — so a postponement or reschedule is never missed. It
prints a verdict per competition (`full run` / `maintenance only` / `nothing
to do`) and `prompts/daily-run.md` obeys it: on a quiet day it only grades
results, refreshes the league table, and rebuilds the dashboard. It does not
research fixtures that are weeks away, and it does not send an empty email.

## The dashboard
`dashboard.html` is a single self-contained file (data baked in, no server,
no npm) covering both competitions behind a UCL/UEL switch. For the selected
competition it shows:
- Per matchday, each match with a 3-way market probability bar, the agent's
  pick + scoreline + confidence stars, the rationale, a flag when tipsters
  disagree with the market, and — once games finish — the actual score with
  ✓/✗ hit badges.
- A **league table** for that competition, with its promotion/elimination
  cutlines marked.
- A top panel tracking running hit-rate and exact-score hits, **split by
  research depth** (deep vs quick) — the most honest number this project
  produces, since the two are graded on very different amounts of work.
- An outrights panel (winner, top 8, top scorer, finalists, dark horse), each
  with its own lock deadline.

Rebuilt at the end of every daily run; open it any time with
`open dashboard.html`.

**Design principle:** the sharp market (Pinnacle, exchanges) is the single
best predictor available. We treat it as the prior and only deviate when
there's a concrete, plausibly-unpriced reason (late team news). Tipster blogs
supply the *narrative and the edge cases*, not the base rate.

**Tiered depth:** a full matchday card is too many matches to research
equally. Every match gets a market-derived `quick` pick; a handful get full
research (`deep`) — chosen for where the market is closest, where there's
genuine team-news uncertainty, or where the tie is a marquee draw. UCL takes
6 deep picks per matchday, UEL takes 3 — Europa League previews and odds
depth are thinner for many clubs beyond the half-dozen biggest names, so
fewer matches can be researched to a standard worth publishing. The dashboard
keeps the two visibly separate rather than dressing up a market lookup as
analysis.

## Layout

`config/competitions.json` is the single source of truth for which
competitions the agent covers and their calendars, sport keys, deep-pick
counts, and outrights lock deadlines — everything else in the pipeline reads
it rather than hardcoding UCL/UEL-specific logic.

**Per competition** (`<comp>` is `ucl` or `uel`):
- `config/teams/<comp>.json` — that competition's clubs (name, short code,
  country, flag). Team names are the join key across odds, scores, and
  predictions within a competition — never rename one; they're verified
  byte-for-byte against the live odds feed. UCL and UEL club sets are
  disjoint this season, but the two registries are never merged into one
  lookup.
- `data/<comp>/odds-*.json`, `scores-*.json`, `predictions-*.json`,
  `outrights-*.json`, `standings-*.json` — same inner schemas as before,
  scoped per competition.
- `reports/<comp>/YYYY-MM-DD.md` — one markdown report per matchday run.
- `tracking/<comp>/accuracy.md` — immutable log of calls vs outcomes +
  running hit-rate, split by research depth.

**Shared, not per-competition:**
- `scripts/whats_on.py` — zero-credit calendar check across every
  competition in the registry; prints the daily verdict the agent obeys.
  Stdlib only.
- `scripts/fetch_odds.py` — pulls & de-vigs odds → `data/<comp>/odds-*.json`.
  Takes `--comp <comp>` (default: every competition with something to
  fetch, decided via the free events check). Stdlib only.
- `scripts/fetch_scores.py` — pulls actual final scores →
  `data/<comp>/scores-*.json`, used to grade past predictions. Takes
  `--comp <comp>` (same default behaviour). Stdlib only.
- `scripts/build_dashboard.py` — bakes both competitions' predictions +
  odds + scores + league tables + accuracy + outrights into a single
  self-contained `dashboard.html` with a competition switch. Stdlib only.
- `scripts/send_email.py` — emails the daily summary via SMTP, covering
  whichever competitions changed. Stdlib only.
- `dashboard.html` — the UI. Just open it (`open dashboard.html`).
- `config/sources.md` — curated trusted sources + rules for using them,
  across both competitions.
- `data/digest-el-YYYY-MM-DD.md` — one Greek round-up per day covering every
  competition that played.

## Email
The daily run sends **one short digest** via `scripts/send_email.py`
(from/to nkatsam@gmail.com by default) covering both competitions — a link
to the dashboard plus what changed since the previous run for whichever
competitions had changes (it diffs each competition's `data/<comp>/*.json`
files); it does not dump the full report. Sent only when at least one
competition had a match day — a quiet day sends nothing. One-time setup —
create a Gmail **App Password**
(https://myaccount.google.com/apppasswords, needs 2-Step Verification) and
export it:
```
echo 'export UCL_SMTP_PASSWORD="abcd efgh ijkl mnop"' >> ~/.zshrc && source ~/.zshrc
```
Override `UCL_EMAIL_FROM` / `UCL_EMAIL_TO` / `UCL_SMTP_HOST` / `UCL_SMTP_PORT`
if needed. Test it: `python3 scripts/send_email.py --report reports/ucl/<today>.md --dry-run`.
- `prompts/daily-run.md` — the instruction set the daily agent follows.

## Setup
1. **Get an Odds API key** (paid-but-cheap tier) at https://the-odds-api.com.
   The sport keys are `soccer_uefa_champs_league` (UCL) and
   `soccer_uefa_europa_league` (UEL) — see `config/competitions.json`. Note
   that The Odds API has **no outright market** for either competition —
   outright prices come from web research (OddsChecker, Oddspedia), not the
   API.
2. Put it in your environment so the scripts and scheduled task can see it:
   ```
   echo 'export THE_ODDS_API_KEY=your_key_here' >> ~/.zshrc && source ~/.zshrc
   ```
3. Test the zero-credit calendar check, then the fetcher:
   ```
   python3 scripts/whats_on.py
   python3 scripts/fetch_odds.py --comp ucl --days 4
   ```
   (`--days 4` matches a matchday's few-day cluster — a wider window mostly
   just spans dead air between rounds.)
4. Do a manual run: in Claude Code, run the steps in `prompts/daily-run.md`.
5. Schedule it daily (see below) — it self-limits to matchday work per
   competition; running it every day is safe and cheap on quiet days.

**API credit budget:** the key is on a 500-credit tier; **484 credits
remain** as of 15 Sep 2026. `whats_on.py`'s `/events` and `/sports` checks
are **free** (verified: `x-requests-last: 0`), so checking the calendar every
day costs nothing. The paid calls are `/odds` (2 credits, `regions=eu,uk`)
and `/scores` (2 credits, with `daysFrom`) — 4 credits per competition per
match day, and only spent when `whats_on.py` confirms there's something to
fetch. Roughly 26 UCL match days and 18 UEL match days remain this season
(league phase, play-offs, and knockouts combined) — even if every one of
those 44 match days spends the full 4 credits, that's ~176 credits, well
inside the 484 remaining. If the budget ever gets tight, `--regions eu`
instead of `eu,uk` saves a further credit per run.

## Scheduling
Scheduling is now **one** daily task (not one per competition) — use Claude
Code's `/schedule` to run `prompts/daily-run.md` every morning (e.g. 9:00
local). It checks both competitions' calendars itself via `whats_on.py` and
skips research and email for whichever competition is quiet that day.

**The first run must be started manually** with "Run now" while you are
present to approve its tool calls. Tool approvals are stored on the
scheduled task itself, not granted automatically — without that first
approved run, every subsequent scheduled run silently stalls waiting on
permissions it can never get. (`prompts/daily-run.md` now has an explicit
guardrail to report a blocked/denied command in its summary rather than
letting a stalled run look like a normal quiet day, but avoiding the stall
in the first place is better than detecting it after the fact.)

## Season calendar (2026-27)

`config/competitions.json` is the **authoritative** calendar — it drives
`whats_on.py` and every script; the table below is a human-readable summary
only, not something the code reads.

**Champions League** — 36 teams, one league-phase table, each club plays 8
different opponents (4 home, 4 away). Ranks **1-8** go straight to the round
of 16, **9-24** enter a two-legged knockout play-off, **25-36** are
eliminated. League phase MD1-MD8 run 8 Sep 2026 - 27 Jan 2027, then play-offs
(16-24 Feb 2027), round of 16 (9-17 Mar), quarter-finals (6-14 Apr),
semi-finals (27 Apr - 5 May), and the final on **5 Jun 2027** (Estadio
Metropolitano, Madrid).

**Europa League** — league phase MD1-MD8 run 16 Sep 2026 - 28 Jan 2027, one
matchday behind the Champions League each round, then its own knockout
play-offs, round of 16, quarter-finals, and semi-finals, culminating in the
final on **26 May 2027** (Waldstadion, Frankfurt). Exact cutlines and squad
counts are checked against `config/competitions.json` / uefa.com rather than
assumed to mirror the Champions League's.

Every round from the play-offs onward is two-legged in both competitions,
except each competition's single-match final.

## Notes & honesty
- These are predictions **for fun**, not betting advice.
- Accuracy is logged transparently, per competition. Club football with big,
  well-known favourites is more predictable than World Cup groups — expect a
  naive 1X2 hit rate noticeably above the ~50-55% that was realistic for the
  World Cup, simply because a lot of these matches have a heavy favourite. A
  high number here is not, on its own, evidence of skill; the deep-vs-quick
  split in the dashboard is the more honest read, since it isolates the
  matches where research actually had something to add.
- Beating the closing line consistently is genuinely hard, regardless of the
  raw hit rate.
- The agent must cite sources and never invent team news or results — when a
  result can't be confirmed from at least two sources, it stays ungraded
  rather than guessed.
