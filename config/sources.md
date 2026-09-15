# Trusted sources

The agent reads these when gathering qualitative intel for both competitions
(Champions League and Europa League). Curated for signal, not volume — a
handful of sharp, well-sourced outlets beats scraping everything.

## Quantitative — odds & model probabilities
The market is the backbone. Pulled automatically via `scripts/fetch_odds.py`.
- **The Odds API** (`soccer_uefa_champs_league`, `soccer_uefa_europa_league`)
  — aggregates Pinnacle, Bet365, Betfair exchange, William Hill, etc.
  Pinnacle/exchanges weighted highest.
- **Opta / The Analyst** — supercomputer win probabilities, league-phase
  simulations, and match previews for both competitions' league-phase tables.
- **club-elo.com** — Elo ratings built specifically for club sides (unlike the
  WC's national-team Elo, this tracks club form week to week including domestic
  results) — a solid sanity check vs the market, especially early in the
  league phase before enough fixtures exist to price teams confidently.
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
    Villarreal, Real Betis, Real Sociedad.
  - **Bild, Kicker** — Bayern Munich, Borussia Dortmund, RB Leipzig, VfB
    Stuttgart, Bayer Leverkusen.
  - **Gazzetta dello Sport, Corriere dello Sport** — Inter Milan, Napoli, AS
    Roma, Como, Juventus, AC Milan.
  - **L'Équipe** — Paris Saint Germain, Lille, RC Lens, Marseille, Lyon.
  - **Record, A Bola** — Porto, Sporting Lisbon, Benfica.
- **Reputable club beat reporters on X** — confirmed starting XIs, fitness
  and rotation updates (use only well-sourced, named journalists).

## Europa League — additional local coverage
Same rules apply; a handful of extra big-club outlets plus guidance for the
rest of a much larger, more varied league-phase field.
- **Celtic** — Daily Record, The Scotsman (established Scottish sports
  press, strong on team news and beat reporting).
- **Olympiakos, OFI Crete** — Gazzetta.gr, SDNA, Sport24 (established Greek
  sports media, the sharpest source for team news on both clubs).
- **Everyone else in the Europa League field** — English-language previews
  and tipster consensus thin out fast outside the handful of clubs named
  above and in the Champions League list. Don't force it: where dedicated
  coverage isn't findable, say so plainly in the rationale ("no dedicated
  preview found, market-derived pick") rather than stretching a thin search
  into false confidence, and fall back to the club's own country's main
  national sports outlet (its own equivalent of Marca or Gazzetta) as the
  best single source of team news, searched by name rather than assumed.

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
