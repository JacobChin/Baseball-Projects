# Advanced Spray Chart

An interactive Streamlit app for exploring hitter spray charts and advanced batted-ball leaderboards across the 2024, 2025, and 2026 seasons.

## Features

- Filter by season, hitter, count, pitch group/type, zone, pitcher handedness, result, and normalized spray angle.
- Mirror zone filters automatically for left- and right-handed hitters.
- Define squared-up contact at any threshold and show all, over-threshold, or under-threshold batted balls.
- Compare xBA, xWOBA, EV50, median launch angle, bat speed, swing length, attack metrics, contact depth, and squared-up rate.
- Build composite percentile leaderboards with independently selected high/low directions.
- Search for a player inside the complete filtered leaderboard.
- Download interactive spray charts and leaderboard CSV files.

## Project Structure

- `app.py` - Streamlit application entry point.
- `data/` - Compact 2024-2026 app-ready Statcast dataset.
- `notebooks/` - Original Jupyter notebook workflow.
- `scripts/` - Dataset download and refresh utilities.
- `assets/` - Spray chart and leaderboard demonstration GIFs.
- `requirements.txt` - Python dependencies.
## Run The App

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The repository includes the compact app-ready dataset at `data/statcast_bbe_2024_2026.parquet`, so no notebook setup is required.

## Refresh The Data

To rebuild the dataset through a particular date:

```powershell
python scripts/prepare_data.py --end-date 2026-10-16
```

The preparation script uses the local 2024 and 2025 source files configured near the top of `scripts/prepare_data.py`, downloads 2026 data with `pybaseball`, keeps only fields used by the app, and writes a compressed parquet file.
