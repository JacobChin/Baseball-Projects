from baseball_lineup_optimizer.engine.advancement import (
    BaseOutState,
    apply_deterministic_advancement,
)


def test_walk_forces_only_when_required():
    result = apply_deterministic_advancement(
        BaseOutState(on_first=False, on_second=True, on_third=True, outs=1),
        "bb",
    )

    assert result.runs == 0
    assert result.state == BaseOutState(on_first=True, on_second=False, on_third=True, outs=1)


def test_walk_with_bases_loaded_scores_one():
    result = apply_deterministic_advancement(
        BaseOutState(on_first=True, on_second=True, on_third=True, outs=2),
        "bb",
    )

    assert result.runs == 1
    assert result.state == BaseOutState(on_first=True, on_second=True, on_third=True, outs=2)


def test_double_advances_runners_two_bases():
    result = apply_deterministic_advancement(
        BaseOutState(on_first=True, on_second=True, on_third=True, outs=0),
        "double",
    )

    assert result.runs == 2
    assert result.state == BaseOutState(on_first=False, on_second=True, on_third=True, outs=0)


def test_out_adds_one_out_and_holds_runners():
    result = apply_deterministic_advancement(
        BaseOutState(on_first=True, on_second=False, on_third=True, outs=1),
        "k",
    )

    assert result.runs == 0
    assert result.state == BaseOutState(on_first=True, on_second=False, on_third=True, outs=2)

