# Prediction accuracy log

Immutable record of calls vs outcomes. Never edit a prediction after kickoff.

## Running tally
- Matches predicted (graded): 6
- Correct picks (1X2): 4 — hit rate 67% (4/6)
- Exact scoreline hits: 1 (Real Madrid 2-1)
- Avg confidence of correct picks: 3.5
- Avg confidence of wrong picks: 3.0
- Deep: 1/3 (33%), 1 exact. Quick: 3/3 (100%), 0 exact.
- Blind market-favourite control: also 4/6 — identical, because we deviated from the favourite zero times on this card.

**Notes:**
On night one the market-derived quick picks outscored the researched ones 3/3 versus 1/3. The sample is three matches per bucket, which is far too small to conclude anything — but it is exactly the comparison this log exists to make, so it gets recorded rather than buried.
Both deep misses (Club Brugge, Lille) were matches where the research reinforced the market's home lean, and the home side lost. On Club Brugge the research actively hurt: confidence was raised from 2 to 3 on the basis that Aston Villa had not scored in three league games. Villa scored three.
The one exact scoreline (Real Madrid 2-1) was a deep pick, made while explicitly flagging the seven-player absence list as a headwind and lowering confidence from 4 to 3.

## Log
| Date | Match | Pick | Score guess | Conf | Depth | Actual | Pick hit? | Score hit? |
|------|-------|------|-------------|------|-------|--------|-----------|------------|
| 2026-09-08 | AEK Athens vs LASK | Home | 2-1 | 4 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-09-08 | Club Brugge vs Aston Villa | Home | 1-0 | 3 | deep | 2-3 (away) | ✗ | ✗ |
| 2026-09-08 | Borussia Dortmund vs Villarreal | Home | 2-1 | 3 | quick | 3-2 (home) | ✓ | ✗ |
| 2026-09-08 | Real Madrid vs Inter Milan | Home | 2-1 | 3 | deep | 2-1 (home) | ✓ | ✓ |
| 2026-09-08 | Lille vs Real Betis | Home | 1-0 | 3 | deep | 2-3 (away) | ✗ | ✗ |
| 2026-09-08 | Porto vs Manchester City | Away | 1-2 | 4 | quick | 0-2 (away) | ✓ | ✗ |
