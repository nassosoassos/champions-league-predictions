# Prediction accuracy log

Immutable record of calls vs outcomes. Never edit a prediction after kickoff.

## Running tally
- Matches predicted (graded): 81
- Correct picks (1X2): 55 — hit rate 68% (55/81)
- Exact scoreline hits: 5 (Real Madrid 2-1, Liverpool 2-1, Shakhtar Donetsk 0-1 Sporting Lisbon, Borussia Dortmund 2-1 Real Betis, ŠK Slovan Bratislava 0-2 Real Betis)
- Avg confidence of correct picks: 3.95
- Avg confidence of wrong picks: 3.27
- Deep: 14/26 (54%), 1 exact. Quick: 41/55 (75%), 4 exact.
- Blind market-favourite control: 55/81 — identical, because no pick on any card so far deviated from the favourite.
- MD5 night one (24 Nov): 6/9. Deep 1/2: Porto won 1-0 at Feyenoord, while Galatasaray beat Aston Villa 1-0 at home against a 43% Villa favourite. Quick 5/7. Both misses were draws: Manchester City 2-2 Napoli (conf 5) and Arsenal 1-1 Borussia Dortmund (conf 4). One exact score, ŠK Slovan Bratislava 0-2 Real Betis. Night two (25 Nov) is still to be graded.
- MD4 (3-4 Nov): 15/18. Deep 6/6 — the first perfect deep card: Galatasaray 2-0 VfB Stuttgart, Manchester United 3-2 AS Roma, Atlético Madrid 0-2 Bayern Munich, Feyenoord 0-3 Inter Milan, RC Lens 1-9 Como (a record-equalling margin, picked at confidence 3) and Porto 4-1 Napoli; every one of them was a market favourite, so the blind control scored the same. Quick 9/12; the misses were Bodø/Glimt 0-0 Lille (conf 4), Fenerbahce 3-2 Liverpool (conf 4, Liverpool's first league-phase defeat) and PSV Eindhoven 1-2 Club Brugge (conf 3). Two exact scores, Shakhtar Donetsk 0-1 Sporting Lisbon and Borussia Dortmund 2-1 Real Betis, the first exact hits since MD1. Cutlines moved between the MD3 and MD4 tables: Como (9th to 4th) and Manchester City (10th to 7th) climbed into the top eight, pushing out Real Betis (5th to 11th) and VfB Stuttgart (6th to 14th); Fenerbahce (31st to 19th) and Viking FK (33rd to 22nd) climbed into the knockout play-off places, while Napoli (22nd to 27th) and Villarreal (19th to 28th) fell out of them.
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
| 2026-11-03 | Galatasaray vs VfB Stuttgart | Home | 2-1 | 3 | deep | 2-0 (home) | ✓ | ✗ |
| 2026-11-03 | Shakhtar Donetsk vs Sporting Lisbon | Away | 0-1 | 3 | quick | 0-1 (away) | ✓ | ✓ |
| 2026-11-03 | Manchester United vs AS Roma | Home | 2-1 | 2 | deep | 3-2 (home) | ✓ | ✗ |
| 2026-11-03 | Barcelona vs Aston Villa | Home | 2-0 | 5 | quick | 3-0 (home) | ✓ | ✗ |
| 2026-11-03 | Atlético Madrid vs Bayern Munich | Away | 1-2 | 2 | deep | 0-2 (away) | ✓ | ✗ |
| 2026-11-03 | Bodø/Glimt vs Lille | Home | 2-1 | 4 | quick | 0-0 (draw) | ✗ | ✗ |
| 2026-11-03 | Feyenoord vs Inter Milan | Away | 1-2 | 3 | deep | 0-3 (away) | ✓ | ✗ |
| 2026-11-03 | LASK vs ŠK Slovan Bratislava | Home | 2-0 | 5 | quick | 4-0 (home) | ✓ | ✗ |
| 2026-11-03 | Villarreal vs Paris Saint Germain | Away | 1-2 | 4 | quick | 0-6 (away) | ✓ | ✗ |
| 2026-11-04 | AEK Athens vs Real Madrid | Away | 0-2 | 5 | quick | 2-3 (away) | ✓ | ✗ |
| 2026-11-04 | Fenerbahce vs Liverpool | Away | 1-2 | 4 | quick | 3-2 (home) | ✗ | ✗ |
| 2026-11-04 | Slavia Praha vs Arsenal | Away | 0-2 | 5 | quick | 1-2 (away) | ✓ | ✗ |
| 2026-11-04 | Borussia Dortmund vs Real Betis | Home | 2-1 | 3 | quick | 2-1 (home) | ✓ | ✓ |
| 2026-11-04 | PSV Eindhoven vs Club Brugge | Home | 1-0 | 3 | quick | 1-2 (away) | ✗ | ✗ |
| 2026-11-04 | RC Lens vs Como | Away | 1-2 | 3 | deep | 1-9 (away) | ✓ | ✗ |
| 2026-11-04 | RB Leipzig vs Manchester City | Away | 1-2 | 4 | quick | 2-3 (away) | ✓ | ✗ |
| 2026-11-04 | Porto vs Napoli | Home | 2-1 | 3 | deep | 4-1 (home) | ✓ | ✗ |
| 2026-11-04 | Viking FK vs Sabah FK | Home | 2-1 | 4 | quick | 4-1 (home) | ✓ | ✗ |
| 2026-11-24 | Galatasaray vs Aston Villa | Away | 1-2 | 2 | deep | 1-0 (home) | ✗ | ✗ |
| 2026-11-24 | Bodø/Glimt vs LASK | Home | 2-1 | 4 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-11-24 | Como vs AEK Athens | Home | 2-0 | 5 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-11-24 | Arsenal vs Borussia Dortmund | Home | 2-1 | 4 | quick | 1-1 (draw) | ✗ | ✗ |
| 2026-11-24 | Feyenoord vs Porto | Away | 1-2 | 3 | deep | 0-1 (away) | ✓ | ✗ |
| 2026-11-24 | Manchester City vs Napoli | Home | 2-0 | 5 | quick | 2-2 (draw) | ✗ | ✗ |
| 2026-11-24 | Real Madrid vs PSV Eindhoven | Home | 2-0 | 5 | quick | 5-1 (home) | ✓ | ✗ |
| 2026-11-24 | RB Leipzig vs RC Lens | Home | 2-1 | 4 | quick | 3-1 (home) | ✓ | ✗ |
| 2026-11-24 | ŠK Slovan Bratislava vs Real Betis | Away | 0-2 | 5 | quick | 0-2 (away) | ✓ | ✓ |
