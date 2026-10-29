# Common-Input Clone And No-Duplicate Lineups By Decade

## Purpose

Historical seasons through 2019 use common recorded batting and steal inputs with tracking-dependent skills neutralized. Eligible 2021-2025 seasons use their available season-specific Statcast and Savant inputs.

## Common Inputs And Neutralizations

- Observed inputs for every era: AB, singles, doubles, triples, home runs, total walks, HBP, and strikeouts.
- Eligibility: at least 600 common opportunities, defined as AB + BB + HBP.
- One season per player per decade, selected by the fixed-weight common batting metric.
- Strikeouts: each player-season uses its recorded total; 32 eligible 1911-1912 gaps were reconstructed from Retrosheet.
- 1900-2019 BIP type/direction: neutral league treatment; 2021-2025: season-specific Statcast type and detail profiles.
- 1900-2019 running: neutral 27.35 ft/s and 4.35 seconds; 2021-2025 uses season-specific Savant values.
- Steals: recorded SB/CS where both exist; missing CS is inferred at a standardized 75% success rate and is never treated as zero.
- Contextual walk replacement: disabled; observed total walks are retained.
- Historical GDP and player-specific BIP advancement inputs are neutral; eligible 2021-2025 candidates use the available season-specific running and BIP detail inputs.
- All players use the same current direct-movement transition engine.

## Search And Precision

- Eligible player-seasons: 6,311
- Best player-season candidates by player and decade: 2,395
- Clone candidate pool per decade: up to 500
- Clone final games per hitter: 5,000
- Distinct no-duplicate player sets screened: 2,791
- No-duplicate final games per order: 20,000
- No-duplicate refinement games per order: 100,000
- Runtime: 0.0 minutes

## 1900-1909

### Top 20 Clone Lineups

|   rank | player_name    |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:---------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Elmer Flick    |     1900 | PHI    |        8.905 |      8.772 |       9.039 |         0.43  |        0.441 |        0.545 |   11 |   56 |
|      2 | Cy Seymour     |     1905 | CIN    |        8.505 |      8.377 |       8.634 |         0.429 |        0.429 |        0.559 |    8 |   51 |
|      3 | Jesse Burkett  |     1901 | SLN    |        8.372 |      8.243 |       8.502 |         0.417 |        0.44  |        0.509 |   10 |   59 |
|      4 | Ed Delahanty   |     1901 | PHI    |        8.273 |      8.147 |       8.399 |         0.416 |        0.427 |        0.528 |    8 |   65 |
|      5 | Ty Cobb        |     1909 | DET    |        8.15  |      8.027 |       8.273 |         0.415 |        0.431 |        0.517 |    9 |   48 |
|      6 | Honus Wagner   |     1908 | PIT    |        7.989 |      7.867 |       8.111 |         0.416 |        0.415 |        0.542 |   10 |   54 |
|      7 | Jimmy Sheckard |     1901 | BRO    |        7.646 |      7.531 |       7.762 |         0.41  |        0.409 |        0.534 |   11 |   47 |
|      8 | Billy Hamilton |     1900 | BSN    |        7.532 |      7.408 |       7.655 |         0.385 |        0.449 |        0.396 |    1 |  107 |
|      9 | George Stone   |     1906 | SLA    |        7.444 |      7.328 |       7.561 |         0.402 |        0.417 |        0.501 |    6 |   52 |
|     10 | Kip Selbach    |     1900 | NY1    |        7.337 |      7.217 |       7.456 |         0.393 |        0.425 |        0.461 |    4 |   72 |
|     11 | Mike Donlin    |     1905 | NY1    |        7.292 |      7.176 |       7.408 |         0.398 |        0.413 |        0.495 |    7 |   56 |
|     12 | Topsy Hartsel  |     1901 | CHN    |        7.091 |      6.975 |       7.207 |         0.392 |        0.414 |        0.475 |    7 |   74 |
|     13 | Roy Thomas     |     1900 | PHI    |        7.077 |      6.956 |       7.197 |         0.368 |        0.451 |        0.335 |    0 |  115 |
|     14 | Eddie Collins  |     1909 | PHA    |        6.833 |      6.722 |       6.945 |         0.384 |        0.416 |        0.45  |    3 |   62 |
|     15 | Willie Keeler  |     1900 | BRO    |        6.371 |      6.262 |       6.48  |         0.376 |        0.402 |        0.449 |    4 |   30 |
|     16 | Nap Lajoie     |     1906 | CLE    |        6.344 |      6.291 |       6.398 |         0.377 |        0.392 |        0.465 |    0 |   30 |
|     17 | John Titus     |     1905 | PHI    |        6.248 |      6.193 |       6.302 |         0.37  |        0.397 |        0.436 |    2 |   69 |
|     18 | Dummy Hoy      |     1901 | CHA    |        6.178 |      6.123 |       6.232 |         0.364 |        0.407 |        0.4   |    2 |   86 |
|     19 | Jimmy Collins  |     1901 | BOS    |        6.173 |      6.122 |       6.225 |         0.379 |        0.375 |        0.495 |    6 |   34 |
|     20 | Sam Crawford   |     1902 | CIN    |        6.087 |      6.035 |       6.14  |         0.372 |        0.386 |        0.461 |    3 |   47 |

### Best No-Duplicate Lineup Found

- Runs/9: **8.021**
- 95% CI: **7.993-8.049**
- Batting order: Honus Wagner (1908) / Cy Seymour (1905) / Elmer Flick (1900) / Ed Delahanty (1901) / Ty Cobb (1909) / Jesse Burkett (1901) / Kip Selbach (1900) / Billy Hamilton (1900) / Roy Thomas (1900)

## 1910-1919

### Top 20 Clone Lineups

|   rank | player_name          |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:---------------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Ty Cobb              |     1911 | DET    |       10.997 |     10.848 |      11.146 |         0.47  |        0.467 |        0.621 |    8 |   44 |
|      2 | Shoeless Joe Jackson |     1911 | CLE    |       10.542 |     10.396 |      10.688 |         0.459 |        0.468 |        0.59  |    7 |   56 |
|      3 | Tris Speaker         |     1912 | BOS    |       10.212 |     10.068 |      10.357 |         0.448 |        0.464 |        0.567 |   10 |   82 |
|      4 | Benny Kauff          |     1914 | IND    |        9.022 |      8.889 |       9.155 |         0.429 |        0.447 |        0.534 |    8 |   72 |
|      5 | Nap Lajoie           |     1910 | CLE    |        8.694 |      8.565 |       8.823 |         0.421 |        0.444 |        0.514 |    4 |   60 |
|      6 | Sherry Magee         |     1910 | PHI    |        8.617 |      8.484 |       8.75  |         0.418 |        0.445 |        0.507 |    6 |   94 |
|      7 | Sam Crawford         |     1911 | DET    |        8.573 |      8.443 |       8.702 |         0.421 |        0.438 |        0.526 |    7 |   61 |
|      8 | Eddie Collins        |     1915 | CHA    |        8.335 |      8.204 |       8.466 |         0.403 |        0.46  |        0.436 |    4 |  119 |
|      9 | Heinie Zimmerman     |     1912 | CHN    |        8.298 |      8.174 |       8.422 |         0.428 |        0.418 |        0.571 |   14 |   38 |
|     10 | Home Run Baker       |     1912 | PHA    |        7.525 |      7.407 |       7.644 |         0.41  |        0.404 |        0.541 |   10 |   50 |
|     11 | Larry Doyle          |     1911 | NY1    |        7.225 |      7.11  |       7.341 |         0.401 |        0.397 |        0.527 |   13 |   71 |
|     12 | Jimmy Sheckard       |     1911 | CHN    |        7.086 |      6.968 |       7.204 |         0.376 |        0.434 |        0.388 |    4 |  147 |
|     13 | Gavvy Cravath        |     1915 | PHI    |        7.009 |      6.898 |       7.121 |         0.394 |        0.393 |        0.51  |   24 |   86 |
|     14 | Frank Schulte        |     1911 | CHN    |        6.954 |      6.843 |       7.065 |         0.397 |        0.384 |        0.534 |   21 |   76 |
|     15 | Jim Delahanty        |     1911 | DET    |        6.921 |      6.808 |       7.035 |         0.386 |        0.411 |        0.463 |    3 |   56 |
|     16 | Bill Sweeney         |     1912 | BSN    |        6.802 |      6.688 |       6.915 |         0.382 |        0.416 |        0.445 |    1 |   68 |
|     17 | Honus Wagner         |     1912 | PIT    |        6.716 |      6.605 |       6.826 |         0.389 |        0.395 |        0.496 |    7 |   59 |
|     18 | Dode Paskert         |     1912 | PHI    |        6.678 |      6.567 |       6.789 |         0.375 |        0.42  |        0.413 |    2 |   91 |
|     19 | Johnny Bates         |     1911 | CIN    |        6.335 |      6.28  |       6.39  |         0.366 |        0.415 |        0.394 |    1 |  103 |
|     20 | Bobby Veach          |     1917 | DET    |        6.304 |      6.25  |       6.358 |         0.376 |        0.393 |        0.457 |    8 |   61 |

### Best No-Duplicate Lineup Found

- Runs/9: **9.083**
- 95% CI: **9.053-9.113**
- Batting order: Shoeless Joe Jackson (1911) / Ty Cobb (1911) / Heinie Zimmerman (1912) / Tris Speaker (1912) / Benny Kauff (1914) / Sam Crawford (1911) / Nap Lajoie (1910) / Sherry Magee (1910) / Jimmy Sheckard (1911)

## 1920-1929

### Top 20 Clone Lineups

|   rank | player_name          |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:---------------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Babe Ruth            |     1920 | NYA    |       17.263 |     17.059 |      17.466 |         0.564 |        0.533 |        0.849 |   54 |  150 |
|      2 | Rogers Hornsby       |     1924 | SLN    |       13.95  |     13.774 |      14.127 |         0.513 |        0.507 |        0.696 |   25 |   89 |
|      3 | Lou Gehrig           |     1927 | NYA    |       12.786 |     12.626 |      12.946 |         0.519 |        0.474 |        0.765 |   47 |  109 |
|      4 | Harry Heilmann       |     1923 | DET    |       11.729 |     11.571 |      11.887 |         0.479 |        0.481 |        0.632 |   18 |   74 |
|      5 | Lefty O'Doul         |     1929 | PHI    |       10.978 |     10.828 |      11.127 |         0.47  |        0.465 |        0.622 |   32 |   76 |
|      6 | Jimmie Foxx          |     1929 | PHA    |       10.948 |     10.798 |      11.098 |         0.467 |        0.463 |        0.625 |   33 |  103 |
|      7 | Tris Speaker         |     1923 | CLE    |       10.867 |     10.72  |      11.015 |         0.465 |        0.469 |        0.61  |   17 |   93 |
|      8 | Mel Ott              |     1929 | NY1    |       10.381 |     10.239 |      10.523 |         0.464 |        0.449 |        0.635 |   42 |  113 |
|      9 | George Sisler        |     1920 | SLA    |       10.336 |     10.194 |      10.477 |         0.466 |        0.449 |        0.632 |   19 |   46 |
|     10 | Ken Williams         |     1923 | SLA    |        9.677 |      9.543 |       9.811 |         0.456 |        0.439 |        0.623 |   29 |   79 |
|     11 | Shoeless Joe Jackson |     1920 | CHA    |        9.573 |      9.438 |       9.708 |         0.447 |        0.444 |        0.589 |   12 |   56 |
|     12 | Babe Herman          |     1929 | BRO    |        9.475 |      9.341 |       9.61  |         0.452 |        0.436 |        0.612 |   21 |   55 |
|     13 | Jack Fournier        |     1925 | BRO    |        9.341 |      9.204 |       9.478 |         0.44  |        0.446 |        0.569 |   22 |   86 |
|     14 | Hack Wilson          |     1929 | CHN    |        9.31  |      9.178 |       9.441 |         0.449 |        0.425 |        0.618 |   39 |   78 |
|     15 | Paul Waner           |     1928 | PIT    |        9.246 |      9.11  |       9.382 |         0.432 |        0.446 |        0.547 |    6 |   77 |
|     16 | Chuck Klein          |     1929 | PHI    |        9.055 |      8.926 |       9.183 |         0.456 |        0.407 |        0.657 |   43 |   54 |
|     17 | Kiki Cuyler          |     1925 | PIT    |        8.913 |      8.785 |       9.041 |         0.439 |        0.423 |        0.598 |   18 |   58 |
|     18 | Joe Sewell           |     1923 | CLE    |        8.814 |      8.747 |       8.882 |         0.414 |        0.456 |        0.479 |    3 |   98 |
|     19 | Tony Lazzeri         |     1929 | NYA    |        8.636 |      8.573 |       8.699 |         0.43  |        0.429 |        0.561 |   18 |   68 |
|     20 | Ross Youngs          |     1924 | NY1    |        8.629 |      8.564 |       8.693 |         0.421 |        0.441 |        0.521 |   10 |   77 |

### Best No-Duplicate Lineup Found

- Runs/9: **11.947**
- 95% CI: **11.912-11.982**
- Batting order: Babe Ruth (1920) / Lou Gehrig (1927) / Mel Ott (1929) / Rogers Hornsby (1924) / Harry Heilmann (1923) / Lefty O'Doul (1929) / Jimmie Foxx (1929) / Tris Speaker (1923) / Jack Fournier (1925)

## 1930-1939

### Top 20 Clone Lineups

|   rank | player_name       |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:------------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Babe Ruth         |     1930 | NYA    |       13.77  |     13.595 |      13.945 |         0.514 |        0.493 |        0.732 |   49 |  136 |
|      2 | Jimmie Foxx       |     1932 | PHA    |       12.65  |     12.489 |      12.812 |         0.512 |        0.469 |        0.749 |   58 |  116 |
|      3 | Lou Gehrig        |     1930 | NYA    |       12.116 |     11.957 |      12.276 |         0.505 |        0.473 |        0.721 |   41 |  101 |
|      4 | Arky Vaughan      |     1935 | PIT    |       11.94  |     11.777 |      12.103 |         0.474 |        0.491 |        0.607 |   19 |   97 |
|      5 | Hack Wilson       |     1930 | CHN    |       11.492 |     11.344 |      11.641 |         0.497 |        0.454 |        0.723 |   56 |  105 |
|      6 | Babe Herman       |     1930 | BRO    |       10.977 |     10.829 |      11.126 |         0.485 |        0.455 |        0.678 |   35 |   66 |
|      7 | Hank Greenberg    |     1938 | DET    |       10.773 |     10.627 |      10.92  |         0.475 |        0.438 |        0.683 |   58 |  119 |
|      8 | Chuck Klein       |     1930 | PHI    |       10.42  |     10.285 |      10.556 |         0.481 |        0.436 |        0.687 |   40 |   54 |
|      9 | Bill Terry        |     1930 | NY1    |       10.278 |     10.136 |      10.42  |         0.463 |        0.452 |        0.619 |   23 |   57 |
|     10 | Mel Ott           |     1930 | NY1    |       10.182 |     10.036 |      10.327 |         0.449 |        0.458 |        0.578 |   25 |  103 |
|     11 | Johnny Mize       |     1939 | SLN    |       10.054 |      9.913 |      10.194 |         0.458 |        0.444 |        0.626 |   28 |   92 |
|     12 | Luke Appling      |     1936 | CHA    |        9.947 |      9.803 |      10.09  |         0.433 |        0.474 |        0.508 |    6 |   85 |
|     13 | Earl Averill      |     1936 | CLE    |        9.768 |      9.631 |       9.905 |         0.458 |        0.438 |        0.627 |   28 |   65 |
|     14 | Charlie Gehringer |     1937 | DET    |        9.517 |      9.379 |       9.655 |         0.43  |        0.458 |        0.52  |   14 |   90 |
|     15 | Ted Williams      |     1939 | BOS    |        9.429 |      9.292 |       9.566 |         0.448 |        0.436 |        0.609 |   31 |  107 |
|     16 | Joe DiMaggio      |     1937 | NYA    |        9.356 |      9.227 |       9.486 |         0.462 |        0.412 |        0.673 |   46 |   64 |
|     17 | Dolph Camilli     |     1936 | PHI    |        9.314 |      9.176 |       9.452 |         0.439 |        0.441 |        0.577 |   28 |  116 |
|     18 | Joe Medwick       |     1937 | SLN    |        9.068 |      9.004 |       9.132 |         0.454 |        0.414 |        0.641 |   31 |   41 |
|     19 | Bob Johnson       |     1939 | PHA    |        9.006 |      8.939 |       9.073 |         0.432 |        0.44  |        0.553 |   23 |   99 |
|     20 | Paul Waner        |     1936 | PIT    |        8.913 |      8.846 |       8.98  |         0.423 |        0.446 |        0.52  |    5 |   74 |

### Best No-Duplicate Lineup Found

- Runs/9: **11.503**
- 95% CI: **11.469-11.537**
- Batting order: Bill Terry (1930) / Arky Vaughan (1935) / Babe Herman (1930) / Chuck Klein (1930) / Lou Gehrig (1930) / Jimmie Foxx (1932) / Babe Ruth (1930) / Hack Wilson (1930) / Hank Greenberg (1938)

## 1940-1949

### Top 20 Clone Lineups

|   rank | player_name     |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:----------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Ted Williams    |     1941 | BOS    |       17.638 |     17.425 |      17.85  |         0.541 |        0.553 |        0.735 |   37 |  147 |
|      2 | Stan Musial     |     1948 | SLN    |       11.134 |     10.988 |      11.281 |         0.489 |        0.45  |        0.702 |   39 |   79 |
|      3 | Hank Greenberg  |     1940 | DET    |       10.211 |     10.07  |      10.351 |         0.469 |        0.433 |        0.67  |   41 |   93 |
|      4 | Joe DiMaggio    |     1941 | NYA    |       10.099 |      9.959 |      10.239 |         0.463 |        0.44  |        0.643 |   30 |   76 |
|      5 | Ralph Kiner     |     1949 | PIT    |        9.935 |      9.798 |      10.073 |         0.463 |        0.432 |        0.658 |   54 |  117 |
|      6 | Lou Boudreau    |     1948 | CLE    |        9.402 |      9.265 |       9.539 |         0.432 |        0.453 |        0.534 |   18 |   98 |
|      7 | Roy Cullenbine  |     1941 | SLA    |        8.697 |      8.561 |       8.834 |         0.409 |        0.452 |        0.465 |    9 |  121 |
|      8 | Johnny Mize     |     1940 | SLN    |        8.645 |      8.52  |       8.77  |         0.444 |        0.404 |        0.636 |   43 |   82 |
|      9 | Dixie Walker    |     1944 | BRO    |        8.641 |      8.509 |       8.773 |         0.421 |        0.434 |        0.529 |   13 |   72 |
|     10 | Charlie Keller  |     1941 | NYA    |        8.515 |      8.39  |       8.64  |         0.429 |        0.416 |        0.58  |   33 |  102 |
|     11 | Jimmie Foxx     |     1940 | BOS    |        8.456 |      8.33  |       8.581 |         0.428 |        0.412 |        0.581 |   36 |  101 |
|     12 | Tommy Holmes    |     1945 | BSN    |        8.416 |      8.29  |       8.543 |         0.432 |        0.42  |        0.577 |   28 |   70 |
|     13 | Jackie Robinson |     1949 | BRO    |        8.389 |      8.262 |       8.517 |         0.42  |        0.432 |        0.528 |   16 |   86 |
|     14 | Bob Johnson     |     1944 | BOS    |        8.365 |      8.239 |       8.491 |         0.419 |        0.431 |        0.528 |   17 |   95 |
|     15 | Whitey Kurowski |     1947 | SLN    |        8.347 |      8.221 |       8.473 |         0.42  |        0.42  |        0.544 |   27 |   87 |
|     16 | Rudy York       |     1940 | DET    |        8.283 |      8.157 |       8.409 |         0.428 |        0.41  |        0.583 |   33 |   89 |
|     17 | Dolph Camilli   |     1941 | BRO    |        8.113 |      7.989 |       8.238 |         0.417 |        0.407 |        0.556 |   34 |  104 |
|     18 | Augie Galan     |     1944 | BRO    |        7.903 |      7.841 |       7.965 |         0.405 |        0.426 |        0.495 |   12 |  101 |
|     19 | Enos Slaughter  |     1949 | SLN    |        7.763 |      7.702 |       7.823 |         0.406 |        0.418 |        0.511 |   13 |   79 |
|     20 | Jeff Heath      |     1941 | CLE    |        7.75  |      7.691 |       7.808 |         0.423 |        0.396 |        0.586 |   24 |   50 |

### Best No-Duplicate Lineup Found

- Runs/9: **10.301**
- 95% CI: **10.269-10.333**
- Batting order: Roy Cullenbine (1941) / Ted Williams (1941) / Stan Musial (1948) / Ralph Kiner (1949) / Hank Greenberg (1940) / Joe DiMaggio (1941) / Johnny Mize (1940) / Lou Boudreau (1948) / Charlie Keller (1941)

## 1950-1959

### Top 20 Clone Lineups

|   rank | player_name     |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:----------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Mickey Mantle   |     1957 | NYA    |       14.199 |     14.018 |      14.38  |         0.501 |        0.515 |        0.665 |   34 |  146 |
|      2 | Ralph Kiner     |     1951 | PIT    |       10.381 |     10.237 |      10.526 |         0.461 |        0.452 |        0.627 |   42 |  137 |
|      3 | Ted Williams    |     1951 | BOS    |       10.29  |     10.144 |      10.436 |         0.444 |        0.464 |        0.556 |   30 |  144 |
|      4 | Stan Musial     |     1951 | SLN    |       10.093 |      9.95  |      10.237 |         0.457 |        0.449 |        0.614 |   32 |   98 |
|      5 | Duke Snider     |     1954 | BRO    |        9.648 |      9.514 |       9.782 |         0.459 |        0.427 |        0.647 |   40 |   84 |
|      6 | Willie Mays     |     1954 | NY1    |        9.375 |      9.243 |       9.507 |         0.462 |        0.415 |        0.667 |   41 |   66 |
|      7 | Larry Doby      |     1950 | CLE    |        9.028 |      8.894 |       9.161 |         0.43  |        0.442 |        0.545 |   25 |   98 |
|      8 | Al Rosen        |     1953 | CLE    |        9.013 |      8.886 |       9.141 |         0.445 |        0.422 |        0.613 |   43 |   85 |
|      9 | Hank Aaron      |     1959 | ML1    |        8.992 |      8.865 |       9.12  |         0.448 |        0.406 |        0.636 |   39 |   51 |
|     10 | Ted Kluszewski  |     1954 | CIN    |        8.892 |      8.762 |       9.021 |         0.45  |        0.41  |        0.642 |   49 |   78 |
|     11 | Eddie Mathews   |     1953 | ML1    |        8.689 |      8.563 |       8.815 |         0.441 |        0.406 |        0.627 |   47 |   99 |
|     12 | Eddie Stanky    |     1950 | NY1    |        8.329 |      8.197 |       8.461 |         0.397 |        0.46  |        0.412 |    8 |  144 |
|     13 | Jackie Robinson |     1951 | BRO    |        8.314 |      8.187 |       8.44  |         0.419 |        0.429 |        0.527 |   19 |   79 |
|     14 | Minnie Minoso   |     1956 | CHA    |        8.259 |      8.13  |       8.387 |         0.418 |        0.43  |        0.525 |   21 |   86 |
|     15 | Al Kaline       |     1955 | DET    |        8.238 |      8.111 |       8.364 |         0.423 |        0.425 |        0.546 |   27 |   82 |
|     16 | Richie Ashburn  |     1955 | PHI    |        8.132 |      8.004 |       8.26  |         0.401 |        0.449 |        0.448 |    3 |  105 |
|     17 | Frank Robinson  |     1959 | CIN    |        7.914 |      7.855 |       7.973 |         0.423 |        0.397 |        0.583 |   36 |   69 |
|     18 | Joe DiMaggio    |     1950 | NYA    |        7.809 |      7.75  |       7.868 |         0.421 |        0.394 |        0.585 |   32 |   80 |
|     19 | Eddie Yost      |     1959 | DET    |        7.782 |      7.719 |       7.845 |         0.394 |        0.437 |        0.436 |   21 |  135 |
|     20 | Hoot Evers      |     1950 | DET    |        7.78  |      7.72  |       7.839 |         0.416 |        0.408 |        0.551 |   21 |   71 |

### Best No-Duplicate Lineup Found

- Runs/9: **9.995**
- 95% CI: **9.963-10.026**
- Batting order: Ted Williams (1951) / Stan Musial (1951) / Ralph Kiner (1951) / Ted Kluszewski (1954) / Mickey Mantle (1957) / Al Rosen (1953) / Larry Doby (1950) / Willie Mays (1954) / Duke Snider (1954)

## 1960-1969

### Top 20 Clone Lineups

|   rank | player_name      |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:-----------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Norm Cash        |     1961 | DET    |       12.518 |     12.356 |      12.68  |         0.49  |        0.488 |        0.662 |   41 |  124 |
|      2 | Mickey Mantle    |     1961 | NYA    |       11.069 |     10.919 |      11.218 |         0.481 |        0.452 |        0.687 |   54 |  126 |
|      3 | Willie McCovey   |     1969 | SFN    |       11.014 |     10.863 |      11.165 |         0.474 |        0.458 |        0.656 |   45 |  121 |
|      4 | Harmon Killebrew |     1969 | MIN    |        9.247 |      9.111 |       9.382 |         0.437 |        0.43  |        0.584 |   49 |  145 |
|      5 | Frank Robinson   |     1962 | CIN    |        9.128 |      8.997 |       9.26  |         0.45  |        0.424 |        0.624 |   39 |   76 |
|      6 | Carl Yastrzemski |     1967 | BOS    |        9.113 |      8.982 |       9.244 |         0.448 |        0.421 |        0.622 |   44 |   91 |
|      7 | Jim Wynn         |     1969 | HOU    |        8.732 |      8.599 |       8.864 |         0.418 |        0.44  |        0.507 |   33 |  148 |
|      8 | Reggie Jackson   |     1969 | OAK    |        8.685 |      8.556 |       8.814 |         0.436 |        0.41  |        0.608 |   47 |  114 |
|      9 | Willie Mays      |     1965 | SFN    |        8.645 |      8.521 |       8.769 |         0.446 |        0.399 |        0.645 |   52 |   76 |
|     10 | Rusty Staub      |     1969 | MON    |        8.392 |      8.263 |       8.521 |         0.417 |        0.427 |        0.526 |   29 |  110 |
|     11 | Rocky Colavito   |     1961 | DET    |        8.308 |      8.184 |       8.433 |         0.426 |        0.407 |        0.58  |   45 |  113 |
|     12 | Rico Petrocelli  |     1969 | BOS    |        8.273 |      8.15  |       8.396 |         0.429 |        0.407 |        0.589 |   40 |   98 |
|     13 | Pete Rose        |     1969 | CIN    |        8.267 |      8.139 |       8.395 |         0.414 |        0.432 |        0.512 |   16 |   88 |
|     14 | Hank Aaron       |     1962 | ML1    |        8.235 |      8.117 |       8.354 |         0.434 |        0.393 |        0.618 |   45 |   66 |
|     15 | Frank Howard     |     1969 | WS2    |        8.047 |      7.924 |       8.17  |         0.423 |        0.403 |        0.574 |   48 |  102 |
|     16 | Roger Maris      |     1961 | NYA    |        7.903 |      7.786 |       8.019 |         0.426 |        0.376 |        0.62  |   61 |   94 |
|     17 | Roberto Clemente |     1967 | PIT    |        7.817 |      7.696 |       7.937 |         0.416 |        0.402 |        0.554 |   23 |   41 |
|     18 | Eddie Mathews    |     1960 | ML1    |        7.798 |      7.738 |       7.858 |         0.413 |        0.401 |        0.551 |   39 |  111 |
|     19 | Ron Santo        |     1964 | CHN    |        7.763 |      7.646 |       7.881 |         0.417 |        0.401 |        0.564 |   30 |   86 |
|     20 | Norm Siebern     |     1962 | KC1    |        7.668 |      7.607 |       7.728 |         0.401 |        0.416 |        0.495 |   25 |  110 |

### Best No-Duplicate Lineup Found

- Runs/9: **9.671**
- 95% CI: **9.640-9.701**
- Batting order: Mickey Mantle (1961) / Jim Wynn (1969) / Norm Cash (1961) / Eddie Mathews (1960) / Willie McCovey (1969) / Harmon Killebrew (1969) / Frank Robinson (1962) / Reggie Jackson (1969) / Carl Yastrzemski (1967)

## 1970-1979

### Top 20 Clone Lineups

|   rank | player_name      |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:-----------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Carl Yastrzemski |     1970 | BOS    |       10.037 |     10.006 |      10.069 |         0.452 |        0.453 |        0.592 |   40 |  128 |
|      2 | Willie McCovey   |     1970 | SFN    |       10.037 |     10.006 |      10.069 |         0.453 |        0.446 |        0.612 |   39 |  137 |
|      3 | Joe Morgan       |     1975 | CIN    |        9.952 |      9.92  |       9.985 |         0.432 |        0.471 |        0.508 |   17 |  132 |
|      4 | Rod Carew        |     1977 | MIN    |        9.513 |      9.377 |       9.648 |         0.444 |        0.452 |        0.57  |   14 |   69 |
|      5 | Fred Lynn        |     1979 | BOS    |        9.419 |      9.286 |       9.553 |         0.455 |        0.426 |        0.637 |   39 |   82 |
|      6 | Dick Allen       |     1972 | CHA    |        8.929 |      8.799 |       9.058 |         0.44  |        0.422 |        0.603 |   37 |   99 |
|      7 | Jim Hickman      |     1970 | CHN    |        8.79  |      8.66  |       8.921 |         0.433 |        0.421 |        0.582 |   32 |   93 |
|      8 | Ken Singleton    |     1977 | BAL    |        8.671 |      8.538 |       8.804 |         0.419 |        0.442 |        0.507 |   24 |  107 |
|      9 | Willie Stargell  |     1973 | PIT    |        8.65  |      8.524 |       8.776 |         0.443 |        0.395 |        0.646 |   44 |   80 |
|     10 | Jeff Burroughs   |     1978 | ATL    |        8.622 |      8.491 |       8.753 |         0.422 |        0.436 |        0.529 |   23 |  117 |
|     11 | Frank Howard     |     1970 | WS2    |        8.494 |      8.364 |       8.624 |         0.421 |        0.42  |        0.546 |   44 |  132 |
|     12 | Joe Torre        |     1971 | SLN    |        8.483 |      8.419 |       8.546 |         0.426 |        0.424 |        0.555 |   24 |   63 |
|     13 | Bobby Murcer     |     1971 | NYA    |        8.458 |      8.33  |       8.586 |         0.424 |        0.429 |        0.543 |   25 |   91 |
|     14 | Billy Williams   |     1972 | CHN    |        8.413 |      8.288 |       8.539 |         0.435 |        0.403 |        0.606 |   37 |   62 |
|     15 | Dick Dietz       |     1970 | SFN    |        8.394 |      8.33  |       8.458 |         0.415 |        0.43  |        0.515 |   22 |  109 |
|     16 | John Mayberry    |     1975 | KCA    |        8.31  |      8.246 |       8.373 |         0.42  |        0.419 |        0.547 |   34 |  119 |
|     17 | Boog Powell      |     1970 | BAL    |        8.29  |      8.227 |       8.352 |         0.421 |        0.417 |        0.549 |   35 |  104 |
|     18 | Tony Perez       |     1970 | CIN    |        8.246 |      8.184 |       8.308 |         0.429 |        0.405 |        0.589 |   40 |   83 |
|     19 | Harmon Killebrew |     1970 | MIN    |        8.225 |      8.162 |       8.287 |         0.419 |        0.416 |        0.546 |   41 |  128 |
|     20 | Greg Luzinski    |     1977 | PHI    |        8.135 |      8.074 |       8.197 |         0.427 |        0.399 |        0.594 |   39 |   80 |

### Best No-Duplicate Lineup Found

- Runs/9: **9.271**
- 95% CI: **9.241-9.301**
- Batting order: Willie McCovey (1970) / Carl Yastrzemski (1970) / Rod Carew (1977) / Jim Hickman (1970) / Tony Perez (1970) / Ken Singleton (1977) / Joe Morgan (1975) / Fred Lynn (1979) / Dick Allen (1972)

## 1980-1989

### Top 20 Clone Lineups

|   rank | player_name       |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:------------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Wade Boggs        |     1987 | BOS    |       10.719 |     10.568 |      10.869 |         0.457 |        0.467 |        0.588 |   24 |  105 |
|      2 | George Brett      |     1985 | KCA    |        9.383 |      9.245 |       9.521 |         0.444 |        0.442 |        0.585 |   30 |  103 |
|      3 | Tony Gwynn        |     1987 | SDN    |        8.996 |      8.861 |       9.13  |         0.422 |        0.45  |        0.511 |    7 |   82 |
|      4 | Dale Murphy       |     1987 | ATL    |        8.698 |      8.568 |       8.829 |         0.432 |        0.42  |        0.58  |   44 |  115 |
|      5 | Dwight Evans      |     1987 | BOS    |        8.613 |      8.484 |       8.742 |         0.429 |        0.422 |        0.569 |   34 |  106 |
|      6 | Tim Raines        |     1987 | MON    |        8.482 |      8.352 |       8.611 |         0.419 |        0.431 |        0.526 |   18 |   90 |
|      7 | Kevin Mitchell    |     1989 | SFN    |        8.333 |      8.212 |       8.453 |         0.438 |        0.392 |        0.635 |   47 |   87 |
|      8 | Pedro Guerrero    |     1987 | LAN    |        8.174 |      8.048 |       8.301 |         0.419 |        0.421 |        0.539 |   27 |   74 |
|      9 | Mike Schmidt      |     1980 | PHI    |        8.139 |      8.02  |       8.258 |         0.432 |        0.388 |        0.624 |   48 |   89 |
|     10 | Darryl Strawberry |     1987 | NYN    |        8.084 |      7.96  |       8.207 |         0.424 |        0.401 |        0.583 |   39 |   97 |
|     11 | Rickey Henderson  |     1985 | NYA    |        8.056 |      7.934 |       8.178 |         0.411 |        0.422 |        0.516 |   24 |   99 |
|     12 | Alvin Davis       |     1989 | SEA    |        7.996 |      7.872 |       8.12  |         0.408 |        0.428 |        0.496 |   21 |  101 |
|     13 | Mike Greenwell    |     1988 | BOS    |        7.983 |      7.861 |       8.105 |         0.415 |        0.42  |        0.531 |   22 |   87 |
|     14 | Will Clark        |     1989 | SFN    |        7.911 |      7.79  |       8.033 |         0.417 |        0.412 |        0.546 |   23 |   74 |
|     15 | Don Mattingly     |     1986 | NYA    |        7.888 |      7.768 |       8.009 |         0.422 |        0.399 |        0.573 |   31 |   53 |
|     16 | Alan Trammell     |     1987 | DET    |        7.838 |      7.718 |       7.958 |         0.417 |        0.406 |        0.551 |   28 |   60 |
|     17 | Mark McGwire      |     1987 | OAK    |        7.68  |      7.623 |       7.737 |         0.425 |        0.374 |        0.618 |   49 |   71 |
|     18 | Jose Canseco      |     1988 | OAK    |        7.614 |      7.555 |       7.672 |         0.417 |        0.394 |        0.569 |   42 |   78 |
|     19 | Fred McGriff      |     1989 | TOR    |        7.572 |      7.513 |       7.632 |         0.405 |        0.402 |        0.525 |   36 |  119 |
|     20 | Eddie Murray      |     1982 | BAL    |        7.505 |      7.447 |       7.564 |         0.41  |        0.395 |        0.549 |   32 |   70 |

### Best No-Duplicate Lineup Found

- Runs/9: **8.762**
- 95% CI: **8.733-8.791**
- Batting order: Tony Gwynn (1987) / Mike Schmidt (1980) / Wade Boggs (1987) / Kevin Mitchell (1989) / George Brett (1985) / Dale Murphy (1987) / Tim Raines (1987) / Pedro Guerrero (1987) / Dwight Evans (1987)

## 1990-1999

### Top 20 Clone Lineups

|   rank | player_name     |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:----------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Mark McGwire    |     1998 | SLN    |       12.926 |     12.761 |      13.091 |         0.508 |        0.473 |        0.752 |   70 |  162 |
|      2 | Edgar Martinez  |     1995 | SEA    |       11.807 |     11.647 |      11.967 |         0.477 |        0.482 |        0.628 |   29 |  116 |
|      3 | Larry Walker    |     1997 | COL    |       11.593 |     11.442 |      11.745 |         0.498 |        0.455 |        0.72  |   49 |   78 |
|      4 | Barry Bonds     |     1993 | SFN    |       11.397 |     11.244 |      11.55  |         0.483 |        0.463 |        0.677 |   46 |  126 |
|      5 | John Olerud     |     1993 | TOR    |       11.366 |     11.214 |      11.518 |         0.465 |        0.478 |        0.599 |   24 |  114 |
|      6 | Gary Sheffield  |     1996 | FLO    |       11.162 |     11.009 |      11.315 |         0.468 |        0.469 |        0.624 |   42 |  142 |
|      7 | Frank Thomas    |     1996 | CHA    |       10.963 |     10.813 |      11.112 |         0.469 |        0.465 |        0.626 |   40 |  109 |
|      8 | Manny Ramirez   |     1999 | CLE    |       10.784 |     10.638 |      10.929 |         0.474 |        0.448 |        0.663 |   44 |   96 |
|      9 | Jim Thome       |     1996 | CLE    |       10.324 |     10.175 |      10.472 |         0.456 |        0.451 |        0.612 |   38 |  123 |
|     10 | Jeff Bagwell    |     1999 | HOU    |       10.282 |     10.134 |      10.431 |         0.453 |        0.458 |        0.591 |   42 |  149 |
|     11 | Chipper Jones   |     1999 | ATL    |       10.242 |     10.1   |      10.385 |         0.461 |        0.445 |        0.633 |   45 |  126 |
|     12 | Mike Piazza     |     1997 | LAN    |        9.85  |      9.712 |       9.987 |         0.462 |        0.435 |        0.638 |   40 |   69 |
|     13 | Rafael Palmeiro |     1999 | TEX    |        9.346 |      9.213 |       9.48  |         0.453 |        0.426 |        0.63  |   47 |   97 |
|     14 | Bobby Abreu     |     1999 | PHI    |        9.328 |      9.259 |       9.398 |         0.434 |        0.448 |        0.549 |   20 |  109 |
|     15 | Tim Salmon      |     1995 | CAL    |        9.287 |      9.219 |       9.354 |         0.443 |        0.432 |        0.594 |   34 |   91 |
|     16 | Albert Belle    |     1995 | CLE    |        9.24  |      9.176 |       9.305 |         0.463 |        0.403 |        0.69  |   50 |   73 |
|     17 | Brian Giles     |     1999 | PIT    |        9.181 |      9.114 |       9.247 |         0.445 |        0.423 |        0.614 |   39 |   95 |
|     18 | Alex Rodriguez  |     1996 | SEA    |        9.129 |      9.064 |       9.195 |         0.451 |        0.419 |        0.631 |   36 |   59 |
|     19 | Chuck Knoblauch |     1996 | MIN    |        9.085 |      9.017 |       9.154 |         0.426 |        0.452 |        0.517 |   13 |   98 |
|     20 | Derek Jeter     |     1999 | NYA    |        9.022 |      8.955 |       9.089 |         0.433 |        0.441 |        0.552 |   24 |   91 |

### Best No-Duplicate Lineup Found

- Runs/9: **11.375**
- 95% CI: **11.341-11.410**
- Batting order: John Olerud (1993) / Larry Walker (1997) / Manny Ramirez (1999) / Mark McGwire (1998) / Barry Bonds (1993) / Edgar Martinez (1995) / Frank Thomas (1996) / Gary Sheffield (1996) / Jeff Bagwell (1999)

## 2000-2009

### Top 20 Clone Lineups

|   rank | player_name     |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:----------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Barry Bonds     |     2004 | SFG    |       24.331 |     24.071 |      24.591 |         0.576 |        0.612 |        0.812 |   45 |  232 |
|      2 | Jason Giambi    |     2001 | OAK    |       12.185 |     12.023 |      12.347 |         0.487 |        0.483 |        0.66  |   38 |  129 |
|      3 | Todd Helton     |     2000 | COL    |       12.112 |     11.956 |      12.268 |         0.496 |        0.47  |        0.698 |   42 |  103 |
|      4 | Carlos Delgado  |     2000 | TOR    |       11.833 |     11.674 |      11.992 |         0.484 |        0.472 |        0.664 |   41 |  123 |
|      5 | Albert Pujols   |     2008 | STL    |       11.513 |     11.36  |      11.666 |         0.479 |        0.468 |        0.653 |   37 |  104 |
|      6 | Sammy Sosa      |     2001 | CHC    |       11.378 |     11.228 |      11.529 |         0.496 |        0.445 |        0.737 |   64 |  116 |
|      7 | Jim Thome       |     2002 | CLE    |       11.032 |     10.883 |      11.181 |         0.477 |        0.45  |        0.677 |   52 |  122 |
|      8 | Luis Gonzalez   |     2001 | ARI    |       10.364 |     10.221 |      10.506 |         0.474 |        0.432 |        0.688 |   57 |  100 |
|      9 | Brian Giles     |     2002 | PIT    |       10.354 |     10.21  |      10.499 |         0.459 |        0.454 |        0.622 |   38 |  135 |
|     10 | David Ortiz     |     2007 | BOS    |       10.158 |     10.016 |      10.3   |         0.458 |        0.447 |        0.621 |   35 |  111 |
|     11 | Gary Sheffield  |     2000 | LAD    |       10.118 |      9.977 |      10.258 |         0.464 |        0.442 |        0.643 |   43 |  101 |
|     12 | Frank Thomas    |     2000 | CHW    |       10.011 |      9.87  |      10.151 |         0.457 |        0.441 |        0.625 |   43 |  112 |
|     13 | Ryan Howard     |     2006 | PHI    |        9.912 |      9.775 |      10.049 |         0.463 |        0.428 |        0.659 |   58 |  108 |
|     14 | Joe Mauer       |     2009 | MIN    |        9.734 |      9.594 |       9.873 |         0.449 |        0.448 |        0.587 |   28 |   76 |
|     15 | Alex Rodriguez  |     2007 | NYY    |        9.696 |      9.628 |       9.764 |         0.459 |        0.428 |        0.645 |   54 |   95 |
|     16 | Derrek Lee      |     2005 | CHC    |        9.653 |      9.586 |       9.72  |         0.462 |        0.423 |        0.662 |   46 |   85 |
|     17 | Jim Edmonds     |     2004 | STL    |        9.552 |      9.484 |       9.62  |         0.454 |        0.424 |        0.643 |   42 |  101 |
|     18 | Lance Berkman   |     2001 | HOU    |        9.511 |      9.444 |       9.579 |         0.452 |        0.434 |        0.62  |   34 |   92 |
|     19 | Magglio Ordóñez |     2007 | DET    |        9.44  |      9.373 |       9.508 |         0.447 |        0.437 |        0.595 |   28 |   76 |
|     20 | Manny Ramírez   |     2008 | 2TM    |        9.387 |      9.319 |       9.455 |         0.446 |        0.432 |        0.601 |   37 |   87 |

### Best No-Duplicate Lineup Found

- Runs/9: **12.306**
- 95% CI: **12.270-12.342**
- Batting order: Barry Bonds (2004) / David Ortiz (2007) / Sammy Sosa (2001) / Albert Pujols (2008) / Jim Thome (2002) / Jason Giambi (2001) / Todd Helton (2000) / Carlos Delgado (2000) / Brian Giles (2002)

## 2010-2019

### Top 20 Clone Lineups

|   rank | player_name      |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:-----------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Bryce Harper     |     2015 | WSN    |       11.218 |     11.184 |      11.252 |         0.474 |        0.463 |        0.649 |   42 |  124 |
|      2 | Mike Trout       |     2018 | LAA    |       11.012 |     10.978 |      11.046 |         0.467 |        0.463 |        0.628 |   39 |  122 |
|      3 | Mookie Betts     |     2018 | BOS    |       10.244 |     10.104 |      10.383 |         0.463 |        0.442 |        0.64  |   32 |   81 |
|      4 | Joey Votto       |     2017 | CIN    |       10.243 |     10.096 |      10.39  |         0.449 |        0.458 |        0.578 |   36 |  134 |
|      5 | José Bautista    |     2011 | TOR    |       10.183 |     10.038 |      10.328 |         0.455 |        0.45  |        0.608 |   43 |  132 |
|      6 | Miguel Cabrera   |     2013 | DET    |       10.177 |     10.035 |      10.319 |         0.464 |        0.443 |        0.636 |   44 |   90 |
|      7 | Aaron Judge      |     2017 | NYY    |        9.448 |      9.315 |       9.581 |         0.449 |        0.424 |        0.627 |   52 |  127 |
|      8 | Paul Goldschmidt |     2015 | ARI    |        9.31  |      9.178 |       9.443 |         0.438 |        0.44  |        0.57  |   33 |  118 |
|      9 | Alex Bregman     |     2019 | HOU    |        8.969 |      8.839 |       9.099 |         0.439 |        0.428 |        0.592 |   41 |  119 |
|     10 | Albert Pujols    |     2010 | STL    |        8.9   |      8.771 |       9.028 |         0.437 |        0.418 |        0.596 |   42 |  103 |
|     11 | Anthony Rendon   |     2019 | WSN    |        8.74  |      8.612 |       8.867 |         0.438 |        0.418 |        0.598 |   34 |   80 |
|     12 | J.D. Martinez    |     2018 | BOS    |        8.736 |      8.608 |       8.864 |         0.444 |        0.407 |        0.629 |   43 |   69 |
|     13 | Cody Bellinger   |     2019 | LAD    |        8.726 |      8.598 |       8.854 |         0.444 |        0.409 |        0.629 |   47 |   95 |
|     14 | David Ortiz      |     2016 | BOS    |        8.604 |      8.477 |       8.732 |         0.439 |        0.405 |        0.62  |   38 |   80 |
|     15 | Prince Fielder   |     2011 | MIL    |        8.409 |      8.283 |       8.534 |         0.427 |        0.418 |        0.566 |   38 |  107 |
|     16 | Christian Yelich |     2018 | MIL    |        8.237 |      8.175 |       8.298 |         0.431 |        0.404 |        0.598 |   36 |   68 |
|     17 | Charlie Blackmon |     2017 | COL    |        8.219 |      8.158 |       8.28  |         0.431 |        0.401 |        0.601 |   37 |   65 |
|     18 | Victor Martinez  |     2014 | DET    |        8.205 |      8.144 |       8.267 |         0.425 |        0.413 |        0.565 |   32 |   70 |
|     19 | Matt Kemp        |     2011 | LAD    |        8.204 |      8.143 |       8.266 |         0.428 |        0.403 |        0.586 |   39 |   74 |
|     20 | Buster Posey     |     2012 | SFG    |        8.187 |      8.125 |       8.249 |         0.419 |        0.414 |        0.549 |   24 |   69 |

### Best No-Duplicate Lineup Found

- Runs/9: **9.922**
- 95% CI: **9.890-9.953**
- Batting order: Joey Votto (2017) / José Bautista (2011) / Miguel Cabrera (2013) / Mike Trout (2018) / Mookie Betts (2018) / Paul Goldschmidt (2015) / Aaron Judge (2017) / Adrián González (2011) / Bryce Harper (2015)

## 2020-2029

### Top 20 Clone Lineups

|   rank | player_name           |   season | team   |   runs_per_9 |   ci95_low |   ci95_high |   common_woba |   common_obp |   common_slg |   hr |   bb |
|-------:|:----------------------|---------:|:-------|-------------:|-----------:|------------:|--------------:|-------------:|-------------:|-----:|-----:|
|      1 | Aaron Judge           |     2024 | NYY    |       11.505 |     11.351 |      11.659 |         0.489 |        0.459 |        0.701 |   58 |  133 |
|      2 | Juan Soto             |     2021 | WSN    |        9.883 |      9.741 |      10.025 |         0.44  |        0.468 |        0.534 |   29 |  145 |
|      3 | Ronald Acuña Jr.      |     2023 | ATL    |        8.642 |      8.516 |       8.768 |         0.438 |        0.418 |        0.596 |   41 |   80 |
|      4 | Shohei Ohtani         |     2024 | LAD    |        8.635 |      8.51  |       8.759 |         0.443 |        0.393 |        0.646 |   54 |   81 |
|      5 | Mookie Betts          |     2023 | LAD    |        8.215 |      8.088 |       8.342 |         0.428 |        0.411 |        0.579 |   39 |   96 |
|      6 | Vladimir Guerrero Jr. |     2021 | TOR    |        8.119 |      7.998 |       8.239 |         0.432 |        0.402 |        0.601 |   48 |   86 |
|      7 | Bobby Witt Jr.        |     2024 | KCR    |        8.033 |      7.912 |       8.154 |         0.423 |        0.394 |        0.588 |   32 |   57 |
|      8 | Freddie Freeman       |     2023 | LAD    |        8.009 |      7.886 |       8.132 |         0.425 |        0.412 |        0.567 |   29 |   72 |
|      9 | Paul Goldschmidt      |     2022 | STL    |        7.97  |      7.848 |       8.091 |         0.426 |        0.406 |        0.578 |   35 |   79 |
|     10 | Matt Olson            |     2023 | ATL    |        7.894 |      7.776 |       8.013 |         0.427 |        0.391 |        0.604 |   54 |  104 |
|     11 | Yordan Alvarez        |     2024 | HOU    |        7.466 |      7.348 |       7.584 |         0.417 |        0.395 |        0.567 |   35 |   69 |
|     12 | Jose Altuve           |     2022 | HOU    |        7.165 |      7.051 |       7.279 |         0.401 |        0.388 |        0.533 |   28 |   66 |
|     13 | Bryan Reynolds        |     2021 | PIT    |        7.151 |      7.037 |       7.266 |         0.399 |        0.393 |        0.522 |   24 |   75 |
|     14 | Trea Turner           |     2021 | 2TM    |        7.095 |      6.982 |       7.207 |         0.397 |        0.377 |        0.536 |   28 |   41 |
|     15 | Cal Raleigh           |     2025 | SEA    |        7.08  |      6.97  |       7.189 |         0.407 |        0.36  |        0.589 |   60 |   97 |
|     16 | Brent Rooker          |     2024 | OAK    |        6.908 |      6.799 |       7.016 |         0.402 |        0.367 |        0.562 |   39 |   59 |
|     17 | Marcell Ozuna         |     2024 | ATL    |        6.87  |      6.76  |       6.98  |         0.403 |        0.381 |        0.546 |   39 |   74 |
|     18 | Kyle Schwarber        |     2025 | PHI    |        6.869 |      6.76  |       6.978 |         0.4   |        0.365 |        0.563 |   56 |  108 |
|     19 | Bryce Harper          |     2024 | PHI    |        6.616 |      6.562 |       6.67  |         0.392 |        0.374 |        0.525 |   30 |   76 |
|     20 | Gunnar Henderson      |     2024 | BAL    |        6.566 |      6.513 |       6.619 |         0.389 |        0.366 |        0.529 |   37 |   78 |

### Best No-Duplicate Lineup Found

- Runs/9: **8.662**
- 95% CI: **8.634-8.690**
- Batting order: Aaron Judge (2024) / Shohei Ohtani (2024) / Freddie Freeman (2023) / Bobby Witt Jr. (2024) / Mookie Betts (2023) / Paul Goldschmidt (2022) / Yordan Alvarez (2024) / Ronald Acuña Jr. (2023) / Juan Soto (2021)

## Interpretation

These are not era-adjusted results. They translate every batting line into the same modern league transition environment. Tracking-dependent player skills are neutral through 2019 and season-specific for eligible 2021-2025 candidates. The no-duplicate search is broad and staged, but it is not an exhaustive search of every nine-player combination and all 9! batting orders.

## Files

- `data/decade_top20_clone_runs9.csv`
- `data/decade_best_no_duplicate_lineups.csv`
- `data/no_duplicate_finalists.csv`
- `data/common_input_player_decade_candidates.csv`
- `data/common_input_eligible_seasons.csv`
- `model_qa.json`
