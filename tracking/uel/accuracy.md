# Prediction accuracy log — Europa League

Immutable record of calls vs outcomes. Never edit a prediction after kickoff.

## Running tally
- Matches predicted (graded): 54
- Correct picks (1X2): 34 — hit rate 63% (34/54)
- Exact scoreline hits: 8 (Bayer Leverkusen 2-0, Olympiakos Piraeus 2-1, Levski Sofia 0-1, Real Sociedad 1-2, Sunderland 1-2, Ferencváros TC 2-1, OFI Crete–Bayer Leverkusen 0-2, Celtic–Celta Vigo 1-2)
- Avg confidence of correct picks: 3.74
- Avg confidence of wrong picks: 3.40
- Deep: 5/9 (56%), 2 exact. Quick: 29/45 (64%), 6 exact.
- Blind market-favourite control: 34/54. Identical to our record because no pick on any card deviated from the favourite.

**Notes (MD3, 22 Oct):** 11/18, 2 exact. Deep 2/3: Bournemouth beat AC Milan 3-0 and Celta Vigo won 2-1 at Celtic (exact score, on a confidence-2 pick); Besiktas JK–Crystal Palace finished 2-2. Quick 9/15; four of the six misses were draws (Juventus–Rennes, Besiktas–Palace, NK Celje–Salzburg 2-2; Lech Poznań–Sunderland 1-1), plus away upsets at Dinamo Zagreb (2-4 to NEC Nijmegen) and Viktoria Plzeň (1-2 to Levski Sofia) and Sturm Graz's 1-0 home win over Marseille. Every miss was at confidence 3-4; all three confidence-5 picks hit.

**Notes (MD2, 15 Oct):** 12/18, 2 exact. Deep 1/3: Juventus won 2-1 at Celta Vigo; Omonoia FC won 3-0 at NK Celje and Olympiakos Piraeus won 1-0 at Marseille, both against the market. Quick 11/15; three of the four misses were draws (Sparta Prague–Lillestrom, Union Saint-Gilloise–Real Sociedad, NEC Nijmegen–Levski Sofia, all 1-1). Confidence separated better than in MD1 (3.70 vs 3.23 overall).

**Notes (MD1):**
Deep vs quick is not a test of research. On the three deep matches the blind favourite also went 2/3, so research changed no pick and the pick-level result is the same by construction.
Confidence barely separated correct from wrong picks (3.45 vs 3.43). That is a weaker signal than in the UCL, where it was 4.08 vs 3.20. Two draws (Hapoel Be'er Sheva–Dinamo Zagreb and Sturm Graz–Rennes, both 0-0) and three home upsets (Omonoia, OFI Crete, Lillestrom) cost 4-confidence and 3-confidence picks.

## Log
| Date | Match | Pick | Score guess | Conf | Depth | Actual | Pick hit? | Score hit? |
|------|-------|------|-------------|------|-------|--------|-----------|------------|
| 2026-09-16 | Omonoia FC vs Celta Vigo | Away | 0-1 | 3 | quick | 1-0 (home) | ✗ | ✗ |
| 2026-09-16 | FC Ararat-Armenia vs Sparta Prague | Away | 1-2 | 4 | quick | 1-4 (away) | ✓ | ✗ |
| 2026-09-16 | AC Milan vs Benfica | Home | 2-1 | 3 | deep | 0-2 (away) | ✗ | ✗ |
| 2026-09-16 | Sunderland vs AZ Alkmaar | Home | 2-1 | 4 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-09-16 | Anderlecht vs Lyon | Away | 0-1 | 3 | quick | 1-2 (away) | ✓ | ✗ |
| 2026-09-16 | Bayer Leverkusen vs NK Celje | Home | 2-0 | 5 | quick | 2-0 (home) | ✓ | ✓ |
| 2026-09-16 | Hapoel Be'er Sheva vs Dinamo Zagreb | Away | 0-1 | 3 | quick | 0-0 (draw) | ✗ | ✗ |
| 2026-09-16 | Olympiakos Piraeus vs Jagiellonia Białystok | Home | 2-1 | 4 | quick | 2-1 (home) | ✓ | ✓ |
| 2026-09-16 | SK Sturm Graz vs Rennes | Away | 0-1 | 3 | quick | 0-0 (draw) | ✗ | ✗ |
| 2026-09-17 | OFI Crete vs TSG Hoffenheim | Away | 1-2 | 4 | quick | 2-0 (home) | ✗ | ✗ |
| 2026-09-17 | PFC Levski Sofia vs Salzburg | Away | 0-1 | 3 | quick | 0-1 (away) | ✓ | ✓ |
| 2026-09-17 | Besiktas JK vs Marseille | Home | 2-1 | 3 | quick | 4-1 (home) | ✓ | ✗ |
| 2026-09-17 | Real Sociedad vs Bournemouth | Away | 1-2 | 1 | deep | 1-2 (away) | ✓ | ✓ |
| 2026-09-17 | Celtic vs Ferencváros TC | Home | 2-1 | 4 | quick | 1-3 (away) | ✗ | ✗ |
| 2026-09-17 | Crystal Palace vs Lech Poznań | Home | 2-1 | 4 | quick | 4-0 (home) | ✓ | ✗ |
| 2026-09-17 | Juventus vs NEC Nijmegen | Home | 2-1 | 5 | quick | 5-0 (home) | ✓ | ✗ |
| 2026-09-17 | Lillestrom vs Torreense | Home | 2-1 | 4 | quick | 1-2 (away) | ✗ | ✗ |
| 2026-09-17 | Viktoria Plzeň vs Union Saint-Gilloise | Away | 1-2 | 2 | deep | 0-3 (away) | ✓ | ✗ |
| 2026-10-15 | Salzburg vs AC Milan | Away | 0-1 | 3 | quick | 0-4 (away) | ✓ | ✗ |
| 2026-10-15 | AZ Alkmaar vs Hapoel Be'er Sheva | Home | 2-0 | 5 | quick | 2-1 (home) | ✓ | ✗ |
| 2026-10-15 | Lech Poznań vs Bayer Leverkusen | Away | 1-2 | 4 | quick | 0-4 (away) | ✓ | ✗ |
| 2026-10-15 | Lyon vs Crystal Palace | Home | 1-0 | 3 | quick | 3-2 (home) | ✓ | ✗ |
| 2026-10-15 | Sparta Prague vs Lillestrom | Home | 2-0 | 5 | quick | 1-1 (draw) | ✗ | ✗ |
| 2026-10-15 | NK Celje vs Omonoia FC | Home | 1-0 | 2 | deep | 0-3 (away) | ✗ | ✗ |
| 2026-10-15 | Union Saint-Gilloise vs Real Sociedad | Home | 1-0 | 2 | quick | 1-1 (draw) | ✗ | ✗ |
| 2026-10-15 | Torreense vs Sunderland | Away | 1-2 | 4 | quick | 1-2 (away) | ✓ | ✓ |
| 2026-10-15 | Dinamo Zagreb vs Anderlecht | Home | 2-1 | 3 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-10-15 | Benfica vs Celtic | Home | 2-0 | 5 | quick | 4-1 (home) | ✓ | ✗ |
| 2026-10-15 | TSG Hoffenheim vs Besiktas JK | Home | 2-1 | 3 | quick | 2-3 (away) | ✗ | ✗ |
| 2026-10-15 | Bournemouth vs SK Sturm Graz | Home | 2-0 | 5 | quick | 3-0 (home) | ✓ | ✗ |
| 2026-10-15 | Celta Vigo vs Juventus | Away | 0-1 | 3 | deep | 1-2 (away) | ✓ | ✗ |
| 2026-10-15 | Jagiellonia Białystok vs FC Ararat-Armenia | Home | 2-1 | 4 | quick | 3-1 (home) | ✓ | ✗ |
| 2026-10-15 | Ferencváros TC vs Viktoria Plzeň | Home | 2-1 | 3 | quick | 2-1 (home) | ✓ | ✓ |
| 2026-10-15 | Marseille vs Olympiakos Piraeus | Home | 1-0 | 3 | deep | 0-1 (away) | ✗ | ✗ |
| 2026-10-15 | NEC Nijmegen vs PFC Levski Sofia | Home | 2-1 | 3 | quick | 1-1 (draw) | ✗ | ✗ |
| 2026-10-15 | Rennes vs OFI Crete | Home | 2-0 | 5 | quick | 2-1 (home) | ✓ | ✗ |
| 2026-10-22 | FC Ararat-Armenia vs AZ Alkmaar | Away | 1-2 | 4 | quick | 0-4 (away) | ✓ | ✗ |
| 2026-10-22 | OFI Crete vs Bayer Leverkusen | Away | 0-2 | 5 | quick | 0-2 (away) | ✓ | ✓ |
| 2026-10-22 | Dinamo Zagreb vs NEC Nijmegen | Home | 2-1 | 4 | quick | 2-4 (away) | ✗ | ✗ |
| 2026-10-22 | Ferencváros TC vs Torreense | Home | 2-0 | 5 | quick | 4-1 (home) | ✓ | ✗ |
| 2026-10-22 | Union Saint-Gilloise vs Hapoel Be'er Sheva | Home | 2-1 | 4 | quick | 4-0 (home) | ✓ | ✗ |
| 2026-10-22 | Juventus vs Rennes | Home | 2-1 | 4 | quick | 2-2 (draw) | ✗ | ✗ |
| 2026-10-22 | Lech Poznań vs Sunderland | Away | 1-2 | 4 | quick | 1-1 (draw) | ✗ | ✗ |
| 2026-10-22 | SK Sturm Graz vs Marseille | Away | 1-2 | 3 | quick | 1-0 (home) | ✗ | ✗ |
| 2026-10-22 | Bournemouth vs AC Milan | Home | 2-1 | 3 | deep | 3-0 (home) | ✓ | ✗ |
| 2026-10-22 | Jagiellonia Białystok vs Anderlecht | Away | 0-1 | 3 | quick | 0-3 (away) | ✓ | ✗ |
| 2026-10-22 | Omonoia FC vs Benfica | Away | 0-2 | 5 | quick | 1-4 (away) | ✓ | ✗ |
| 2026-10-22 | Besiktas JK vs Crystal Palace | Home | 2-1 | 3 | deep | 2-2 (draw) | ✗ | ✗ |
| 2026-10-22 | Celtic vs Celta Vigo | Away | 1-2 | 2 | deep | 1-2 (away) | ✓ | ✓ |
| 2026-10-22 | Lillestrom vs Real Sociedad | Away | 1-2 | 4 | quick | 0-6 (away) | ✓ | ✗ |
| 2026-10-22 | TSG Hoffenheim vs Lyon | Home | 2-1 | 3 | quick | 3-0 (home) | ✓ | ✗ |
| 2026-10-22 | NK Celje vs Salzburg | Away | 1-2 | 4 | quick | 2-2 (draw) | ✗ | ✗ |
| 2026-10-22 | Olympiakos Piraeus vs Sparta Prague | Home | 2-1 | 4 | quick | 1-0 (home) | ✓ | ✗ |
| 2026-10-22 | Viktoria Plzeň vs PFC Levski Sofia | Home | 2-1 | 4 | quick | 1-2 (away) | ✗ | ✗ |
