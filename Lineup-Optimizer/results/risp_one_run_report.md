# 2025 Clone Lineups: One-Run Probability From A RISP Situation

Objective: estimate `P(score >= 1 run before 3 outs)` for nine-player clone lineups when the starting base/out state is drawn from the empirical 2025 distribution of plate appearances with at least one runner in scoring position.

## Interpretation

- This is an exploratory 10,000-trial sweep, not a final high-precision ordering.
- All 18 combinations of six RISP base states and 0/1/2 outs are included.
- Every hitter receives the same deterministic, frequency-matched allocation of starting states, preventing context-mix noise from affecting player comparisons.
- Every occupied base initially contains the same cloned hitter, preserving that player's running profile.
- Contextual walks, direct-movement BIP transitions, empirical Sprint-Speed advancement, fitted GDP, and production behavioral stolen bases are enabled.
- Bunting and optimized decisions are not included.

## Settings

- Qualified hitters: 277
- Trials per hitter: 10,000
- Empirical RISP PA used for weights: 46,399
- Deterministic seed: `202510270`
- Workers: `8`
- Runtime: 139.1 seconds

## Starting-State Weights

|   outs | base_state   | base_state_label   |   situation_pa |   weight_pct |
|-------:|:-------------|:-------------------|---------------:|-------------:|
|      0 | --3          | 3rd                |            281 |       0.6056 |
|      0 | -2-          | 2nd                |           2941 |       6.3385 |
|      0 | -23          | 2nd_3rd            |            610 |       1.3147 |
|      0 | 1-3          | 1st_3rd            |            873 |       1.8815 |
|      0 | 12-          | 1st_2nd            |           3358 |       7.2372 |
|      0 | 123          | loaded             |            911 |       1.9634 |
|      1 | --3          | 3rd                |           1361 |       2.9333 |
|      1 | -2-          | 2nd                |           4229 |       9.1144 |
|      1 | -23          | 2nd_3rd            |           1482 |       3.194  |
|      1 | 1-3          | 1st_3rd            |           1900 |       4.0949 |
|      1 | 12-          | 1st_2nd            |           5401 |      11.6403 |
|      1 | 123          | loaded             |           1986 |       4.2803 |
|      2 | --3          | 3rd                |           2303 |       4.9635 |
|      2 | -2-          | 2nd                |           5399 |      11.636  |
|      2 | -23          | 2nd_3rd            |           1579 |       3.4031 |
|      2 | 1-3          | 1st_3rd            |           2513 |       5.4161 |
|      2 | 12-          | 1st_2nd            |           6698 |      14.4357 |
|      2 | 123          | loaded             |           2574 |       5.5475 |

## Ranking Comparison

- Spearman rank correlation with bases-empty one-run leaderboard: `0.739`
- Spearman rank correlation with runs/9 leaderboard: `0.730`
- Top-10 overlap with bases-empty one-run leaderboard: `4/10`
- Top-25 overlap with bases-empty one-run leaderboard: `15/25`
- Negative rank change means a hitter ranks better in the RISP-start leaderboard.

## Main Findings

- `Aaron Judge` has the highest point estimate at `49.90%`.
- The estimated lead over `Jeremy Peña` is `1.21` percentage points (approximate 95% interval `-0.08` to `2.50`), so the exact top ordering is not yet statistically secure.
- The largest positive rank mover is `Chandler Simpson`, moving from bases-empty rank `157` to RISP rank `23`.
- The largest negative rank mover is `Eugenio Suárez`, moving from bases-empty rank `36` to RISP rank `215`.
- Because every starting runner is also the cloned hitter, this leaderboard measures the combined batting and baserunning value of an all-clone offense, not batter-only performance with neutral runners.

## Top 25

|   risp_rank | player_name           | team   |   risp_one_run_probability |   standard_error |   ci95_low |   ci95_high |   bases_empty_rank |   bases_empty_probability |   rank_change_risp_minus_empty |   runs9_rank |   runs_per_9 |   woba |    obp |    slg |   bb_rate |   k_rate |
|------------:|:----------------------|:-------|---------------------------:|-----------------:|-----------:|------------:|-------------------:|--------------------------:|-------------------------------:|-------------:|-------------:|-------:|-------:|-------:|----------:|---------:|
|           1 | Aaron Judge           | NYY    |                     0.499  |           0.0047 |     0.4898 |      0.5082 |                  1 |                    0.4461 |                              0 |            1 |        8.984 | 0.4628 | 0.4566 | 0.6876 |    0.1826 |   0.2356 |
|           2 | Jeremy Peña           | HOU    |                     0.4869 |           0.0046 |     0.4779 |      0.496  |                 17 |                    0.3417 |                            -15 |           16 |        5.74  | 0.3629 | 0.3635 | 0.4767 |    0.0645 |   0.1713 |
|           3 | Trea Turner           | PHI    |                     0.4807 |           0.0046 |     0.4717 |      0.4898 |                 25 |                    0.3274 |                            -22 |           39 |        5.272 | 0.3516 | 0.3552 | 0.4567 |    0.0673 |   0.1674 |
|           4 | George Springer       | TOR    |                     0.4791 |           0.0046 |     0.47   |      0.4882 |                  4 |                    0.3771 |                              0 |            5 |        6.672 | 0.4079 | 0.399  | 0.5602 |    0.1177 |   0.1894 |
|           5 | Ronald Acuña Jr.      | ATL    |                     0.4753 |           0.0047 |     0.4662 |      0.4845 |                  6 |                    0.3715 |                             -1 |            4 |        7.038 | 0.4029 | 0.4175 | 0.5178 |    0.1723 |   0.2476 |
|           6 | Roman Anthony         | BOS    |                     0.4752 |           0.0047 |     0.4661 |      0.4844 |                 15 |                    0.3429 |                             -9 |           10 |        6.156 | 0.3764 | 0.396  | 0.463  |    0.132  |   0.2772 |
|           7 | Bobby Witt Jr.        | KCR    |                     0.4745 |           0.0046 |     0.4655 |      0.4836 |                 14 |                    0.3445 |                             -7 |           20 |        5.568 | 0.3603 | 0.3508 | 0.5008 |    0.0713 |   0.182  |
|           8 | Will Smith            | LAD    |                     0.4733 |           0.0046 |     0.4642 |      0.4824 |                 10 |                    0.3553 |                             -2 |            9 |        6.317 | 0.3892 | 0.4037 | 0.4972 |    0.1468 |   0.2041 |
|           9 | Jake Mangum           | TBR    |                     0.473  |           0.0046 |     0.464  |      0.4821 |                125 |                    0.2658 |                           -116 |          140 |        3.998 | 0.3075 | 0.3302 | 0.3679 |    0.0444 |   0.1495 |
|          10 | Daylen Lile           | WSN    |                     0.4706 |           0.0046 |     0.4615 |      0.4797 |                 20 |                    0.3308 |                            -10 |           31 |        5.349 | 0.3604 | 0.3467 | 0.4984 |    0.0598 |   0.1595 |
|          11 | Miguel Andujar        | 2 Tms  |                     0.4699 |           0.0046 |     0.4608 |      0.479  |                 52 |                    0.3073 |                            -41 |           46 |        5.129 | 0.3539 | 0.3519 | 0.4704 |    0.0499 |   0.1437 |
|          12 | Geraldo Perdomo       | ARI    |                     0.4695 |           0.0046 |     0.4604 |      0.4786 |                 24 |                    0.3278 |                            -12 |           27 |        5.474 | 0.3699 | 0.389  | 0.4623 |    0.1306 |   0.1153 |
|          13 | José Ramírez          | CLE    |                     0.4693 |           0.0046 |     0.4604 |      0.4783 |                 16 |                    0.3426 |                             -3 |           18 |        5.649 | 0.3596 | 0.3601 | 0.5025 |    0.0981 |   0.11   |
|          14 | Jonathan Aranda       | TBR    |                     0.4678 |           0.0047 |     0.4586 |      0.4771 |                 21 |                    0.3307 |                             -7 |           12 |        5.902 | 0.3809 | 0.3934 | 0.4892 |    0.0972 |   0.2536 |
|          15 | Nico Hoerner          | CHC    |                     0.4676 |           0.0046 |     0.4586 |      0.4767 |                 99 |                    0.2807 |                            -84 |           97 |        4.456 | 0.3241 | 0.3451 | 0.394  |    0.0601 |   0.0755 |
|          16 | Bo Bichette           | TOR    |                     0.4659 |           0.0047 |     0.4568 |      0.4751 |                 54 |                    0.3066 |                            -38 |           45 |        5.137 | 0.3609 | 0.3567 | 0.4828 |    0.0637 |   0.1449 |
|          17 | Nick Kurtz            | ATH    |                     0.4657 |           0.0046 |     0.4566 |      0.4748 |                  3 |                    0.4014 |                             14 |            2 |        7.363 | 0.4189 | 0.3832 | 0.619  |    0.1288 |   0.3088 |
|          18 | Romy Gonzalez         | BOS    |                     0.4623 |           0.0047 |     0.4532 |      0.4715 |                 39 |                    0.3164 |                            -21 |           25 |        5.49  | 0.3519 | 0.3431 | 0.4825 |    0.0528 |   0.2375 |
|          19 | Ketel Marte           | ARI    |                     0.4621 |           0.0046 |     0.4531 |      0.4712 |                 13 |                    0.3463 |                              6 |           11 |        6.145 | 0.3805 | 0.3759 | 0.5167 |    0.1151 |   0.1493 |
|          20 | Maikel Garcia         | KCR    |                     0.4614 |           0.0046 |     0.4524 |      0.4705 |                 53 |                    0.3071 |                            -33 |           66 |        4.839 | 0.3469 | 0.3514 | 0.4487 |    0.0931 |   0.1261 |
|          21 | Vladimir Guerrero Jr. | TOR    |                     0.4612 |           0.0046 |     0.4522 |      0.4703 |                 42 |                    0.3121 |                            -21 |           30 |        5.367 | 0.3656 | 0.3809 | 0.4669 |    0.1191 |   0.1382 |
|          22 | Jacob Wilson          | ATH    |                     0.461  |           0.0046 |     0.452  |      0.4701 |                 72 |                    0.2956 |                            -50 |           65 |        4.842 | 0.3479 | 0.3551 | 0.4444 |    0.0516 |   0.0746 |
|          23 | Chandler Simpson      | TBR    |                     0.4606 |           0.0046 |     0.4516 |      0.4697 |                157 |                    0.2541 |                           -134 |          222 |        3.416 | 0.2962 | 0.3257 | 0.3454 |    0.0454 |   0.0975 |
|          24 | Jake Meyers           | HOU    |                     0.46   |           0.0046 |     0.4509 |      0.4691 |                144 |                    0.2577 |                           -120 |          128 |        4.09  | 0.3226 | 0.3536 | 0.3732 |    0.0814 |   0.1759 |
|          25 | Shohei Ohtani         | LAD    |                     0.4595 |           0.0047 |     0.4504 |      0.4687 |                  2 |                    0.4053 |                             23 |            3 |        7.234 | 0.4178 | 0.3917 | 0.6219 |    0.1499 |   0.2572 |

## Largest Positive Rank Movers Versus Bases Empty

|   risp_rank |   bases_empty_rank |   rank_change_risp_minus_empty | player_name        | team   |   risp_one_run_probability |   bases_empty_probability |   woba |    obp |    slg |
|------------:|-------------------:|-------------------------------:|:-------------------|:-------|---------------------------:|--------------------------:|-------:|-------:|-------:|
|          23 |                157 |                           -134 | Chandler Simpson   | TBR    |                     0.4606 |                    0.2541 | 0.2962 | 0.3257 | 0.3454 |
|          42 |                168 |                           -126 | Steven Kwan        | CLE    |                     0.4461 |                    0.2502 | 0.3095 | 0.3304 | 0.3744 |
|          34 |                156 |                           -122 | Xavier Edwards     | MIA    |                     0.4519 |                    0.2544 | 0.3084 | 0.3425 | 0.3529 |
|          55 |                176 |                           -121 | Luis Arraez        | SDP    |                     0.4404 |                    0.2469 | 0.3134 | 0.3273 | 0.3919 |
|          24 |                144 |                           -120 | Jake Meyers        | HOU    |                     0.46   |                    0.2577 | 0.3226 | 0.3536 | 0.3732 |
|         134 |                251 |                           -117 | Chase Meidroth     | CHW    |                     0.4172 |                    0.2101 | 0.2936 | 0.3287 | 0.32   |
|         115 |                231 |                           -116 | Nick Gonzales      | PIT    |                     0.422  |                    0.2223 | 0.2889 | 0.299  | 0.3622 |
|           9 |                125 |                           -116 | Jake Mangum        | TBR    |                     0.473  |                    0.2658 | 0.3075 | 0.3302 | 0.3679 |
|         151 |                253 |                           -102 | Isiah Kiner-Falefa | 2 Tms  |                     0.4132 |                    0.2075 | 0.2787 | 0.2974 | 0.3341 |
|         145 |                247 |                           -102 | Edgar Quero        | CHW    |                     0.4146 |                    0.2121 | 0.3066 | 0.3325 | 0.3562 |
|          83 |                182 |                            -99 | J.P. Crawford      | SEA    |                     0.4309 |                    0.2459 | 0.3224 | 0.3519 | 0.3702 |
|          32 |                131 |                            -99 | Tyler Freeman      | COL    |                     0.453  |                    0.263  | 0.3195 | 0.3545 | 0.3607 |
|         121 |                218 |                            -97 | Adam Frazier       | 2 Tms  |                     0.4213 |                    0.2322 | 0.2997 | 0.3188 | 0.3652 |
|          36 |                132 |                            -96 | Ernie Clement      | TOR    |                     0.4497 |                    0.2629 | 0.3083 | 0.3133 | 0.3982 |
|          95 |                187 |                            -92 | Otto Lopez         | MIA    |                     0.4274 |                    0.2454 | 0.2948 | 0.3047 | 0.3676 |
|         141 |                230 |                            -89 | Liam Hicks         | MIA    |                     0.4162 |                    0.2252 | 0.3127 | 0.3463 | 0.3464 |
|          76 |                165 |                            -89 | Alec Bohm          | PHI    |                     0.4333 |                    0.2521 | 0.3224 | 0.3313 | 0.4095 |
|          93 |                180 |                            -87 | Paul Goldschmidt   | NYY    |                     0.4276 |                    0.2465 | 0.3161 | 0.3277 | 0.4029 |
|          85 |                171 |                            -86 | Gavin Lux          | CIN    |                     0.4307 |                    0.2497 | 0.3223 | 0.3499 | 0.3744 |
|         156 |                242 |                            -86 | Kyle Isbel         | KCR    |                     0.41   |                    0.2162 | 0.287  | 0.3005 | 0.3533 |

## Largest Negative Rank Movers Versus Bases Empty

|   risp_rank |   bases_empty_rank |   rank_change_risp_minus_empty | player_name       | team   |   risp_one_run_probability |   bases_empty_probability |   woba |    obp |    slg |
|------------:|-------------------:|-------------------------------:|:------------------|:-------|---------------------------:|--------------------------:|-------:|-------:|-------:|
|         215 |                 36 |                            179 | Eugenio Suárez    | 2 Tms  |                     0.3917 |                    0.3196 | 0.3468 | 0.2983 | 0.5255 |
|         245 |                 82 |                            163 | Matt Wallner      | MIN    |                     0.3801 |                    0.2903 | 0.3342 | 0.3112 | 0.4643 |
|         207 |                 64 |                            143 | Taylor Ward       | LAA    |                     0.3946 |                    0.3004 | 0.3388 | 0.3167 | 0.475  |
|         248 |                121 |                            127 | Kody Clemens      | 2 Tms  |                     0.3792 |                    0.2683 | 0.3067 | 0.2812 | 0.4339 |
|         189 |                 63 |                            126 | Jo Adell          | LAA    |                     0.4006 |                    0.3004 | 0.3325 | 0.293  | 0.4848 |
|         227 |                102 |                            125 | Kyle Manzardo     | CLE    |                     0.3886 |                    0.2781 | 0.3294 | 0.3126 | 0.4553 |
|         230 |                108 |                            122 | Willy Adames      | SFG    |                     0.3875 |                    0.2721 | 0.3208 | 0.3182 | 0.4213 |
|         264 |                145 |                            119 | Rowdy Tellez      | 2 Tms  |                     0.3643 |                    0.2572 | 0.3072 | 0.2756 | 0.4429 |
|         153 |                 43 |                            110 | James Wood        | WSN    |                     0.4128 |                    0.3119 | 0.3528 | 0.3498 | 0.4749 |
|         167 |                 58 |                            109 | Seiya Suzuki      | CHC    |                     0.4074 |                    0.3046 | 0.3434 | 0.3257 | 0.4781 |
|         184 |                 76 |                            108 | Kerry Carpenter   | DET    |                     0.403  |                    0.2953 | 0.3345 | 0.2913 | 0.4965 |
|         130 |                 23 |                            107 | Junior Caminero   | TBR    |                     0.4182 |                    0.3288 | 0.3565 | 0.3109 | 0.5349 |
|         111 |                  7 |                            104 | Kyle Schwarber    | PHI    |                     0.4228 |                    0.3653 | 0.3914 | 0.3646 | 0.5629 |
|         243 |                141 |                            102 | Tyler Stephenson  | CIN    |                     0.3812 |                    0.2583 | 0.3193 | 0.3158 | 0.4214 |
|         261 |                159 |                            102 | Austin Wells      | NYY    |                     0.3671 |                    0.2537 | 0.3022 | 0.2752 | 0.4364 |
|         171 |                 73 |                             98 | Mike Trout        | LAA    |                     0.4057 |                    0.2955 | 0.3432 | 0.3586 | 0.4386 |
|         158 |                 60 |                             98 | Riley Greene      | DET    |                     0.4098 |                    0.3031 | 0.3433 | 0.313  | 0.4933 |
|         244 |                148 |                             96 | Rhys Hoskins      | MIL    |                     0.381  |                    0.2567 | 0.3244 | 0.3323 | 0.4158 |
|         176 |                 81 |                             95 | Spencer Torkelson | DET    |                     0.4048 |                    0.2906 | 0.3386 | 0.3328 | 0.4565 |
|         202 |                109 |                             93 | Teoscar Hernández | LAD    |                     0.3962 |                    0.2717 | 0.3149 | 0.2844 | 0.454  |

## Precision Warning

At 10,000 trials per hitter, a simple probability near 0.50 has a Monte Carlo standard error of roughly 0.50 percentage points. Use this run to identify broad patterns; players separated by only a few standard errors should still be treated as a close group.

## Files

- `data/risp_one_run_clone_leaderboard.csv`: aggregate player leaderboard and comparisons.
- `data/risp_state_results.csv`: player-by-starting-state diagnostics.
- `data/risp_state_weights.csv`: empirical 2025 state counts and weights.