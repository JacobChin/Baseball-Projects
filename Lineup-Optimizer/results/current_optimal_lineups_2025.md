# Current 2025 Optimal Lineups

Settings: empirical Statcast transition model, empirical speed-attempt advancement model, revised neutralized 2B/3B steal rates, contextual BB model enabled.

- Clone games per hitter: 1,000
- Search candidate pool size: 70
- Candidate lineups per search: up to 200
- Screen games per batting order: 25
- Random batting orders per lineup: 6
- Final games per finalist: 3,000
- Runtime: 1130.8 seconds

## Clone Lineups

| rank | player_name      | team | runs_per_9 | ci95_half_width | woba  | obp   | slg   | bb_rate | k_rate | sprint_speed |
| ---- | ---------------- | ---- | ---------- | --------------- | ----- | ----- | ----- | ------- | ------ | ------------ |
| 1    | Aaron Judge      | NYY  | 8.984      | 0.284           | 0.463 | 0.457 | 0.688 | 0.183   | 0.236  | 27.100       |
| 2    | Nick Kurtz       | ATH  | 7.363      | 0.258           | 0.419 | 0.383 | 0.619 | 0.129   | 0.309  | 27.100       |
| 3    | Shohei Ohtani    | LAD  | 7.234      | 0.236           | 0.418 | 0.392 | 0.622 | 0.150   | 0.257  | 28.000       |
| 4    | Ronald Acuña Jr. | ATL  | 7.038      | 0.240           | 0.403 | 0.417 | 0.518 | 0.172   | 0.248  | 27.900       |
| 5    | George Springer  | TOR  | 6.672      | 0.231           | 0.408 | 0.399 | 0.560 | 0.118   | 0.189  | 28.000       |
| 6    | Kyle Schwarber   | PHI  | 6.621      | 0.238           | 0.391 | 0.365 | 0.563 | 0.149   | 0.272  | 25.900       |
| 7    | Cal Raleigh      | SEA  | 6.497      | 0.224           | 0.392 | 0.359 | 0.589 | 0.138   | 0.267  | 26.000       |
| 8    | Juan Soto        | NYM  | 6.448      | 0.244           | 0.390 | 0.396 | 0.525 | 0.178   | 0.192  | 25.800       |
| 9    | Will Smith       | LAD  | 6.317      | 0.231           | 0.389 | 0.404 | 0.497 | 0.147   | 0.204  | 27.300       |
| 10   | Roman Anthony    | BOS  | 6.156      | 0.230           | 0.376 | 0.396 | 0.463 | 0.132   | 0.277  | 27.800       |
| 11   | Ketel Marte      | ARI  | 6.145      | 0.221           | 0.381 | 0.376 | 0.517 | 0.115   | 0.149  | 26.600       |
| 12   | Jonathan Aranda  | TBR  | 5.902      | 0.221           | 0.381 | 0.393 | 0.489 | 0.097   | 0.254  | 25.900       |
| 13   | Kyle Stowers     | MIA  | 5.869      | 0.215           | 0.386 | 0.368 | 0.544 | 0.105   | 0.274  | 27.100       |
| 14   | Byron Buxton     | MIN  | 5.835      | 0.209           | 0.367 | 0.327 | 0.551 | 0.076   | 0.273  | 30.200       |
| 15   | Michael Busch    | CHC  | 5.788      | 0.211           | 0.369 | 0.343 | 0.523 | 0.095   | 0.235  | 26.500       |

## Best No-Duplicate Lineups

| rank | runs_per_9 | ci95_half_width | label                    | best_order_label         | lineup_order                                                                                                                                      |
| ---- | ---------- | --------------- | ------------------------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | 6.871      | 0.136           | top 9 by search_priority | Selected order rotated 4 | Will Smith / Shohei Ohtani / Juan Soto / Cal Raleigh / Nick Kurtz / George Springer / Aaron Judge / Kyle Schwarber / Ronald Acuña Jr.             |
| 2    | 6.599      | 0.135           | weighted random 73       | single_per_ab descending | Bo Bichette / Will Smith / Ronald Acuña Jr. / George Springer / Aaron Judge / Juan Soto / Nick Kurtz / Byron Buxton / Cal Raleigh                 |
| 3    | 6.476      | 0.135           | weighted random 153      | bsr high-low             | Shohei Ohtani / Rafael Devers / George Springer / Aaron Judge / Nick Kurtz / Isaac Paredes / Kyle Schwarber / Will Smith / Freddie Freeman        |
| 4    | 6.437      | 0.126           | top 9 by iso             | iso descending           | Aaron Judge / Cal Raleigh / Shohei Ohtani / Nick Kurtz / Kyle Schwarber / Eugenio Suárez / Byron Buxton / Corbin Carroll / Junior Caminero        |
| 5    | 6.418      | 0.130           | weighted random 102      | Selected order rotated 7 | Shea Langeliers / Nick Kurtz / George Springer / Aaron Judge / Alex Bregman / Will Smith / Shohei Ohtani / Juan Soto / Bobby Witt Jr.             |
| 6    | 6.347      | 0.132           | weighted random 3        | woba high-low            | Aaron Judge / Alex Bregman / Nick Kurtz / Rafael Devers / Ronald Acuña Jr. / Vladimir Guerrero Jr. / Cal Raleigh / Juan Soto / Kyle Schwarber     |
| 7    | 6.346      | 0.135           | weighted random 155      | single_per_ab high-low   | Ronald Acuña Jr. / Cal Raleigh / George Springer / Max Muncy / Roman Anthony / Kyle Stowers / Aaron Judge / Ketel Marte / José Ramírez            |
| 8    | 6.330      | 0.130           | weighted random 177      | iso high-low             | Aaron Judge / Miguel Andujar / Shohei Ohtani / Will Smith / Kyle Schwarber / Max Muncy / Corbin Carroll / George Springer / Juan Soto             |
| 9    | 6.329      | 0.130           | weighted random 114      | bb_per_k high-low        | Kyle Tucker / Bobby Witt Jr. / Aaron Judge / Nick Kurtz / George Springer / Freddie Freeman / Rafael Devers / Roman Anthony / Shohei Ohtani       |
| 10   | 6.291      | 0.131           | weighted random 118      | obp high-low             | George Springer / Bo Bichette / Shohei Ohtani / Cal Raleigh / Nick Kurtz / Jeremy Peña / Vladimir Guerrero Jr. / Kyle Schwarber / Freddie Freeman |

## Best Position-Constrained Lineups

| rank | runs_per_9 | ci95_half_width | label                                        | best_order_label                | lineup_order                                                                                                                                    | position_assignment                                                                                                                                                                     |
| ---- | ---------- | --------------- | -------------------------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | 6.819      | 0.134           | position-constrained top by search_priority  | Random order 2                  | Nick Kurtz / George Springer / Aaron Judge / Shohei Ohtani / Ronald Acuña Jr. / Jonathan Aranda / Cal Raleigh / Geraldo Perdomo / Ketel Marte   | C: Cal Raleigh; CIF1: Nick Kurtz; CIF2: Jonathan Aranda; MIF1: Ketel Marte; MIF2: Geraldo Perdomo; OF1: Aaron Judge; OF2: George Springer; OF3: Ronald Acuña Jr.; UTIL: Shohei Ohtani   |
| 2    | 6.634      | 0.138           | position-constrained top by clone_runs_per_9 | hr_per_ab ascending             | Jeremy Peña / Jonathan Aranda / Ketel Marte / Ronald Acuña Jr. / George Springer / Nick Kurtz / Shohei Ohtani / Aaron Judge / Cal Raleigh       | C: Cal Raleigh; CIF1: Nick Kurtz; CIF2: Jonathan Aranda; MIF1: Ketel Marte; MIF2: Jeremy Peña; OF1: Aaron Judge; OF2: George Springer; OF3: Ronald Acuña Jr.; UTIL: Shohei Ohtani       |
| 3    | 6.487      | 0.134           | position-constrained weighted random 69      | wrc_plus descending             | Aaron Judge / Shohei Ohtani / Nick Kurtz / Cal Raleigh / Juan Soto / Geraldo Perdomo / Max Muncy / Kyle Tucker / Bryce Harper                   | C: Cal Raleigh; CIF1: Nick Kurtz; CIF2: Bryce Harper; MIF1: Geraldo Perdomo; MIF2: Max Muncy; OF1: Aaron Judge; OF2: Juan Soto; OF3: Kyle Tucker; UTIL: Shohei Ohtani                   |
| 4    | 6.426      | 0.134           | position-constrained priority window 3       | Random order 2                  | Jonathan Aranda / Ronald Acuña Jr. / Ketel Marte / Geraldo Perdomo / Kyle Schwarber / Juan Soto / Cal Raleigh / George Springer / Nick Kurtz    | C: Cal Raleigh; CIF1: Nick Kurtz; CIF2: Jonathan Aranda; MIF1: Ketel Marte; MIF2: Geraldo Perdomo; OF1: George Springer; OF2: Ronald Acuña Jr.; OF3: Juan Soto; UTIL: Kyle Schwarber    |
| 5    | 6.393      | 0.132           | position-constrained weighted random 144     | slg high-low                    | Aaron Judge / Max Muncy / Nick Kurtz / Yandy Díaz / George Springer / Will Smith / Juan Soto / Freddie Freeman / Ketel Marte                    | C: Will Smith; CIF1: Nick Kurtz; CIF2: Freddie Freeman; MIF1: Ketel Marte; MIF2: Max Muncy; OF1: Aaron Judge; OF2: George Springer; OF3: Juan Soto; UTIL: Yandy Díaz                    |
| 6    | 6.393      | 0.133           | position-constrained priority window 2       | slg ascending                   | Geraldo Perdomo / Jonathan Aranda / Ketel Marte / Ronald Acuña Jr. / Juan Soto / George Springer / Cal Raleigh / Nick Kurtz / Shohei Ohtani     | C: Cal Raleigh; CIF1: Nick Kurtz; CIF2: Jonathan Aranda; MIF1: Ketel Marte; MIF2: Geraldo Perdomo; OF1: George Springer; OF2: Ronald Acuña Jr.; OF3: Juan Soto; UTIL: Shohei Ohtani     |
| 7    | 6.377      | 0.132           | position-constrained weighted random 77      | single_per_ab high-low          | Geraldo Perdomo / Corbin Carroll / Ronald Acuña Jr. / Nick Kurtz / Freddie Freeman / Shea Langeliers / Aaron Judge / Kyle Stowers / Ketel Marte | C: Shea Langeliers; CIF1: Nick Kurtz; CIF2: Freddie Freeman; MIF1: Ketel Marte; MIF2: Geraldo Perdomo; OF1: Aaron Judge; OF2: Ronald Acuña Jr.; OF3: Kyle Stowers; UTIL: Corbin Carroll |
| 8    | 6.368      | 0.131           | position-constrained weighted random 35      | bb_rate descending              | Aaron Judge / Ronald Acuña Jr. / Will Smith / Geraldo Perdomo / Nick Kurtz / Ketel Marte / Corbin Carroll / Freddie Freeman / Francisco Lindor  | C: Will Smith; CIF1: Nick Kurtz; CIF2: Freddie Freeman; MIF1: Ketel Marte; MIF2: Geraldo Perdomo; OF1: Aaron Judge; OF2: Ronald Acuña Jr.; OF3: Corbin Carroll; UTIL: Francisco Lindor  |
| 9    | 6.300      | 0.132           | position-constrained weighted random 129     | Sabermetric heuristic rotated 4 | Corbin Carroll / Geraldo Perdomo / Yandy Díaz / Ben Rice / Trea Turner / Aaron Judge / Nick Kurtz / George Springer / Shohei Ohtani             | C: Ben Rice; CIF1: Nick Kurtz; CIF2: Yandy Díaz; MIF1: Geraldo Perdomo; MIF2: Trea Turner; OF1: Aaron Judge; OF2: George Springer; OF3: Corbin Carroll; UTIL: Shohei Ohtani             |
| 10   | 6.294      | 0.133           | position-constrained weighted random 145     | bsr ascending                   | Jonathan Aranda / Aaron Judge / Will Smith / Alex Bregman / Ronald Acuña Jr. / George Springer / Geraldo Perdomo / Kyle Tucker / Bobby Witt Jr. | C: Will Smith; CIF1: Jonathan Aranda; CIF2: Alex Bregman; MIF1: Geraldo Perdomo; MIF2: Bobby Witt Jr.; OF1: Aaron Judge; OF2: George Springer; OF3: Ronald Acuña Jr.; UTIL: Kyle Tucker |

Note: the no-duplicate and positional searches are heuristic player-set searches, not exhaustive enumerations of every 9-player combination.