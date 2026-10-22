# Prediction accuracy log

Immutable record of calls vs outcomes. Never edit a prediction after kickoff.

## Running tally
- Matches predicted (graded): 54
- Correct picks (1X2): 34 — hit rate 63% (34/54)
- Exact scoreline hits: 2 (Real Madrid 2-1, Liverpool 2-1)
- Avg confidence of correct picks: 4.03
- Avg confidence of wrong picks: 3.15
- Deep: 7/18 (39%), 1 exact. Quick: 27/36 (75%), 1 exact.
- Blind market-favourite control: 34/54 — identical, because no pick on any card so far deviated from the favourite.
- MD3 night two (21 Oct): 6/9. Deep 2/4 (Como beat Manchester United 4-1 and Club Brugge beat RC Lens 3-0; Galatasaray won 4-2 at Lille and Bayern Munich drew 2-2 with Arsenal). Quick 4/5; the miss was a 5-confidence pick, LASK winning 3-2 at Sporting Lisbon.
- MD3 night one (20 Oct): 5/9. Deep 0/2 (VfB Stuttgart drew 1-1 with Atlético Madrid; Paris Saint Germain beat Barcelona 4-2 in the 39/22/40 coin-flip). Quick 5/7; the misses were Fenerbahce 2-2 Slavia Praha and Porto 0-1 PSV Eindhoven. No exact scores all matchday, again.
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
| 2026-10-20 | Sabah FK vs Borussia Dortmund | Away | 0-2 | 5 | quick | 1-2 (away) | ✓ | ✗ |
| 2026-10-20 | Fenerbahce vs Slavia Praha | Home | 2-1 | 4 | quick | 2-2 (draw) | ✗ | ✗ |
| 2026-10-20 | Manchester City vs AEK Athens | Home | 3-0 | 5 | quick | 5-1 (home) | ✓ | ✗ |
| 2026-10-20 | AS Roma vs ŠK Slovan Bratislava | Home | 3-0 | 5 | quick | 4-0 (home) | ✓ | ✗ |
| 2026-10-20 | VfB Stuttgart vs Atlético Madrid | Away | 1-2 | 3 | deep | 1-1 (draw) | ✗ | ✗ |
| 2026-10-20 | Paris Saint Germain vs Barcelona | Away | 2-3 | 1 | deep | 4-2 (home) | ✗ | ✗ |
| 2026-10-20 | Napoli vs Bodø/Glimt | Home | 2-1 | 3 | quick | 4-3 (home) | ✓ | ✗ |
| 2026-10-20 | Liverpool vs Villarreal | Home | 2-1 | 4 | quick | 4-3 (home) | ✓ | ✗ |
| 2026-10-20 | Porto vs PSV Eindhoven | Home | 2-1 | 4 | quick | 0-1 (away) | ✗ | ✗ |
| 2026-10-21 | Como vs Manchester United | Home | 2-1 | 3 | deep | 4-1 (home) | ✓ | ✗ |
| 2026-10-21 | Lille vs Galatasaray | Home | 2-1 | 3 | deep | 2-4 (away) | ✗ | ✗ |
| 2026-10-21 | Bayern Munich vs Arsenal | Home | 2-1 | 2 | deep | 2-2 (draw) | ✗ | ✗ |
| 2026-10-21 | Aston Villa vs Viking FK | Home | 2-0 | 5 | quick | 3-1 (home) | ✓ | ✗ |
| 2026-10-21 | Club Brugge vs RC Lens | Home | 2-1 | 3 | deep | 3-0 (home) | ✓ | ✗ |
| 2026-10-21 | Real Betis vs Feyenoord | Home | 2-1 | 4 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-10-21 | Inter Milan vs Shakhtar Donetsk | Home | 2-0 | 5 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-10-21 | Sporting Lisbon vs LASK | Home | 2-0 | 5 | quick | 2-3 (away) | ✗ | ✗ |
| 2026-10-21 | Real Madrid vs RB Leipzig | Home | 2-1 | 5 | quick | 4-1 (home) | ✓ | ✗ |
