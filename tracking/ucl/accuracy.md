# Prediction accuracy log

Immutable record of calls vs outcomes. Never edit a prediction after kickoff.

## Running tally
- Matches predicted (graded): 36
- Correct picks (1X2): 23 — hit rate 64% (23/36)
- Exact scoreline hits: 2 (Real Madrid 2-1, Liverpool 2-1)
- Avg confidence of correct picks: 3.91
- Avg confidence of wrong picks: 3.15
- Deep: 5/12 (42%), 1 exact. Quick: 18/24 (75%), 1 exact.
- Blind market-favourite control: 23/36 — identical, because no pick on any card so far deviated from the favourite.
- MD2 night two (14 Oct): 5/9. Deep 1/3 (Real Madrid won 4-3 at Roma; Shakhtar Donetsk beat AEK Athens 3-1 and Paris Saint Germain won 4-2 at Manchester City). Quick 4/6; the misses were Feyenoord 3-2 over Como and Bodø/Glimt 1-0 over Borussia Dortmund. A goal-heavy night: 46 goals in 9 matches, so no scoreline came close.
- MD2 night one (13 Oct): 5/9. Deep 2/3 (Atlético Madrid, Villarreal hit; RC Lens missed). Quick 3/6 — two 5-confidence favourites failed to win: Bayern Munich drew 3-3 at Viking FK, Inter Milan lost 3-4 at home to Club Brugge.

**Notes:**
The night-one note compared deep and quick hit rates as if that measured research. It does not, and that note was wrong. Deep picks are selected as the tightest lines on the card, while quick picks include 85-92% favourites, so deep picks will always hit less often. The 33% vs 92% gap is a selection effect, not evidence that research hurts.
The fair test is research versus the market favourite on the SAME matches. On the six deep matches the blind favourite also went 2/6. Because research moved no pick off the favourite this matchday, the pick-level result is identical by construction — MD1 says nothing about whether research helps.
What research did change was confidence, three times: Club Brugge 2→3 (lost 2-3), Fenerbahce 3→4 (drew 1-1), Real Madrid 4→3 (won 2-1, exact). Three moves, none borne out — far too few to conclude anything, but recorded.
Correct picks carried higher average confidence than wrong ones (4.08 vs 3.20), which is the direction a calibrated system should show.

## Log
| Date | Match | Pick | Score guess | Conf | Depth | Actual | Pick hit? | Score hit? |
|------|-------|------|-------------|------|-------|--------|-----------|------------|
| 2026-09-08 | AEK Athens vs LASK | Home | 2-1 | 4 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-09-08 | Club Brugge vs Aston Villa | Home | 1-0 | 3 | deep | 2-3 (away) | ✗ | ✗ |
| 2026-09-08 | Borussia Dortmund vs Villarreal | Home | 2-1 | 3 | quick | 3-2 (home) | ✓ | ✗ |
| 2026-09-08 | Real Madrid vs Inter Milan | Home | 2-1 | 3 | deep | 2-1 (home) | ✓ | ✓ |
| 2026-09-08 | Lille vs Real Betis | Home | 1-0 | 3 | deep | 2-3 (away) | ✗ | ✗ |
| 2026-09-08 | Porto vs Manchester City | Away | 1-2 | 4 | quick | 0-2 (away) | ✓ | ✗ |
| 2026-09-09 | Barcelona vs Feyenoord | Home | 2-0 | 5 | quick | 5-1 (home) | ✓ | ✗ |
| 2026-09-09 | VfB Stuttgart vs Viking FK | Home | 2-1 | 5 | quick | 3-1 (home) | ✓ | ✗ |
| 2026-09-09 | Napoli vs Arsenal | Away | 1-2 | 4 | deep | 0-1 (away) | ✓ | ✗ |
| 2026-09-09 | Liverpool vs Atlético Madrid | Home | 2-1 | 4 | quick | 2-1 (home) | ✓ | ✓ |
| 2026-09-09 | Sporting Lisbon vs Galatasaray | Home | 1-0 | 3 | quick | 3-1 (home) | ✓ | ✗ |
| 2026-09-09 | Paris Saint Germain vs ŠK Slovan Bratislava | Home | 2-0 | 5 | quick | 6-1 (home) | ✓ | ✗ |
| 2026-09-10 | Fenerbahce vs AS Roma | Away | 1-2 | 4 | deep | 1-1 (draw) | ✗ | ✗ |
| 2026-09-10 | PSV Eindhoven vs Shakhtar Donetsk | Home | 2-1 | 4 | quick | 1-1 (draw) | ✗ | ✗ |
| 2026-09-10 | Bayern Munich vs Bodø/Glimt | Home | 2-0 | 5 | quick | 5-0 (home) | ✓ | ✗ |
| 2026-09-10 | Como vs RB Leipzig | Home | 1-0 | 3 | quick | 4-1 (home) | ✓ | ✗ |
| 2026-09-10 | Manchester United vs Sabah FK | Home | 2-0 | 5 | quick | 4-0 (home) | ✓ | ✗ |
| 2026-09-10 | Slavia Praha vs RC Lens | Home | 1-0 | 2 | deep | 2-3 (away) | ✗ | ✗ |
| 2026-10-13 | RC Lens vs Sporting Lisbon | Home | 2-1 | 2 | deep | 0-2 (away) | ✗ | ✗ |
| 2026-10-13 | Sabah FK vs Slavia Praha | Away | 0-1 | 3 | quick | 2-0 (home) | ✗ | ✗ |
| 2026-10-13 | Arsenal vs Lille | Home | 2-0 | 5 | quick | 3-0 (home) | ✓ | ✗ |
| 2026-10-13 | Atlético Madrid vs Manchester United | Home | 2-1 | 3 | deep | 2-0 (home) | ✓ | ✗ |
| 2026-10-13 | Galatasaray vs Barcelona | Away | 1-2 | 5 | quick | 1-4 (away) | ✓ | ✗ |
| 2026-10-13 | Viking FK vs Bayern Munich | Away | 0-3 | 5 | quick | 3-3 (draw) | ✗ | ✗ |
| 2026-10-13 | Inter Milan vs Club Brugge | Home | 2-0 | 5 | quick | 3-4 (away) | ✗ | ✗ |
| 2026-10-13 | Villarreal vs Napoli | Home | 1-0 | 2 | deep | 3-1 (home) | ✓ | ✗ |
| 2026-10-13 | RB Leipzig vs PSV Eindhoven | Home | 2-1 | 3 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-10-14 | Feyenoord vs Como | Away | 1-2 | 3 | quick | 3-2 (home) | ✗ | ✗ |
| 2026-10-14 | LASK vs Liverpool | Away | 0-2 | 5 | quick | 3-6 (away) | ✓ | ✗ |
| 2026-10-14 | Shakhtar Donetsk vs AEK Athens | Away | 0-1 | 1 | deep | 3-1 (home) | ✗ | ✗ |
| 2026-10-14 | AS Roma vs Real Madrid | Away | 1-2 | 2 | deep | 3-4 (away) | ✓ | ✗ |
| 2026-10-14 | Aston Villa vs Fenerbahce | Home | 2-1 | 4 | quick | 6-0 (home) | ✓ | ✗ |
| 2026-10-14 | Bodø/Glimt vs Borussia Dortmund | Away | 1-2 | 3 | quick | 1-0 (home) | ✗ | ✗ |
| 2026-10-14 | Manchester City vs Paris Saint Germain | Home | 2-1 | 3 | deep | 2-4 (away) | ✗ | ✗ |
| 2026-10-14 | Real Betis vs Porto | Home | 1-0 | 3 | quick | 3-2 (home) | ✓ | ✗ |
| 2026-10-14 | ŠK Slovan Bratislava vs VfB Stuttgart | Away | 0-2 | 5 | quick | 0-3 (away) | ✓ | ✗ |
