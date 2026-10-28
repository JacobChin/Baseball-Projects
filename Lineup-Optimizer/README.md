# Lineup Optimizer

An interactive Streamlit app and Monte Carlo research project for estimating MLB lineup run production, comparing batting orders, and exploring how different hitter profiles interact within an offense.

## Features

- Select any nine 2025 hitters, including duplicate players.
- Fill all nine lineup slots with one hitter for clone-lineup experiments.
- Simulate a selected batting order over 250 to 5,000 nine-inning games.
- Search candidate batting orders and compare the optimized order with the selected order.
- Estimate the probability of scoring at least one run before three outs.
- Create, edit, save, and reuse custom hitters.
- Import a player-season from Baseball-Reference and adjust individual attributes.
- Use contextual non-intentional walk probabilities based on the current hitter, on-deck threat, base/out state, inning, and score.
- Model stolen bases, double plays, Sprint Speed advancement, and empirical batted-ball transitions.

## Model Overview

The simulator samples each plate appearance from the hitter's season-level outcome profile, then advances runners with empirical transition distributions. Production defaults include:

- 2025 hitter outcome profiles.
- Direct runner-movement transitions reconstructed from 2021-2025 StatsAPI plays.
- Six Sprint Speed-sensitive advancement models.
- A beta-binomial behavioral stolen-base model with separate attempt and success probabilities by base/out context.
- A fitted home-to-first double-play adjustment.
- An optional contextual non-IBB walk model.
- No wild pitches, passed balls, errors, pitcher hitting, or sacrifice-bunt optimization.

This is an offensive research simulator, not a forecast of team wins or a claim that one lineup is universally optimal. See [`docs/model_specification.md`](docs/model_specification.md) for assumptions and limitations.

## Selected Results

The high-precision cross-era search found this all-time no-duplicate lineup at **14.9275 runs per nine innings** in the common-input simulation environment:

1. Barry Bonds, 2004
2. Ted Williams, 1941
3. Babe Ruth, 1920
4. Mickey Mantle, 1957
5. Rogers Hornsby, 1924
6. Norm Cash, 1961
7. Mark McGwire, 1998
8. Todd Helton, 2000
9. Jimmie Foxx, 1932

The reported finalist orders were simulated for 100,000 games each. Historical comparisons retain actual strikeouts and stolen bases, standardize missing caught-stealing information, and neutralize unavailable pre-Statcast running and batted-ball detail.

- [No-duplicate lineups by decade and all time](results/no_duplicate_lineups_by_decade_and_all_time.md)
- [All-time clone leaderboard](results/all_time_top20_clone_runs9.md)
- [Current 2025 optimal-lineup report](results/current_optimal_lineups_2025.md)

## Project Structure

- `app.py` - Streamlit application entry point.
- `baseball_lineup_optimizer/` - Simulation, transition, optimization, and data-loading code.
- `data/processed/` - Compact app-ready hitter profiles and fitted runtime artifacts.
- `docs/` - Model specification and assumptions.
- `results/` - Selected high-precision leaderboards and reports.
- `tests/` - Core simulator and engine tests.
- `requirements.txt` - Hosted-app dependencies.

## Run The App

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The repository includes all compact runtime artifacts required by the app. Raw Statcast downloads, fitting checkpoints, and large intermediate audit tables are intentionally excluded.

## Data Sources

- Baseball Savant / Statcast
- MLB StatsAPI structured runner movements
- FanGraphs season batting data
- Baseball-Reference historical player-season data

All source data remains subject to the terms of its original provider.
