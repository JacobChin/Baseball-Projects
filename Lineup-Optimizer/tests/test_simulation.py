import pytest

from baseball_lineup_optimizer.engine.outcomes import make_synthetic_hitter
from baseball_lineup_optimizer.engine.simulation import expected_runs


def test_always_out_lineup_scores_zero():
    hitter = make_synthetic_hitter("Always Out", {"other_out": 1.0})

    result = expected_runs([hitter] * 9, games=25, seed=1)

    assert result.runs_per_game == 0
    assert result.run_min == 0
    assert result.run_max == 0


def test_no_out_lineup_trips_plate_appearance_guard():
    hitter = make_synthetic_hitter("Always Walk", {"bb": 1.0})

    with pytest.raises(RuntimeError, match="max_plate_appearances"):
        expected_runs([hitter] * 9, games=1, seed=1, max_plate_appearances_per_game=50)


def test_stronger_synthetic_lineup_beats_weak_synthetic_lineup():
    strong = make_synthetic_hitter(
        "Strong",
        {"bb": 0.12, "single": 0.16, "double": 0.06, "hr": 0.06, "k": 0.22, "other_out": 0.38},
    )
    weak = make_synthetic_hitter(
        "Weak",
        {"bb": 0.05, "single": 0.08, "double": 0.02, "hr": 0.01, "k": 0.30, "other_out": 0.54},
    )

    strong_result = expected_runs([strong] * 9, games=2_000, seed=10)
    weak_result = expected_runs([weak] * 9, games=2_000, seed=10)

    assert strong_result.runs_per_game > weak_result.runs_per_game

