# Champions League 2026-27 prediction agent

A daily agent that predicts upcoming UEFA Champions League matches by
combining the betting market (quantitative backbone) with tipster/preview
intel (qualitative layer), then writes a markdown report and tracks its own
accuracy. It is a port of a World Cup 2026 prediction agent, adapted for a
competition that plays in bursts of 18 matches followed by weeks of nothing.

## How it works

```
                 ┌──────────────────────────────┐
  daily          │  scripts/fetch_odds.py        │  → vig-free market
  scheduled  ──▶ │  (The Odds API, de-vigged)    │    probabilities
  task           └──────────────┬───────────────┘    (the PRIOR)
                                │
                 ┌──────────────▼───────────────┐
                 │  Agent runs prompts/          │  → quick pick for all 18,
                 │  daily-run.md: matchday check,│    deep research on ~6
                 │  tiered depth, web-searches   │    (lineups, tipsters, why)
                 └──────────────┬───────────────┘
                                │
                 ┌──────────────▼───────────────┐
                 │  Synthesis: start from market,│  → pick, scoreline,
                 │  nudge for unpriced news      │    confidence, rationale
                 └──────────────┬───────────────┘
                                │
       reports/*.md  +  data/predictions-*.json  +  tracking/accuracy.md
                                │
                 ┌──────────────▼───────────────┐
                 │  scripts/build_dashboard.py   │  → dashboard.html
                 │  (predictions + odds + scores │    (open in any browser)
                 │   + league table + outrights) │
                 └──────────────────────────────┘
```

On most days there is nothing to predict — the league phase plays 18 matches
on a matchday and then goes quiet for weeks. `prompts/daily-run.md` checks
the calendar first and, on a quiet day, only grades results, refreshes the
league table, and rebuilds the dashboard. It does not research fixtures that
are two weeks away, and it does not send an empty email.

## The dashboard
`dashboard.html` is a single self-contained file (data baked in, no server,
no npm). It shows:
- Per matchday, each match with a 3-way market probability bar, the agent's
  pick + scoreline + confidence stars, the rationale, a flag when tipsters
  disagree with the market, and — once games finish — the actual score with
  ✓/✗ hit badges.
- A **league table** — all 36 clubs, one table, with the 1-8 / 9-24 / 25-36
  cutlines marked (straight to the round of 16 / knockout play-off /
  eliminated).
- A top panel tracking running hit-rate and exact-score hits, **split by
  research depth** (deep vs quick) — the most honest number this project
  produces, since the two are graded on very different amounts of work.
- An outrights panel (winner, top 8, top scorer, finalists, dark horse).

Rebuilt at the end of every daily run; open it any time with
`open dashboard.html`.

**Design principle:** the sharp market (Pinnacle, exchanges) is the single
best predictor available. We treat it as the prior and only deviate when
there's a concrete, plausibly-unpriced reason (late team news). Tipster blogs
supply the *narrative and the edge cases*, not the base rate.

**Tiered depth:** 18 matches on a matchday is too many to research equally.
Every match gets a market-derived `quick` pick; roughly six get full research
(`deep`) — chosen for where the market is closest, where there's genuine
team-news uncertainty, or where the tie is a marquee draw. The dashboard
keeps the two visibly separate rather than dressing up a market lookup as
analysis.

## Layout
- `config/teams.json` — all 36 clubs (name, short code, country, flag). Team
  names are the join key across odds, scores, and predictions — never rename
  one; they're verified byte-for-byte against the live odds feed.
- `config/sources.md` — curated trusted sources + rules for using them.
- `scripts/fetch_odds.py` — pulls & de-vigs odds → `data/odds-*.json`.
  Stdlib only.
- `scripts/fetch_scores.py` — pulls actual final scores → `data/scores-*.json`,
  used to grade past predictions. Stdlib only.
- `scripts/build_dashboard.py` — bakes predictions + odds + scores + league
  table + accuracy + outrights into a single self-contained `dashboard.html`.
  Stdlib only.
- `scripts/send_email.py` — emails the daily summary via SMTP. Stdlib only.
- `dashboard.html` — the UI. Just open it (`open dashboard.html`).
- `data/standings-*.json` — the official UEFA league-phase table, fetched
  fresh each run (never reconstructed from our own partial score history).
- `data/outrights-*.json` — outright picks (winner, top 8, top scorer,
  finalists, dark horse); rendered in the dashboard's Outrights panel.

## Email
The daily run sends a **short digest** via `scripts/send_email.py` (from/to
nkatsam@gmail.com by default) — a link to the dashboard plus what changed
since the previous run (it diffs the `data/*.json` files); it does not dump
the full report. Sent only on match days — a quiet day between matchdays
sends nothing. One-time setup — create a Gmail **App Password**
(https://myaccount.google.com/apppasswords, needs 2-Step Verification) and
export it:
```
echo 'export UCL_SMTP_PASSWORD="abcd efgh ijkl mnop"' >> ~/.zshrc && source ~/.zshrc
```
Override `UCL_EMAIL_FROM` / `UCL_EMAIL_TO` / `UCL_SMTP_HOST` / `UCL_SMTP_PORT`
if needed. Test it: `python3 scripts/send_email.py --report reports/<today>.md --dry-run`.
- `prompts/daily-run.md` — the instruction set the daily agent follows.
- `reports/` — one markdown report per matchday run.
- `tracking/accuracy.md` — immutable log of calls vs outcomes + running
  hit-rate, split by research depth.

## Setup
1. **Get an Odds API key** (paid-but-cheap tier) at https://the-odds-api.com.
   The sport key for this competition is `soccer_uefa_champs_league`. Note
   that The Odds API has **no outright market** for the Champions League —
   outright prices come from web research (OddsChecker, Oddspedia), not the
   API.
2. Put it in your environment so the script and scheduled task can see it:
   ```
   echo 'export THE_ODDS_API_KEY=your_key_here' >> ~/.zshrc && source ~/.zshrc
   ```
3. Test the fetcher:
   ```
   python3 scripts/fetch_odds.py --days 4
   ```
   (`--days 4` matches the matchday's 3-day Tue/Wed/Thu cluster — a wider
   window mostly just spans dead air between rounds.)
4. Do a manual run: in Claude Code, run the steps in `prompts/daily-run.md`.
5. Schedule it daily (see below) — it self-limits to matchday work; running
   it every day is safe and cheap on quiet days.

**API credit budget:** the key is on a 500-credit tier; each run costs ~4
credits (one odds call at 2 for `regions=eu,uk`, one scores call at 2).
Calling the API only on the ~44 active match days costs ~176 credits for the
season — comfortably within budget. Calling it every day of the season
(~270 days) costs ~1080 credits and runs dry around February, right at the
knockout play-offs — this is why Step 1's quiet-day branch skips the fetch
rather than just being tidy. If the budget ever gets tight, `--regions eu`
instead of `eu,uk` saves a further credit per run.

## Scheduling
Use Claude Code's `/schedule` to run `prompts/daily-run.md` every morning
(e.g. 9:00 local). It checks the season calendar itself and skips research
and email on quiet days between matchdays.

## Season calendar (2026-27)

| Round | Dates |
|---|---|
| MD1 | 8-10 Sep 2026 |
| MD2 | 13-14 Oct 2026 |
| MD3 | 20-21 Oct 2026 |
| MD4 | 3-4 Nov 2026 |
| MD5 | 24-25 Nov 2026 |
| MD6 | 8-9 Dec 2026 |
| MD7 | 19-20 Jan 2027 |
| MD8 | 27 Jan 2027 (all 18 games simultaneous) |
| Knockout play-offs | 16-17 & 23-24 Feb 2027 |
| Round of 16 | 9-10 & 16-17 Mar 2027 |
| Quarter-finals | 6-7 & 13-14 Apr 2027 |
| Semi-finals | 27-28 Apr & 4-5 May 2027 |
| Final | 5 Jun 2027, Estadio Metropolitano, Madrid |

Format: 36 teams, one league-phase table, each plays 8 different opponents
(4 home, 4 away). **1-8** go straight to the round of 16. **9-24** enter a
two-legged knockout play-off. **25-36** are eliminated — no European football
after the league phase. Every round from the play-offs onward is two-legged
except the single-match final.

## Notes & honesty
- These are predictions **for fun**, not betting advice.
- Accuracy is logged transparently. Club football with big, well-known
  favourites is more predictable than World Cup groups — expect a naive
  1X2 hit rate noticeably above the ~50-55% that was realistic for the World
  Cup, simply because a lot of these matches have a heavy favourite. A high
  number here is not, on its own, evidence of skill; the deep-vs-quick split
  in the dashboard is the more honest read, since it isolates the matches
  where research actually had something to add.
- Beating the closing line consistently is genuinely hard, regardless of the
  raw hit rate.
- The agent must cite sources and never invent team news.
