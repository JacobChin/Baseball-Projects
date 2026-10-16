from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from pybaseball import playerid_reverse_lookup, statcast


ROOT = Path(__file__).parent
OUTPUT = ROOT / "data" / "statcast_bbe_2024_2026.parquet"
CACHE_DIR = ROOT / "data" / "cache_2026"
LOCAL_2024 = Path(r"E:\Baseball\Data\Savant\2024_statcast_full.parquet")
LOCAL_2025 = Path(r"E:\Baseball\Data\Savant\2025_Hitters_Bat_Tracking_Full")
KEEP_COLUMNS = [
    "game_date", "release_speed", "batter", "events", "description", "zone",
    "stand", "p_throws", "bb_type", "balls", "strikes", "game_year", "hc_x",
    "hc_y", "hit_distance_sc", "launch_speed", "launch_angle",
    "estimated_ba_using_speedangle", "estimated_woba_using_speedangle", "pitch_name",
    "bat_speed", "swing_length", "attack_angle", "attack_direction", "swing_path_tilt",
    "intercept_ball_minus_batter_pos_y_inches",
]


def pitch_bucket(name: str) -> str:
    if name in {"4-Seam Fastball", "Sinker", "Cutter"}:
        return "Fastball"
    if name in {"Changeup", "Split-Finger", "Forkball", "Screwball"}:
        return "Offspeed"
    return "Breaking"


def trim(data: pd.DataFrame) -> pd.DataFrame:
    for column in KEEP_COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA
    out = data.loc[data["bb_type"].notna(), KEEP_COLUMNS].copy()
    out["pitch_bucket"] = out["pitch_name"].map(pitch_bucket)
    return out


def add_batter_names(data: pd.DataFrame) -> pd.DataFrame:
    ids = data["batter"].dropna().astype(int).unique().tolist()
    lookup = playerid_reverse_lookup(ids, key_type="mlbam")
    lookup["batter_name"] = lookup["name_first"].str.strip() + " " + lookup["name_last"].str.strip()
    name_map = lookup.set_index("key_mlbam")["batter_name"]
    data["batter_name"] = data["batter"].astype("Int64").map(name_map)
    return data


def download_2026(end_date: str) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cursor = pd.Timestamp("2026-03-25")
    end = pd.Timestamp(end_date)
    chunks = []
    while cursor <= end:
        chunk_end = min(cursor + pd.offsets.MonthEnd(0), end)
        cache_path = CACHE_DIR / f"statcast_{cursor:%Y%m%d}_{chunk_end:%Y%m%d}.parquet"
        if cache_path.exists():
            print(f"Using cached {cache_path.name}")
            chunk = pd.read_parquet(cache_path)
        else:
            print(f"Downloading {cursor:%Y-%m-%d} through {chunk_end:%Y-%m-%d}...")
            chunk = statcast(cursor.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d"))
            chunk.to_parquet(cache_path, index=False, compression="zstd")
        chunks.append(chunk)
        cursor = chunk_end + pd.Timedelta(days=1)
    return pd.concat(chunks, ignore_index=True)


def main(end_date: str) -> None:
    datetime.strptime(end_date, "%Y-%m-%d")
    data_2026 = download_2026(end_date)
    combined = pd.concat([
        trim(pd.read_parquet(LOCAL_2024)),
        trim(pd.read_parquet(LOCAL_2025)),
        trim(data_2026),
    ], ignore_index=True)
    combined = add_batter_names(combined)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(OUTPUT, index=False, compression="zstd")
    print(f"Saved {len(combined):,} batted balls to {OUTPUT} ({OUTPUT.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the compact Advanced Spray Chart dataset.")
    parser.add_argument("--end-date", default=date.today().isoformat())
    args = parser.parse_args()
    main(args.end_date)


