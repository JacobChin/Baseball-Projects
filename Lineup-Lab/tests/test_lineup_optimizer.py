from baseball_lineup_optimizer.engine.lineup_optimizer import candidate_orders, optimize_lineup_order
from baseball_lineup_optimizer.engine.outcomes import make_synthetic_hitter


def test_candidate_orders_collapse_identical_duplicate_lineups():
    judge = make_synthetic_hitter(
        "Judge Clone",
        {"bb": 0.18, "hbp": 0.01, "single": 0.14, "double": 0.06, "triple": 0.0, "hr": 0.09, "k": 0.24, "other_out": 0.28},
        player_id="judge",
    )
    lineup = [judge] * 9

    orders = candidate_orders(lineup, random_order_count=10)

    assert len(orders) == 1
    assert orders[0][0] == "Selected order"


def test_optimizer_returns_result_for_duplicate_lineup():
    judge = make_synthetic_hitter(
        "Judge Clone",
        {"bb": 0.18, "hbp": 0.01, "single": 0.14, "double": 0.06, "triple": 0.0, "hr": 0.09, "k": 0.24, "other_out": 0.28},
        player_id="judge",
    )

    result = optimize_lineup_order([judge] * 9, games_per_order=5, final_games=5, random_order_count=5)

    assert result.orders_tested == 1
    assert len(result.lineup) == 9
    assert result.result.runs_per_game >= 0
