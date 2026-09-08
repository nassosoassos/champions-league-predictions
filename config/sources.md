# Trusted sources

The agent reads these when gathering qualitative intel. Curated for signal, not
volume — a handful of sharp, well-sourced outlets beats scraping everything.

## Quantitative — odds & model probabilities
The market is the backbone. Pulled automatically via `scripts/fetch_odds.py`.
- **The Odds API** (`soccer_uefa_champs_league`) — aggregates Pinnacle, Bet365,
  Betfair exchange, William Hill, etc. Pinnacle/exchanges weighted highest.
- **Opta / The Analyst** — supercomputer win probabilities, league-phase
  simulations, and match previews for the 36-team table.
- **club-elo.com** — Elo ratings built specifically for club sides (unlike the
  WC's national-team Elo, this tracks club form week to week including domestic
  results) — a solid sanity check vs the market, especially early in the
  league phase before enough UCL fixtures exist to price teams confidently.
- **FBref / Understat** — underlying xG and shot-quality form. Useful for
  spotting a team whose results are running hot or cold relative to
  performance, which the market is often slow to reprice.

## Qualitative — previews, team news, tactical reads
Used for what the market may not have priced yet (late injuries, lineup leaks,
rotation, motivation). The agent web-searches these per match.
- **The Athletic** — match previews, tactical analysis, club beat reporters.
- **BBC Sport** & **ESPN FC** — predicted lineups, team news, expert picks.
- **The Guardian football** — previews and reporting.
- **OddsChecker / OLBG** — aggregated tipster consensus + reasoning.
- **Local-language beat reporters and outlets** — the unpriced edge in club
  football usually surfaces here first, hours before English-language outlets
  pick it up:
  - **Marca, AS, Mundo Deportivo** — Real Madrid, Barcelona, Atlético Madrid,
    Villarreal, Real Betis.
  - **Bild, Kicker** — Bayern Munich, Borussia Dortmund, RB Leipzig, VfB
    Stuttgart.
  - **Gazzetta dello Sport, Corriere dello Sport** — Inter Milan, Napoli, AS
    Roma, Como.
  - **L'Équipe** — Paris Saint Germain, Lille, RC Lens.
  - **Record, A Bola** — Porto, Sporting Lisbon.
- **Reputable club beat reporters on X** — confirmed starting XIs, fitness
  and rotation updates (use only well-sourced, named journalists).

## Rules for the agent
- Prefer **named, dated reporting** over anonymous tip aggregators.
- A tip is only as good as its *reasoning* — capture the "why", not just the pick.
- When a tipster disagrees with the sharp market, note it but default to the
  market unless there's concrete breaking news (injury, suspension, keeper out).
- Ignore content that is purely promotional ("sign up for our VIP picks").
- **Rotation is the single most common unpriced factor in the league phase.**
  With 8 different opponents across 8 matchdays plus a full domestic
  calendar, a manager resting starters ahead of a league fixture — especially
  in a tie that already looks decided, or a midweek-heavy stretch — happens
  constantly and the market is frequently slow to fully price it in. Always
  check the local-language press for confirmed or rumoured rotation before
  finalizing a pick, and flag it explicitly in the rationale when it's a
  factor.
