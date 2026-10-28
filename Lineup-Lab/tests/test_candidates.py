import pandas as pd

from baseball_lineup_optimizer.experiments.candidates import (
    add_component_composite,
    build_candidate_pool,
)


def test_candidate_pool_includes_low_k_and_power_routes():
    rows = []
    for index in range(40):
        rows.append(
            {
                "player_id": index,
                "player_name": f"Player {index}",
                "woba": index / 100,
                "wrc_plus": index,
                "obp": index / 100,
                "slg": index / 100,
                "iso": index / 100,
                "bb_rate": index / 100,
                "k_rate": (40 - index) / 100,
                "xbh_per_ab": index / 100,
                "hr_per_ab": index / 100,
                "single_per_ab": index / 100,
                "bb_per_k": index / 100,
            }
        )
    pool = pd.DataFrame(rows)

    candidates = build_candidate_pool(pool, top_k_per_metric=3)

    assert len(candidates) >= 3
    assert candidates["candidate_reasons"].str.contains("low_k_rate").any()
    assert candidates["candidate_reasons"].str.contains("high_hr_per_ab").any()


def test_component_score_rewards_good_rates_and_penalizes_k_rate():
    pool = pd.DataFrame(
        [
            {"woba": 0.400, "bb_per_k": 0.800, "xbh_per_ab": 0.160, "hr_per_ab": 0.060, "single_per_ab": 0.150, "k_rate": 0.150},
            {"woba": 0.300, "bb_per_k": 0.200, "xbh_per_ab": 0.080, "hr_per_ab": 0.020, "single_per_ab": 0.100, "k_rate": 0.300},
        ]
    )

    scored = add_component_composite(pool)

    assert scored.loc[0, "component_score"] > scored.loc[1, "component_score"]
