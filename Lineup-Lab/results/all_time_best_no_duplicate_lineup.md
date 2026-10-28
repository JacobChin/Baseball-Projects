# Best All-Time No-Duplicate Lineup

## Result

- Runs per 9: **14.9275**
- Monte Carlo SE: **0.0209**
- 95% simulation interval: **14.8865 to 14.9685**
- Final comparison games per order: **100,000**
- Duplicate-player check: **passed (9 distinct player identities)**

## Batting Order

|   slot | player         |   season | team   |   woba |   obp |   slg |   hr |   bb |   k |   sb |   cs |
|-------:|:---------------|---------:|:-------|-------:|------:|------:|-----:|-----:|----:|-----:|-----:|
|      1 | Barry Bonds    |     2004 | SFG    |  0.576 | 0.612 | 0.812 |   45 |  232 |  41 |    6 |    1 |
|      2 | Ted Williams   |     1941 | BOS    |  0.541 | 0.553 | 0.735 |   37 |  147 |  27 |    2 |    4 |
|      3 | Babe Ruth      |     1920 | NYA    |  0.564 | 0.533 | 0.849 |   54 |  150 |  80 |   14 |   14 |
|      4 | Mickey Mantle  |     1957 | NYA    |  0.501 | 0.515 | 0.665 |   34 |  146 |  75 |   16 |    3 |
|      5 | Rogers Hornsby |     1924 | SLN    |  0.513 | 0.507 | 0.696 |   25 |   89 |  32 |    5 |   12 |
|      6 | Norm Cash      |     1961 | DET    |  0.49  | 0.488 | 0.662 |   41 |  124 |  85 |   11 |    5 |
|      7 | Mark McGwire   |     1998 | SLN    |  0.508 | 0.473 | 0.752 |   70 |  162 | 155 |    1 |    0 |
|      8 | Todd Helton    |     2000 | COL    |  0.496 | 0.47  | 0.698 |   42 |  103 |  61 |    5 |    3 |
|      9 | Jimmie Foxx    |     1932 | PHA    |  0.512 | 0.469 | 0.749 |   58 |  116 |  96 |    3 |    7 |

## High-Precision Finalists

|   rank | lineup_order                                                                                                                                                                                   |   runs_per_9 |   run_se |   ci95_low |   ci95_high |   games | label                                             |
|-------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------:|---------:|-----------:|------------:|--------:|:--------------------------------------------------|
|      1 | Barry Bonds (2004) / Ted Williams (1941) / Babe Ruth (1920) / Mickey Mantle (1957) / Rogers Hornsby (1924) / Norm Cash (1961) / Mark McGwire (1998) / Todd Helton (2000) / Jimmie Foxx (1932)  |      14.9275 |   0.0209 |    14.8865 |     14.9685 |  100000 | clone local swap; obp descending                  |
|      2 | Mickey Mantle (1957) / Arky Vaughan (1935) / Barry Bonds (2004) / Rogers Hornsby (1924) / Mark McGwire (1998) / Babe Ruth (1920) / Norm Cash (1961) / Ted Williams (1941) / Lou Gehrig (1927)  |      14.8666 |   0.021  |    14.8255 |     14.9076 |  100000 | clone local swap; Random order 2                  |
|      3 | Rogers Hornsby (1924) / Mickey Mantle (1957) / Norm Cash (1961) / Arky Vaughan (1935) / Barry Bonds (2004) / Babe Ruth (1920) / Lou Gehrig (1927) / Ted Williams (1941) / Mark McGwire (1998)  |      14.8497 |   0.021  |    14.8085 |     14.8908 |  100000 | clone local swap; Sabermetric heuristic rotated 5 |
|      4 | Arky Vaughan (1935) / Babe Ruth (1920) / Barry Bonds (2004) / Lou Gehrig (1927) / Mark McGwire (1998) / Mickey Mantle (1957) / Norm Cash (1961) / Rogers Hornsby (1924) / Ted Williams (1941)  |      14.8474 |   0.0209 |    14.8064 |     14.8884 |  100000 | clone local swap; Selected order                  |
|      5 | Babe Ruth (1920) / Lou Gehrig (1927) / Ted Williams (1941) / Mark McGwire (1998) / Rogers Hornsby (1924) / Mickey Mantle (1957) / Norm Cash (1961) / Arky Vaughan (1935) / Barry Bonds (2004)  |      14.8452 |   0.021  |    14.8041 |     14.8863 |  100000 | clone local swap; Sabermetric heuristic rotated 1 |
|      6 | Barry Bonds (2004) / Jimmie Foxx (1932) / Rogers Hornsby (1924) / Norm Cash (1961) / Ted Williams (1941) / Babe Ruth (1920) / Mickey Mantle (1957) / Todd Helton (2000) / Mark McGwire (1998)  |      14.8046 |   0.0209 |    14.7636 |     14.8456 |  100000 | clone local swap; Random order 8                  |
|      7 | Barry Bonds (2004) / Babe Ruth (1920) / Lou Gehrig (1927) / Ted Williams (1941) / Mark McGwire (1998) / Rogers Hornsby (1924) / Mickey Mantle (1957) / Norm Cash (1961) / Lefty O'Doul (1929)  |      14.7929 |   0.0208 |    14.7521 |     14.8337 |  100000 | clone local swap; Sabermetric heuristic           |
|      8 | Mark McGwire (1998) / Mickey Mantle (1957) / Norm Cash (1961) / Rogers Hornsby (1924) / Ted Williams (1941) / Arky Vaughan (1935) / Babe Ruth (1920) / Barry Bonds (2004) / Lou Gehrig (1927)  |      14.7681 |   0.0208 |    14.7272 |     14.8089 |  100000 | clone local swap; Selected order rotated 4        |
|      9 | Norm Cash (1961) / Jason Giambi (2001) / Barry Bonds (2004) / Babe Ruth (1920) / Lou Gehrig (1927) / Ted Williams (1941) / Mark McGwire (1998) / Rogers Hornsby (1924) / Jimmie Foxx (1932)    |      14.7403 |   0.0206 |    14.6999 |     14.7807 |  100000 | clone local swap; Sabermetric heuristic rotated 7 |
|     10 | Babe Ruth (1920) / Barry Bonds (2004) / Mark McGwire (1998) / Jimmie Foxx (1932) / Ted Williams (1941) / Bryce Harper (2015) / Rogers Hornsby (1924) / Mickey Mantle (1957) / Norm Cash (1961) |      14.7346 |   0.0207 |    14.694  |     14.7753 |  100000 | clone local swap; xbh_per_ab descending           |

## Search Design

- Candidate pool: 60 distinct players; each represented by his strongest simulated candidate season.
- Combination screen: 500 games per candidate set.
- Semifinal: top 20 sets at 5,000 games each.
- Order search: top 5 sets at 500 games per candidate order.
- Final: top 10 orders at 20,000 games, then 100,000 games per order.
- All eras use actual strikeouts and stolen bases, observed caught stealing when available, and standardized 75% steal success when caught stealing is missing.
- Historical seasons through 2019 use neutral running and batted-ball detail; 2020-present uses the available modern inputs.
- This is a simulation search over a broad candidate pool, not a mathematical proof over every possible MLB lineup.

Runtime: 0.0 minutes.
