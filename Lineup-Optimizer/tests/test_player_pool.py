import pandas as pd

from baseball_lineup_optimizer.config import EligibilityConfig
from baseball_lineup_optimizer.data.player_pool import build_player_pool


def test_build_player_pool_from_fangraphs_style_columns():
    raw = pd.DataFrame(
        [
            {
                "IDfg": 1,
                "Name": "Great Hitter",
                "Season": 2025,
                "Team": "ABC",
                "PA": 100,
                "AB": 88,
                "BB": 10,
                "HBP": 2,
                "H": 30,
                "2B": 5,
                "3B": 1,
                "HR": 7,
                "SO": 20,
                "wOBA": 0.420,
                "wRC+": 170,
                "OBP": 0.410,
                "SLG": 0.600,
                "ISO": 0.250,
                "BB%": "10.0%",
                "K%": "20.0%",
                "Rdp": 1.5,
                "GDP": 4,
                "GDPRuns": 1.25,
            },
            {
                "IDfg": 2,
                "Name": "Small Sample",
                "Season": 2025,
                "Team": "XYZ",
                "PA": 20,
                "BB": 1,
                "HBP": 0,
                "H": 4,
                "2B": 1,
                "3B": 0,
                "HR": 1,
                "SO": 6,
            },
        ]
    )

    pool, report = build_player_pool(
        raw,
        EligibilityConfig(season=2025, minimum_pa=50),
    )

    assert report.raw_rows == 2
    assert report.eligible_rows == 1
    assert report.passed
    assert pool.loc[0, "player_name"] == "Great Hitter"
    assert pool.loc[0, "single"] == 17
    assert pool.loc[0, "other_out"] == 38
    assert pool.loc[0, "bb_rate"] == 0.10
    assert pool.loc[0, "k_rate"] == 0.20
    assert pool.loc[0, "xbh"] == 13
    assert pool.loc[0, "xbh_per_ab"] == 13 / 88
    assert pool.loc[0, "hr_per_ab"] == 7 / 88
    assert pool.loc[0, "single_per_ab"] == 17 / 88
    assert pool.loc[0, "bb_per_k"] == 10 / 20
    assert pool.loc[0, "gdp"] == 4
    assert pool.loc[0, "rdp"] == 1.5
    assert pool.loc[0, "gdp_runs"] == 1.25
    assert pool.loc[0, "gdp_per_pa"] == 4 / 100
