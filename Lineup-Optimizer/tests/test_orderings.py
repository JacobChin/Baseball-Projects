from baseball_lineup_optimizer.engine.outcomes import make_synthetic_hitter
from baseball_lineup_optimizer.experiments.orderings import (
    alternate_high_low,
    order_by_metric,
    random_orders,
    sabermetric_heuristic_order,
)


def _hitter(name: str, woba: float, obp: float, slg: float):
    hitter = make_synthetic_hitter(name, {"other_out": 1.0})
    return hitter.__class__(
        player_id=hitter.player_id,
        player_name=hitter.player_name,
        probabilities=hitter.probabilities,
        metadata={"woba": woba, "obp": obp, "slg": slg},
    )


def test_order_by_metric_descending():
    lineup = [_hitter("A", 0.300, 0.300, 0.400), _hitter("B", 0.400, 0.350, 0.500)]

    ordered = order_by_metric(lineup, "woba")

    assert [h.player_name for h in ordered] == ["B", "A"]


def test_ordering_helpers_preserve_lineup_membership():
    lineup = [
        _hitter(str(index), 0.300 + index / 1000, 0.310 + index / 1000, 0.400 + index / 1000)
        for index in range(9)
    ]

    variants = [
        alternate_high_low(lineup),
        sabermetric_heuristic_order(lineup),
        random_orders(lineup, n=1, seed=1)[0],
    ]

    expected_ids = sorted(h.player_id for h in lineup)
    for variant in variants:
        assert len(variant) == 9
        assert sorted(h.player_id for h in variant) == expected_ids

