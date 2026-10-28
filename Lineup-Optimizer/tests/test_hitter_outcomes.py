import pandas as pd

from baseball_lineup_optimizer.features.hitter_outcomes import (
    add_other_outs,
    add_outcome_probabilities,
    check_outcome_probabilities,
)


def test_outcome_probabilities_sum_to_one():
    df = pd.DataFrame(
        [
            {
                "player_id": "test",
                "season": 2025,
                "pa": 100,
                "bb": 10,
                "hbp": 2,
                "single": 15,
                "double": 5,
                "triple": 1,
                "hr": 7,
                "k": 20,
            }
        ]
    )

    with_outs = add_other_outs(df)
    with_probabilities = add_outcome_probabilities(with_outs)
    check = check_outcome_probabilities(with_probabilities)

    assert with_outs.loc[0, "other_out"] == 40
    assert check.passed

