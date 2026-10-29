# All-Time Clone Lineups: RISP One-Run Probability

Each entry is a nine-copy lineup of one MLB player-season. The objective is `P(score at least one run before three outs)` when the starting state is drawn from the empirical 2025 distribution of all 18 RISP base/out states.

## Search And Precision

- Distinct 600+ common-PA player-seasons screened: 6,296
- Screen: 2,000 trials for every season
- Finalist stage: 20,000 trials for 150 seasons
- High-precision stage: 100,000 trials for 50 seasons
- Deterministic seed: `202610290`
- Runtime: 20.5 minutes

## Main Finding

`Barry Bonds (2004)` ranks first at `62.83%`.
The point-estimate lead over `Ted Williams (1941)` is `1.58` percentage points; an approximate independent-simulation 95% interval for that gap is `1.19` to `1.98` percentage points.

## Top 20

|   rank | player_name          |   season | team   |   risp_one_run_probability |   standard_error |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |   k |   sb |      cs |   sprint_speed |
|-------:|:---------------------|---------:|:-------|---------------------------:|-----------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|----:|-----:|--------:|---------------:|
|      1 | Barry Bonds          |     2004 | SFG    |                     0.6283 |           0.0014 |     0.6255 |      0.6311 |        0.5759 |       0.6124 |       0.8123 |   45 |  232 |  41 |    6 |  1      |          27.35 |
|      2 | Ted Williams         |     1941 | BOS    |                     0.6124 |           0.0014 |     0.6097 |      0.6152 |        0.5408 |       0.5528 |       0.7346 |   37 |  147 |  27 |    2 |  4      |          27.35 |
|      3 | Barry Bonds          |     2002 | SFG    |                     0.6124 |           0.0014 |     0.6096 |      0.6152 |        0.5649 |       0.5836 |       0.799  |   46 |  198 |  47 |    9 |  2      |          27.35 |
|      4 | Rogers Hornsby       |     1924 | SLN    |                     0.5984 |           0.0014 |     0.5955 |      0.6012 |        0.5131 |       0.5072 |       0.6959 |   25 |   89 |  32 |    5 | 12      |          27.35 |
|      5 | Babe Ruth            |     1923 | NYA    |                     0.5973 |           0.0014 |     0.5945 |      0.6001 |        0.5443 |       0.5445 |       0.7644 |   41 |  170 |  93 |   17 | 21      |          27.35 |
|      6 | Babe Ruth            |     1920 | NYA    |                     0.5865 |           0.0014 |     0.5836 |      0.5893 |        0.5645 |       0.5328 |       0.849  |   54 |  150 |  80 |   14 | 14      |          27.35 |
|      7 | George Sisler        |     1922 | SLA    |                     0.5864 |           0.0014 |     0.5836 |      0.5893 |        0.4603 |       0.4671 |       0.5939 |    8 |   49 |  14 |   51 | 19      |          27.35 |
|      8 | Ty Cobb              |     1911 | DET    |                     0.583  |           0.0015 |     0.5802 |      0.5859 |        0.4695 |       0.4666 |       0.621  |    8 |   44 |  36 |   83 | 27.6667 |          27.35 |
|      9 | Babe Ruth            |     1921 | NYA    |                     0.5777 |           0.0014 |     0.5749 |      0.5806 |        0.5577 |       0.5123 |       0.8463 |   59 |  145 |  81 |   17 | 13      |          27.35 |
|     10 | Babe Ruth            |     1924 | NYA    |                     0.5761 |           0.0015 |     0.5733 |      0.579  |        0.5251 |       0.5126 |       0.7391 |   46 |  142 |  81 |    9 | 13      |          27.35 |
|     11 | Harry Heilmann       |     1923 | DET    |                     0.5756 |           0.0014 |     0.5727 |      0.5784 |        0.4792 |       0.4809 |       0.6317 |   18 |   74 |  40 |    9 |  7      |          27.35 |
|     12 | Tris Speaker         |     1920 | CLE    |                     0.575  |           0.0014 |     0.5722 |      0.5779 |        0.4552 |       0.4832 |       0.5616 |    8 |   97 |  13 |   10 | 13      |          27.35 |
|     13 | Shoeless Joe Jackson |     1911 | CLE    |                     0.5748 |           0.0014 |     0.5719 |      0.5776 |        0.4586 |       0.4677 |       0.5902 |    7 |   56 |  37 |   41 | 13.6667 |          27.35 |
|     14 | George Sisler        |     1920 | SLA    |                     0.5743 |           0.0014 |     0.5715 |      0.5772 |        0.4664 |       0.4492 |       0.6323 |   19 |   46 |  19 |   42 | 17      |          27.35 |
|     15 | Arky Vaughan         |     1935 | PIT    |                     0.5741 |           0.0014 |     0.5713 |      0.577  |        0.4744 |       0.4909 |       0.6072 |   19 |   97 |  18 |    4 |  1.3333 |          27.35 |
|     16 | Babe Ruth            |     1926 | NYA    |                     0.5737 |           0.0015 |     0.5709 |      0.5765 |        0.5252 |       0.5156 |       0.7374 |   47 |  144 |  76 |   11 |  9      |          27.35 |
|     17 | Rogers Hornsby       |     1922 | SLN    |                     0.5729 |           0.0015 |     0.57   |      0.5757 |        0.503  |       0.4586 |       0.7223 |   42 |   65 |  50 |   17 | 12      |          27.35 |
|     18 | Lefty O'Doul         |     1929 | PHI    |                     0.5691 |           0.0015 |     0.5663 |      0.572  |        0.4704 |       0.4652 |       0.6223 |   32 |   76 |  19 |    2 |  0.6667 |          27.35 |
|     19 | Ty Cobb              |     1912 | DET    |                     0.569  |           0.0015 |     0.5661 |      0.5718 |        0.451  |       0.4559 |       0.5841 |    7 |   43 |  31 |   61 | 20.3333 |          27.35 |
|     20 | Mickey Mantle        |     1957 | NYA    |                     0.5683 |           0.0015 |     0.5655 |      0.5712 |        0.5014 |       0.5145 |       0.6646 |   34 |  146 |  75 |   16 |  3      |          27.35 |

## Historical Input Rules

- Actual strikeouts and stolen bases are retained.
- Actual caught stealing is retained where available; missing CS is standardized to 75% success.
- Seasons through 2019 use neutral BIP mix, Sprint Speed, and home-to-first inputs.
- Qualifying 2021-2025 seasons use cached season-specific Savant BIP mix and running inputs where matched.
- Contextual walks are disabled because the fitted model is keyed to 2025 players and cannot be applied consistently across history.
- The run environment and RISP-state weights are modern and fixed; this is not an era-adjusted measure.
- Every occupied starting base contains the cloned hitter, so the result includes that hitter's baserunning value.
- Bunting and optimized tactical decisions are excluded.

## Modern Coverage

- Modern Eligible Seasons: 317
- Modern Mlbam Matches: 317
- Modern Bip Profiles: 317
- Modern Sprint Speed: 317
- Modern Home To First: 317
- Eligible Seasons: 6,296
- Resolved Name Collision Rows: 30
- Disambiguated Name Collisions: 2

## RISP State Weights

|   outs | base_state   |   situation_pa |   weight_pct |
|-------:|:-------------|---------------:|-------------:|
|      0 | --3          |            281 |       0.6056 |
|      0 | -2-          |           2941 |       6.3385 |
|      0 | -23          |            610 |       1.3147 |
|      0 | 1-3          |            873 |       1.8815 |
|      0 | 12-          |           3358 |       7.2372 |
|      0 | 123          |            911 |       1.9634 |
|      1 | --3          |           1361 |       2.9333 |
|      1 | -2-          |           4229 |       9.1144 |
|      1 | -23          |           1482 |       3.194  |
|      1 | 1-3          |           1900 |       4.0949 |
|      1 | 12-          |           5401 |      11.6403 |
|      1 | 123          |           1986 |       4.2803 |
|      2 | --3          |           2303 |       4.9635 |
|      2 | -2-          |           5399 |      11.636  |
|      2 | -23          |           1579 |       3.4031 |
|      2 | 1-3          |           2513 |       5.4161 |
|      2 | 12-          |           6698 |      14.4357 |
|      2 | 123          |           2574 |       5.5475 |

## Files

- `all_time_risp_screen.csv`: complete all-season screening results.
- `all_time_risp_finalists.csv`: 20,000-trial finalist results.
- `all_time_risp_high_precision.csv`: 100,000-trial high-precision results.
- `all_time_risp_top20.csv`: final top 20.
- `risp_state_weights.csv`: empirical 2025 starting-state weights.
