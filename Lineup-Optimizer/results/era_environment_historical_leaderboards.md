# Historical Lineups With Era Offensive Environments

## Purpose

This report tests how the all-time historical lineup rankings change after adding a decade-level offensive-environment adjustment to the existing common-input simulations.

## Method

- The original player profiles are unchanged, so each hitter's observed batting rates continue to reflect his season.
- Actual MLB runs per team-game are calculated for every decade from 1900 through 2025.
- A league-average clone lineup for every decade is simulated for **20,000 games** with the same production transition engine.
- Decade conversion ratio = actual decade MLB R/G / simulated decade league-average R/G.
- The reference is 2021-2025: **4.454 actual R/G** and a **1.063 conversion ratio**.
- Era-environment runs/9 = fixed-environment player runs/9 x (decade conversion ratio / reference conversion ratio).
- This residual conversion adjustment avoids multiplying by raw league scoring and double-counting the environment already present in each player's batting line.
- The leading adjusted all-time candidates were rerun for **20,000 games each** with deterministic seeds.
- Because every player within a decade receives the same factor, rankings within each decade do not change. The all-time ordering across decades can change.
- This remains a sensitivity analysis, not a complete reconstruction of historical parks, opponent quality, fielding, rules, equipment, or runner advancement.

## Era Calibration

| Decade | Actual Runs Per Team Game | Simulated League Runs Per 9 | Run Conversion Ratio | Environment Factor |
| --- | --- | --- | --- | --- |
| 1900-1909 | 3.994 | 3.178 | 1.257 | 1.182 |
| 1910-1919 | 3.921 | 3.494 | 1.122 | 1.055 |
| 1920-1929 | 4.809 | 4.524 | 1.063 | 1.000 |
| 1930-1939 | 4.934 | 4.503 | 1.096 | 1.030 |
| 1940-1949 | 4.307 | 4.042 | 1.066 | 1.002 |
| 1950-1959 | 4.447 | 4.275 | 1.040 | 0.978 |
| 1960-1969 | 4.041 | 3.823 | 1.057 | 0.994 |
| 1970-1979 | 4.156 | 3.971 | 1.047 | 0.984 |
| 1980-1989 | 4.298 | 4.094 | 1.050 | 0.987 |
| 1990-1999 | 4.677 | 4.531 | 1.032 | 0.971 |
| 2000-2009 | 4.759 | 4.718 | 1.009 | 0.948 |
| 2010-2019 | 4.388 | 4.255 | 1.031 | 0.970 |
| 2020-2025 | 4.467 | 4.260 | 1.049 | 0.986 |

## Adjusted All-Time Top 20 Clone Lineups

| Era Rank | Player Name | Season | Team | Decade | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 | Fixed Rank | Rank Change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Barry Bonds | 2004 | SFG | 2000-2009 | 0.948 | 24.368 | 23.112 | 1 | 0 |
| 2 | Ted Williams | 1941 | BOS | 1940-1949 | 1.002 | 17.734 | 17.770 | 2 | 0 |
| 3 | Babe Ruth | 1920 | NYA | 1920-1929 | 1.000 | 17.270 | 17.262 | 3 | 0 |
| 4 | Babe Ruth | 1930 | NYA | 1930-1939 | 1.030 | 13.482 | 13.890 | 6 | 2 |
| 5 | Rogers Hornsby | 1924 | SLN | 1920-1929 | 1.000 | 13.888 | 13.881 | 5 | 0 |
| 6 | Mickey Mantle | 1957 | NYA | 1950-1959 | 0.978 | 14.185 | 13.876 | 4 | -2 |
| 7 | Jimmie Foxx | 1932 | PHA | 1930-1939 | 1.030 | 12.607 | 12.989 | 9 | 2 |
| 8 | Lou Gehrig | 1927 | NYA | 1920-1929 | 1.000 | 12.904 | 12.898 | 8 | 0 |
| 9 | Lou Gehrig | 1930 | NYA | 1930-1939 | 1.030 | 12.290 | 12.662 | 12 | 3 |
| 10 | Mark McGwire | 1998 | SLN | 1990-1999 | 0.971 | 12.940 | 12.560 | 7 | -3 |
| 11 | Norm Cash | 1961 | DET | 1960-1969 | 0.994 | 12.527 | 12.451 | 10 | -1 |
| 12 | Arky Vaughan | 1935 | PIT | 1930-1939 | 1.030 | 12.045 | 12.410 | 14 | 2 |
| 13 | Hack Wilson | 1930 | CHN | 1930-1939 | 1.030 | 11.625 | 11.977 | 19 | 6 |
| 14 | Harry Heilmann | 1923 | DET | 1920-1929 | 1.000 | 11.768 | 11.762 | 17 | 3 |
| 15 | Jason Giambi | 2001 | OAK | 2000-2009 | 0.948 | 12.315 | 11.681 | 11 | -4 |
| 16 | Todd Helton | 2000 | COL | 2000-2009 | 0.948 | 12.118 | 11.494 | 13 | -3 |
| 17 | Edgar Martinez | 1995 | SEA | 1990-1999 | 0.971 | 11.837 | 11.489 | 15 | -2 |
| 18 | Ty Cobb | 1911 | DET | 1910-1919 | 1.055 | 10.836 | 11.434 | 33 | 15 |
| 19 | Babe Herman | 1930 | BRO | 1930-1939 | 1.030 | 11.085 | 11.421 | 29 | 10 |
| 20 | Aaron Judge | 2024 | NYY | 2020-2025 | 0.986 | 11.549 | 11.388 | 20 | 0 |

## Decade Winners

| Decade | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1900-1909 | Elmer Flick | 1900 | PHI | 1.182 | 8.905 | 10.523 |
| 1910-1919 | Ty Cobb | 1911 | DET | 1.055 | 10.997 | 11.603 |
| 1920-1929 | Babe Ruth | 1920 | NYA | 1.000 | 17.263 | 17.254 |
| 1930-1939 | Babe Ruth | 1930 | NYA | 1.030 | 13.770 | 14.187 |
| 1940-1949 | Ted Williams | 1941 | BOS | 1.002 | 17.638 | 17.673 |
| 1950-1959 | Mickey Mantle | 1957 | NYA | 0.978 | 14.199 | 13.889 |
| 1960-1969 | Norm Cash | 1961 | DET | 0.994 | 12.518 | 12.441 |
| 1970-1979 | Carl Yastrzemski | 1970 | BOS | 0.984 | 10.037 | 9.878 |
| 1980-1989 | Wade Boggs | 1987 | BOS | 0.987 | 10.719 | 10.582 |
| 1990-1999 | Mark McGwire | 1998 | SLN | 0.971 | 12.926 | 12.546 |
| 2000-2009 | Barry Bonds | 2004 | SFG | 0.948 | 24.331 | 23.078 |
| 2010-2019 | Bryce Harper | 2015 | WSN | 0.970 | 11.218 | 10.879 |
| 2020-2025 | Aaron Judge | 2024 | NYY | 0.986 | 11.505 | 11.345 |

## Largest Positive All-Time Rank Movers

| Player Name | Season | Decade | Fixed Rank | Adjusted Rank | Rank Change | Environment Factor | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mike Donlin | 1905 | 1900-1909 | 465 | 182 | 283 | 1.182 | 8.446 |
| Kip Selbach | 1900 | 1900-1909 | 400 | 148 | 252 | 1.182 | 8.723 |
| George Stone | 1906 | 1900-1909 | 362 | 130 | 232 | 1.182 | 8.911 |
| Billy Hamilton | 1900 | 1900-1909 | 335 | 115 | 220 | 1.182 | 9.027 |
| Jimmy Sheckard | 1901 | 1900-1909 | 313 | 104 | 209 | 1.182 | 9.172 |
| Ty Cobb | 1909 | 1900-1909 | 293 | 94 | 199 | 1.182 | 9.289 |
| Honus Wagner | 1908 | 1900-1909 | 288 | 93 | 195 | 1.182 | 9.317 |
| Ed Delahanty | 1901 | 1900-1909 | 235 | 78 | 157 | 1.182 | 9.624 |
| Jesse Burkett | 1901 | 1900-1909 | 175 | 53 | 122 | 1.182 | 10.133 |
| Cy Seymour | 1905 | 1900-1909 | 168 | 50 | 118 | 1.182 | 10.177 |

## Largest Negative All-Time Rank Movers

| Player Name | Season | Decade | Fixed Rank | Adjusted Rank | Rank Change | Environment Factor | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bobby Abreu | 2004 | 2000-2009 | 140 | 205 | -65 | 0.948 | 8.310 |
| Matt Holliday | 2007 | 2000-2009 | 139 | 203 | -64 | 0.948 | 8.324 |
| Edgar Martínez | 2000 | 2000-2009 | 136 | 195 | -59 | 0.948 | 8.370 |
| Troy Glaus | 2000 | 2000-2009 | 196 | 252 | -56 | 0.948 | 7.981 |
| Melvin Mora | 2004 | 2000-2009 | 197 | 253 | -56 | 0.948 | 7.973 |
| Edgardo Alfonzo | 2000 | 2000-2009 | 186 | 241 | -55 | 0.948 | 8.030 |
| Roberto Alomar | 2001 | 2000-2009 | 178 | 233 | -55 | 0.948 | 8.103 |
| Prince Fielder | 2009 | 2000-2009 | 135 | 186 | -51 | 0.948 | 8.411 |
| Jeff Kent | 2000 | 2000-2009 | 127 | 173 | -46 | 0.948 | 8.510 |
| Magglio Ordóñez | 2007 | 2000-2009 | 126 | 171 | -45 | 0.948 | 8.523 |

## No-Duplicate Lineups By Decade

Each established decade lineup receives that decade's residual conversion factor. This changes its estimated runs/9 but not the selected players or batting order because every candidate lineup in the decade receives the same multiplier.

| Decade | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 | Lineup Order |
| --- | --- | --- | --- | --- |
| 1900-1909 | 1.182 | 8.021 | 9.478 | Honus Wagner (1908) / Cy Seymour (1905) / Elmer Flick (1900) / Ed Delahanty (1901) / Ty Cobb (1909) / Jesse Burkett (1901) / Kip Selbach (1900) / Billy Hamilton (1900) / Roy Thomas (1900) |
| 1910-1919 | 1.055 | 9.083 | 9.584 | Shoeless Joe Jackson (1911) / Ty Cobb (1911) / Heinie Zimmerman (1912) / Tris Speaker (1912) / Benny Kauff (1914) / Sam Crawford (1911) / Nap Lajoie (1910) / Sherry Magee (1910) / Jimmy Sheckard (1911) |
| 1920-1929 | 1.000 | 11.947 | 11.941 | Babe Ruth (1920) / Lou Gehrig (1927) / Mel Ott (1929) / Rogers Hornsby (1924) / Harry Heilmann (1923) / Lefty O'Doul (1929) / Jimmie Foxx (1929) / Tris Speaker (1923) / Jack Fournier (1925) |
| 1930-1939 | 1.030 | 11.503 | 11.851 | Bill Terry (1930) / Arky Vaughan (1935) / Babe Herman (1930) / Chuck Klein (1930) / Lou Gehrig (1930) / Jimmie Foxx (1932) / Babe Ruth (1930) / Hack Wilson (1930) / Hank Greenberg (1938) |
| 1940-1949 | 1.002 | 10.301 | 10.322 | Roy Cullenbine (1941) / Ted Williams (1941) / Stan Musial (1948) / Ralph Kiner (1949) / Hank Greenberg (1940) / Joe DiMaggio (1941) / Johnny Mize (1940) / Lou Boudreau (1948) / Charlie Keller (1941) |
| 1950-1959 | 0.978 | 9.995 | 9.777 | Ted Williams (1951) / Stan Musial (1951) / Ralph Kiner (1951) / Ted Kluszewski (1954) / Mickey Mantle (1957) / Al Rosen (1953) / Larry Doby (1950) / Willie Mays (1954) / Duke Snider (1954) |
| 1960-1969 | 0.994 | 9.671 | 9.611 | Mickey Mantle (1961) / Jim Wynn (1969) / Norm Cash (1961) / Eddie Mathews (1960) / Willie McCovey (1969) / Harmon Killebrew (1969) / Frank Robinson (1962) / Reggie Jackson (1969) / Carl Yastrzemski (1967) |
| 1970-1979 | 0.984 | 9.271 | 9.124 | Willie McCovey (1970) / Carl Yastrzemski (1970) / Rod Carew (1977) / Jim Hickman (1970) / Tony Perez (1970) / Ken Singleton (1977) / Joe Morgan (1975) / Fred Lynn (1979) / Dick Allen (1972) |
| 1980-1989 | 0.987 | 8.762 | 8.650 | Tony Gwynn (1987) / Mike Schmidt (1980) / Wade Boggs (1987) / Kevin Mitchell (1989) / George Brett (1985) / Dale Murphy (1987) / Tim Raines (1987) / Pedro Guerrero (1987) / Dwight Evans (1987) |
| 1990-1999 | 0.971 | 11.375 | 11.041 | John Olerud (1993) / Larry Walker (1997) / Manny Ramirez (1999) / Mark McGwire (1998) / Barry Bonds (1993) / Edgar Martinez (1995) / Frank Thomas (1996) / Gary Sheffield (1996) / Jeff Bagwell (1999) |
| 2000-2009 | 0.948 | 12.306 | 11.672 | Barry Bonds (2004) / David Ortiz (2007) / Sammy Sosa (2001) / Albert Pujols (2008) / Jim Thome (2002) / Jason Giambi (2001) / Todd Helton (2000) / Carlos Delgado (2000) / Brian Giles (2002) |
| 2010-2019 | 0.970 | 9.922 | 9.622 | Joey Votto (2017) / José Bautista (2011) / Miguel Cabrera (2013) / Mike Trout (2018) / Mookie Betts (2018) / Paul Goldschmidt (2015) / Aaron Judge (2017) / Adrián González (2011) / Bryce Harper (2015) |
| 2020-2025 | 0.986 | 8.662 | 8.541 | Aaron Judge (2024) / Shohei Ohtani (2024) / Freddie Freeman (2023) / Bobby Witt Jr. (2024) / Mookie Betts (2023) / Paul Goldschmidt (2022) / Yordan Alvarez (2024) / Ronald Acuña Jr. (2023) / Juan Soto (2021) |

An all-time no-duplicate lineup mixes player-seasons from many eras and has no single native offensive environment. Applying a different environment to each lineup slot would not represent one coherent baseball game, so no adjusted all-time mixed-era lineup is reported.

## Top 20 Clone Lineups By Decade

### 1900-1909

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Elmer Flick | 1900 | PHI | 1.182 | 8.905 | 10.523 |
| 2 | Cy Seymour | 1905 | CIN | 1.182 | 8.505 | 10.051 |
| 3 | Jesse Burkett | 1901 | SLN | 1.182 | 8.372 | 9.894 |
| 4 | Ed Delahanty | 1901 | PHI | 1.182 | 8.273 | 9.777 |
| 5 | Ty Cobb | 1909 | DET | 1.182 | 8.150 | 9.631 |
| 6 | Honus Wagner | 1908 | PIT | 1.182 | 7.989 | 9.441 |
| 7 | Jimmy Sheckard | 1901 | BRO | 1.182 | 7.646 | 9.036 |
| 8 | Billy Hamilton | 1900 | BSN | 1.182 | 7.532 | 8.900 |
| 9 | George Stone | 1906 | SLA | 1.182 | 7.444 | 8.797 |
| 10 | Kip Selbach | 1900 | NY1 | 1.182 | 7.337 | 8.670 |
| 11 | Mike Donlin | 1905 | NY1 | 1.182 | 7.292 | 8.617 |
| 12 | Topsy Hartsel | 1901 | CHN | 1.182 | 7.091 | 8.380 |
| 13 | Roy Thomas | 1900 | PHI | 1.182 | 7.077 | 8.363 |
| 14 | Eddie Collins | 1909 | PHA | 1.182 | 6.833 | 8.075 |
| 15 | Willie Keeler | 1900 | BRO | 1.182 | 6.371 | 7.529 |
| 16 | Nap Lajoie | 1906 | CLE | 1.182 | 6.344 | 7.497 |
| 17 | John Titus | 1905 | PHI | 1.182 | 6.248 | 7.383 |
| 18 | Dummy Hoy | 1901 | CHA | 1.182 | 6.178 | 7.300 |
| 19 | Jimmy Collins | 1901 | BOS | 1.182 | 6.173 | 7.295 |
| 20 | Sam Crawford | 1902 | CIN | 1.182 | 6.087 | 7.194 |

### 1910-1919

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Ty Cobb | 1911 | DET | 1.055 | 10.997 | 11.603 |
| 2 | Shoeless Joe Jackson | 1911 | CLE | 1.055 | 10.542 | 11.124 |
| 3 | Tris Speaker | 1912 | BOS | 1.055 | 10.212 | 10.776 |
| 4 | Benny Kauff | 1914 | IND | 1.055 | 9.022 | 9.520 |
| 5 | Nap Lajoie | 1910 | CLE | 1.055 | 8.694 | 9.174 |
| 6 | Sherry Magee | 1910 | PHI | 1.055 | 8.617 | 9.093 |
| 7 | Sam Crawford | 1911 | DET | 1.055 | 8.573 | 9.046 |
| 8 | Eddie Collins | 1915 | CHA | 1.055 | 8.335 | 8.795 |
| 9 | Heinie Zimmerman | 1912 | CHN | 1.055 | 8.298 | 8.756 |
| 10 | Home Run Baker | 1912 | PHA | 1.055 | 7.525 | 7.941 |
| 11 | Larry Doyle | 1911 | NY1 | 1.055 | 7.225 | 7.624 |
| 12 | Jimmy Sheckard | 1911 | CHN | 1.055 | 7.086 | 7.477 |
| 13 | Gavvy Cravath | 1915 | PHI | 1.055 | 7.009 | 7.396 |
| 14 | Frank Schulte | 1911 | CHN | 1.055 | 6.954 | 7.338 |
| 15 | Jim Delahanty | 1911 | DET | 1.055 | 6.921 | 7.303 |
| 16 | Bill Sweeney | 1912 | BSN | 1.055 | 6.802 | 7.177 |
| 17 | Honus Wagner | 1912 | PIT | 1.055 | 6.716 | 7.086 |
| 18 | Dode Paskert | 1912 | PHI | 1.055 | 6.678 | 7.046 |
| 19 | Johnny Bates | 1911 | CIN | 1.055 | 6.335 | 6.685 |
| 20 | Bobby Veach | 1917 | DET | 1.055 | 6.304 | 6.652 |

### 1920-1929

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Babe Ruth | 1920 | NYA | 1.000 | 17.263 | 17.254 |
| 2 | Rogers Hornsby | 1924 | SLN | 1.000 | 13.950 | 13.944 |
| 3 | Lou Gehrig | 1927 | NYA | 1.000 | 12.786 | 12.780 |
| 4 | Harry Heilmann | 1923 | DET | 1.000 | 11.729 | 11.723 |
| 5 | Lefty O'Doul | 1929 | PHI | 1.000 | 10.978 | 10.972 |
| 6 | Jimmie Foxx | 1929 | PHA | 1.000 | 10.948 | 10.943 |
| 7 | Tris Speaker | 1923 | CLE | 1.000 | 10.867 | 10.862 |
| 8 | Mel Ott | 1929 | NY1 | 1.000 | 10.381 | 10.376 |
| 9 | George Sisler | 1920 | SLA | 1.000 | 10.336 | 10.331 |
| 10 | Ken Williams | 1923 | SLA | 1.000 | 9.677 | 9.672 |
| 11 | Shoeless Joe Jackson | 1920 | CHA | 1.000 | 9.573 | 9.568 |
| 12 | Babe Herman | 1929 | BRO | 1.000 | 9.475 | 9.471 |
| 13 | Jack Fournier | 1925 | BRO | 1.000 | 9.341 | 9.336 |
| 14 | Hack Wilson | 1929 | CHN | 1.000 | 9.310 | 9.305 |
| 15 | Paul Waner | 1928 | PIT | 1.000 | 9.246 | 9.242 |
| 16 | Chuck Klein | 1929 | PHI | 1.000 | 9.055 | 9.050 |
| 17 | Kiki Cuyler | 1925 | PIT | 1.000 | 8.913 | 8.909 |
| 18 | Joe Sewell | 1923 | CLE | 1.000 | 8.814 | 8.810 |
| 19 | Tony Lazzeri | 1929 | NYA | 1.000 | 8.636 | 8.632 |
| 20 | Ross Youngs | 1924 | NY1 | 1.000 | 8.629 | 8.624 |

### 1930-1939

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Babe Ruth | 1930 | NYA | 1.030 | 13.770 | 14.187 |
| 2 | Jimmie Foxx | 1932 | PHA | 1.030 | 12.650 | 13.033 |
| 3 | Lou Gehrig | 1930 | NYA | 1.030 | 12.116 | 12.484 |
| 4 | Arky Vaughan | 1935 | PIT | 1.030 | 11.940 | 12.302 |
| 5 | Hack Wilson | 1930 | CHN | 1.030 | 11.492 | 11.841 |
| 6 | Babe Herman | 1930 | BRO | 1.030 | 10.977 | 11.310 |
| 7 | Hank Greenberg | 1938 | DET | 1.030 | 10.773 | 11.100 |
| 8 | Chuck Klein | 1930 | PHI | 1.030 | 10.420 | 10.736 |
| 9 | Bill Terry | 1930 | NY1 | 1.030 | 10.278 | 10.590 |
| 10 | Mel Ott | 1930 | NY1 | 1.030 | 10.182 | 10.490 |
| 11 | Johnny Mize | 1939 | SLN | 1.030 | 10.054 | 10.358 |
| 12 | Luke Appling | 1936 | CHA | 1.030 | 9.947 | 10.248 |
| 13 | Earl Averill | 1936 | CLE | 1.030 | 9.768 | 10.064 |
| 14 | Charlie Gehringer | 1937 | DET | 1.030 | 9.517 | 9.805 |
| 15 | Ted Williams | 1939 | BOS | 1.030 | 9.429 | 9.714 |
| 16 | Joe DiMaggio | 1937 | NYA | 1.030 | 9.356 | 9.640 |
| 17 | Dolph Camilli | 1936 | PHI | 1.030 | 9.314 | 9.597 |
| 18 | Joe Medwick | 1937 | SLN | 1.030 | 9.068 | 9.343 |
| 19 | Bob Johnson | 1939 | PHA | 1.030 | 9.006 | 9.279 |
| 20 | Paul Waner | 1936 | PIT | 1.030 | 8.913 | 9.183 |

### 1940-1949

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Ted Williams | 1941 | BOS | 1.002 | 17.638 | 17.673 |
| 2 | Stan Musial | 1948 | SLN | 1.002 | 11.134 | 11.157 |
| 3 | Hank Greenberg | 1940 | DET | 1.002 | 10.211 | 10.232 |
| 4 | Joe DiMaggio | 1941 | NYA | 1.002 | 10.099 | 10.120 |
| 5 | Ralph Kiner | 1949 | PIT | 1.002 | 9.935 | 9.956 |
| 6 | Lou Boudreau | 1948 | CLE | 1.002 | 9.402 | 9.421 |
| 7 | Roy Cullenbine | 1941 | SLA | 1.002 | 8.697 | 8.715 |
| 8 | Johnny Mize | 1940 | SLN | 1.002 | 8.645 | 8.663 |
| 9 | Dixie Walker | 1944 | BRO | 1.002 | 8.641 | 8.659 |
| 10 | Charlie Keller | 1941 | NYA | 1.002 | 8.515 | 8.532 |
| 11 | Jimmie Foxx | 1940 | BOS | 1.002 | 8.456 | 8.473 |
| 12 | Tommy Holmes | 1945 | BSN | 1.002 | 8.416 | 8.434 |
| 13 | Jackie Robinson | 1949 | BRO | 1.002 | 8.389 | 8.406 |
| 14 | Bob Johnson | 1944 | BOS | 1.002 | 8.365 | 8.382 |
| 15 | Whitey Kurowski | 1947 | SLN | 1.002 | 8.347 | 8.364 |
| 16 | Rudy York | 1940 | DET | 1.002 | 8.283 | 8.300 |
| 17 | Dolph Camilli | 1941 | BRO | 1.002 | 8.113 | 8.130 |
| 18 | Augie Galan | 1944 | BRO | 1.002 | 7.903 | 7.919 |
| 19 | Enos Slaughter | 1949 | SLN | 1.002 | 7.763 | 7.778 |
| 20 | Jeff Heath | 1941 | CLE | 1.002 | 7.750 | 7.765 |

### 1950-1959

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Mickey Mantle | 1957 | NYA | 0.978 | 14.199 | 13.889 |
| 2 | Ralph Kiner | 1951 | PIT | 0.978 | 10.381 | 10.155 |
| 3 | Ted Williams | 1951 | BOS | 0.978 | 10.290 | 10.066 |
| 4 | Stan Musial | 1951 | SLN | 0.978 | 10.093 | 9.873 |
| 5 | Duke Snider | 1954 | BRO | 0.978 | 9.648 | 9.438 |
| 6 | Willie Mays | 1954 | NY1 | 0.978 | 9.375 | 9.171 |
| 7 | Larry Doby | 1950 | CLE | 0.978 | 9.028 | 8.831 |
| 8 | Al Rosen | 1953 | CLE | 0.978 | 9.013 | 8.817 |
| 9 | Hank Aaron | 1959 | ML1 | 0.978 | 8.992 | 8.796 |
| 10 | Ted Kluszewski | 1954 | CIN | 0.978 | 8.892 | 8.698 |
| 11 | Eddie Mathews | 1953 | ML1 | 0.978 | 8.689 | 8.500 |
| 12 | Eddie Stanky | 1950 | NY1 | 0.978 | 8.329 | 8.148 |
| 13 | Jackie Robinson | 1951 | BRO | 0.978 | 8.314 | 8.132 |
| 14 | Minnie Minoso | 1956 | CHA | 0.978 | 8.259 | 8.079 |
| 15 | Al Kaline | 1955 | DET | 0.978 | 8.238 | 8.058 |
| 16 | Richie Ashburn | 1955 | PHI | 0.978 | 8.132 | 7.954 |
| 17 | Frank Robinson | 1959 | CIN | 0.978 | 7.914 | 7.741 |
| 18 | Joe DiMaggio | 1950 | NYA | 0.978 | 7.809 | 7.639 |
| 19 | Eddie Yost | 1959 | DET | 0.978 | 7.782 | 7.613 |
| 20 | Hoot Evers | 1950 | DET | 0.978 | 7.780 | 7.610 |

### 1960-1969

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Norm Cash | 1961 | DET | 0.994 | 12.518 | 12.441 |
| 2 | Mickey Mantle | 1961 | NYA | 0.994 | 11.069 | 11.001 |
| 3 | Willie McCovey | 1969 | SFN | 0.994 | 11.014 | 10.946 |
| 4 | Harmon Killebrew | 1969 | MIN | 0.994 | 9.247 | 9.190 |
| 5 | Frank Robinson | 1962 | CIN | 0.994 | 9.128 | 9.072 |
| 6 | Carl Yastrzemski | 1967 | BOS | 0.994 | 9.113 | 9.057 |
| 7 | Jim Wynn | 1969 | HOU | 0.994 | 8.732 | 8.678 |
| 8 | Reggie Jackson | 1969 | OAK | 0.994 | 8.685 | 8.632 |
| 9 | Willie Mays | 1965 | SFN | 0.994 | 8.645 | 8.592 |
| 10 | Rusty Staub | 1969 | MON | 0.994 | 8.392 | 8.341 |
| 11 | Rocky Colavito | 1961 | DET | 0.994 | 8.308 | 8.258 |
| 12 | Rico Petrocelli | 1969 | BOS | 0.994 | 8.273 | 8.223 |
| 13 | Pete Rose | 1969 | CIN | 0.994 | 8.267 | 8.217 |
| 14 | Hank Aaron | 1962 | ML1 | 0.994 | 8.235 | 8.185 |
| 15 | Frank Howard | 1969 | WS2 | 0.994 | 8.047 | 7.998 |
| 16 | Roger Maris | 1961 | NYA | 0.994 | 7.903 | 7.854 |
| 17 | Roberto Clemente | 1967 | PIT | 0.994 | 7.817 | 7.769 |
| 18 | Eddie Mathews | 1960 | ML1 | 0.994 | 7.798 | 7.750 |
| 19 | Ron Santo | 1964 | CHN | 0.994 | 7.763 | 7.716 |
| 20 | Norm Siebern | 1962 | KC1 | 0.994 | 7.668 | 7.621 |

### 1970-1979

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Carl Yastrzemski | 1970 | BOS | 0.984 | 10.037 | 9.878 |
| 2 | Willie McCovey | 1970 | SFN | 0.984 | 10.037 | 9.878 |
| 3 | Joe Morgan | 1975 | CIN | 0.984 | 9.952 | 9.795 |
| 4 | Rod Carew | 1977 | MIN | 0.984 | 9.513 | 9.362 |
| 5 | Fred Lynn | 1979 | BOS | 0.984 | 9.419 | 9.270 |
| 6 | Dick Allen | 1972 | CHA | 0.984 | 8.929 | 8.787 |
| 7 | Jim Hickman | 1970 | CHN | 0.984 | 8.790 | 8.651 |
| 8 | Ken Singleton | 1977 | BAL | 0.984 | 8.671 | 8.533 |
| 9 | Willie Stargell | 1973 | PIT | 0.984 | 8.650 | 8.513 |
| 10 | Jeff Burroughs | 1978 | ATL | 0.984 | 8.622 | 8.486 |
| 11 | Frank Howard | 1970 | WS2 | 0.984 | 8.494 | 8.359 |
| 12 | Joe Torre | 1971 | SLN | 0.984 | 8.483 | 8.348 |
| 13 | Bobby Murcer | 1971 | NYA | 0.984 | 8.458 | 8.324 |
| 14 | Billy Williams | 1972 | CHN | 0.984 | 8.413 | 8.280 |
| 15 | Dick Dietz | 1970 | SFN | 0.984 | 8.394 | 8.261 |
| 16 | John Mayberry | 1975 | KCA | 0.984 | 8.310 | 8.178 |
| 17 | Boog Powell | 1970 | BAL | 0.984 | 8.290 | 8.158 |
| 18 | Tony Perez | 1970 | CIN | 0.984 | 8.246 | 8.116 |
| 19 | Harmon Killebrew | 1970 | MIN | 0.984 | 8.225 | 8.095 |
| 20 | Greg Luzinski | 1977 | PHI | 0.984 | 8.135 | 8.006 |

### 1980-1989

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Wade Boggs | 1987 | BOS | 0.987 | 10.719 | 10.582 |
| 2 | George Brett | 1985 | KCA | 0.987 | 9.383 | 9.263 |
| 3 | Tony Gwynn | 1987 | SDN | 0.987 | 8.996 | 8.881 |
| 4 | Dale Murphy | 1987 | ATL | 0.987 | 8.698 | 8.588 |
| 5 | Dwight Evans | 1987 | BOS | 0.987 | 8.613 | 8.503 |
| 6 | Tim Raines | 1987 | MON | 0.987 | 8.482 | 8.374 |
| 7 | Kevin Mitchell | 1989 | SFN | 0.987 | 8.333 | 8.226 |
| 8 | Pedro Guerrero | 1987 | LAN | 0.987 | 8.174 | 8.070 |
| 9 | Mike Schmidt | 1980 | PHI | 0.987 | 8.139 | 8.035 |
| 10 | Darryl Strawberry | 1987 | NYN | 0.987 | 8.084 | 7.981 |
| 11 | Rickey Henderson | 1985 | NYA | 0.987 | 8.056 | 7.953 |
| 12 | Alvin Davis | 1989 | SEA | 0.987 | 7.996 | 7.894 |
| 13 | Mike Greenwell | 1988 | BOS | 0.987 | 7.983 | 7.882 |
| 14 | Will Clark | 1989 | SFN | 0.987 | 7.911 | 7.811 |
| 15 | Don Mattingly | 1986 | NYA | 0.987 | 7.888 | 7.788 |
| 16 | Alan Trammell | 1987 | DET | 0.987 | 7.838 | 7.738 |
| 17 | Mark McGwire | 1987 | OAK | 0.987 | 7.680 | 7.582 |
| 18 | Jose Canseco | 1988 | OAK | 0.987 | 7.614 | 7.517 |
| 19 | Fred McGriff | 1989 | TOR | 0.987 | 7.572 | 7.476 |
| 20 | Eddie Murray | 1982 | BAL | 0.987 | 7.505 | 7.410 |

### 1990-1999

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Mark McGwire | 1998 | SLN | 0.971 | 12.926 | 12.546 |
| 2 | Edgar Martinez | 1995 | SEA | 0.971 | 11.807 | 11.460 |
| 3 | Larry Walker | 1997 | COL | 0.971 | 11.593 | 11.253 |
| 4 | Barry Bonds | 1993 | SFN | 0.971 | 11.397 | 11.062 |
| 5 | John Olerud | 1993 | TOR | 0.971 | 11.366 | 11.032 |
| 6 | Gary Sheffield | 1996 | FLO | 0.971 | 11.162 | 10.834 |
| 7 | Frank Thomas | 1996 | CHA | 0.971 | 10.963 | 10.640 |
| 8 | Manny Ramirez | 1999 | CLE | 0.971 | 10.784 | 10.467 |
| 9 | Jim Thome | 1996 | CLE | 0.971 | 10.324 | 10.020 |
| 10 | Jeff Bagwell | 1999 | HOU | 0.971 | 10.282 | 9.980 |
| 11 | Chipper Jones | 1999 | ATL | 0.971 | 10.242 | 9.941 |
| 12 | Mike Piazza | 1997 | LAN | 0.971 | 9.850 | 9.560 |
| 13 | Rafael Palmeiro | 1999 | TEX | 0.971 | 9.346 | 9.072 |
| 14 | Bobby Abreu | 1999 | PHI | 0.971 | 9.328 | 9.054 |
| 15 | Tim Salmon | 1995 | CAL | 0.971 | 9.287 | 9.014 |
| 16 | Albert Belle | 1995 | CLE | 0.971 | 9.240 | 8.969 |
| 17 | Brian Giles | 1999 | PIT | 0.971 | 9.181 | 8.911 |
| 18 | Alex Rodriguez | 1996 | SEA | 0.971 | 9.129 | 8.861 |
| 19 | Chuck Knoblauch | 1996 | MIN | 0.971 | 9.085 | 8.818 |
| 20 | Derek Jeter | 1999 | NYA | 0.971 | 9.022 | 8.757 |

### 2000-2009

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Barry Bonds | 2004 | SFG | 0.948 | 24.331 | 23.078 |
| 2 | Jason Giambi | 2001 | OAK | 0.948 | 12.185 | 11.557 |
| 3 | Todd Helton | 2000 | COL | 0.948 | 12.112 | 11.488 |
| 4 | Carlos Delgado | 2000 | TOR | 0.948 | 11.833 | 11.223 |
| 5 | Albert Pujols | 2008 | STL | 0.948 | 11.513 | 10.920 |
| 6 | Sammy Sosa | 2001 | CHC | 0.948 | 11.378 | 10.792 |
| 7 | Jim Thome | 2002 | CLE | 0.948 | 11.032 | 10.464 |
| 8 | Luis Gonzalez | 2001 | ARI | 0.948 | 10.364 | 9.830 |
| 9 | Brian Giles | 2002 | PIT | 0.948 | 10.354 | 9.821 |
| 10 | David Ortiz | 2007 | BOS | 0.948 | 10.158 | 9.635 |
| 11 | Gary Sheffield | 2000 | LAD | 0.948 | 10.118 | 9.596 |
| 12 | Frank Thomas | 2000 | CHW | 0.948 | 10.011 | 9.495 |
| 13 | Ryan Howard | 2006 | PHI | 0.948 | 9.912 | 9.401 |
| 14 | Joe Mauer | 2009 | MIN | 0.948 | 9.734 | 9.232 |
| 15 | Alex Rodriguez | 2007 | NYY | 0.948 | 9.696 | 9.197 |
| 16 | Derrek Lee | 2005 | CHC | 0.948 | 9.653 | 9.156 |
| 17 | Jim Edmonds | 2004 | STL | 0.948 | 9.552 | 9.060 |
| 18 | Lance Berkman | 2001 | HOU | 0.948 | 9.511 | 9.021 |
| 19 | Magglio Ordóñez | 2007 | DET | 0.948 | 9.440 | 8.954 |
| 20 | Manny Ramírez | 2008 | 2TM | 0.948 | 9.387 | 8.903 |

### 2010-2019

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Bryce Harper | 2015 | WSN | 0.970 | 11.218 | 10.879 |
| 2 | Mike Trout | 2018 | LAA | 0.970 | 11.012 | 10.679 |
| 3 | Mookie Betts | 2018 | BOS | 0.970 | 10.244 | 9.934 |
| 4 | Joey Votto | 2017 | CIN | 0.970 | 10.243 | 9.934 |
| 5 | José Bautista | 2011 | TOR | 0.970 | 10.183 | 9.875 |
| 6 | Miguel Cabrera | 2013 | DET | 0.970 | 10.177 | 9.870 |
| 7 | Aaron Judge | 2017 | NYY | 0.970 | 9.448 | 9.163 |
| 8 | Paul Goldschmidt | 2015 | ARI | 0.970 | 9.310 | 9.029 |
| 9 | Alex Bregman | 2019 | HOU | 0.970 | 8.969 | 8.698 |
| 10 | Albert Pujols | 2010 | STL | 0.970 | 8.900 | 8.631 |
| 11 | Anthony Rendon | 2019 | WSN | 0.970 | 8.740 | 8.476 |
| 12 | J.D. Martinez | 2018 | BOS | 0.970 | 8.736 | 8.472 |
| 13 | Cody Bellinger | 2019 | LAD | 0.970 | 8.726 | 8.462 |
| 14 | David Ortiz | 2016 | BOS | 0.970 | 8.604 | 8.344 |
| 15 | Prince Fielder | 2011 | MIL | 0.970 | 8.409 | 8.155 |
| 16 | Christian Yelich | 2018 | MIL | 0.970 | 8.237 | 7.988 |
| 17 | Charlie Blackmon | 2017 | COL | 0.970 | 8.219 | 7.971 |
| 18 | Victor Martinez | 2014 | DET | 0.970 | 8.205 | 7.958 |
| 19 | Matt Kemp | 2011 | LAD | 0.970 | 8.204 | 7.957 |
| 20 | Buster Posey | 2012 | SFG | 0.970 | 8.187 | 7.940 |

### 2020-2025

| Rank | Player Name | Season | Team | Environment Factor | Fixed Environment Runs Per 9 | Era Environment Runs Per 9 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Aaron Judge | 2024 | NYY | 0.986 | 11.505 | 11.345 |
| 2 | Juan Soto | 2021 | WSN | 0.986 | 9.883 | 9.745 |
| 3 | Ronald Acuña Jr. | 2023 | ATL | 0.986 | 8.642 | 8.522 |
| 4 | Shohei Ohtani | 2024 | LAD | 0.986 | 8.635 | 8.514 |
| 5 | Mookie Betts | 2023 | LAD | 0.986 | 8.215 | 8.101 |
| 6 | Vladimir Guerrero Jr. | 2021 | TOR | 0.986 | 8.119 | 8.006 |
| 7 | Bobby Witt Jr. | 2024 | KCR | 0.986 | 8.033 | 7.921 |
| 8 | Freddie Freeman | 2023 | LAD | 0.986 | 8.009 | 7.897 |
| 9 | Paul Goldschmidt | 2022 | STL | 0.986 | 7.970 | 7.859 |
| 10 | Matt Olson | 2023 | ATL | 0.986 | 7.894 | 7.785 |
| 11 | Yordan Alvarez | 2024 | HOU | 0.986 | 7.466 | 7.362 |
| 12 | Jose Altuve | 2022 | HOU | 0.986 | 7.165 | 7.065 |
| 13 | Bryan Reynolds | 2021 | PIT | 0.986 | 7.151 | 7.052 |
| 14 | Trea Turner | 2021 | 2TM | 0.986 | 7.095 | 6.996 |
| 15 | Cal Raleigh | 2025 | SEA | 0.986 | 7.080 | 6.981 |
| 16 | Brent Rooker | 2024 | OAK | 0.986 | 6.908 | 6.812 |
| 17 | Marcell Ozuna | 2024 | ATL | 0.986 | 6.870 | 6.774 |
| 18 | Kyle Schwarber | 2025 | PHI | 0.986 | 6.869 | 6.774 |
| 19 | Bryce Harper | 2024 | PHI | 0.986 | 6.616 | 6.524 |
| 20 | Gunnar Henderson | 2024 | BAL | 0.986 | 6.566 | 6.475 |

## Runtime

Completed in 21.4 minutes.
