"""The hash-draw properties from three source tests (`test_judge_model.py`,
`test_ablation_arms.py`, `test_allocator.py`) collapsed to one set, plus
`entry_rate`, `pass_mark` and `Ladder`."""
import pytest

from preregister import nulls

TS = "2026-01-01T00:00:00+00:00"


def test_stable_uniform_is_bit_identical_to_the_source() -> None:
    # repete1: judge_model._uniform("BTC/USD", TS, "abl-1") -> 0.2706681860855986
    assert nulls.stable_uniform("BTC/USD", TS, salt="abl-1") == 0.2706681860855986


def test_stable_normal_is_bit_identical_to_the_source() -> None:
    # repete1: allocator._draw(0.0, 1.0, "2026-01-01T00:00:00+00:00|xsmom|v1")
    assert nulls.stable_normal(0.0, 1.0, f"{TS}|xsmom|v1") == 1.1945890754651198


def test_the_same_inputs_reproduce_exactly() -> None:
    """Without this, a re-run of a gate is a new experiment wearing an old name."""
    a = [nulls.stable_uniform(s, TS, salt="x") for s in ("A", "B", "C")]
    b = [nulls.stable_uniform(s, TS, salt="x") for s in ("A", "B", "C")]
    assert a == b


def test_a_different_salt_produces_a_different_draw() -> None:
    """THE negative control. Five 'salts' that drew the same numbers would be
    one arm reported five times, and the variance band a fabrication."""
    draws = {nulls.stable_uniform("A", TS, salt=f"s{i}") for i in range(5)}
    assert len(draws) == 5


def test_a_draw_does_not_depend_on_what_was_drawn_before_it() -> None:
    alone = nulls.stable_uniform("C", TS, salt="x")
    _ = [nulls.stable_uniform(s, TS, salt="x") for s in ("A", "B")]
    assert nulls.stable_uniform("C", TS, salt="x") == alone


def test_uniform_is_in_the_half_open_unit_interval_and_not_degenerate() -> None:
    xs = [nulls.stable_uniform(i, salt="u") for i in range(2000)]
    assert all(0.0 <= x < 1.0 for x in xs)
    assert 0.45 < sum(xs) / len(xs) < 0.55


def test_normal_has_the_requested_moments_roughly() -> None:
    xs = [nulls.stable_normal(5.0, 2.0, f"n|{i}") for i in range(4000)]
    m = sum(xs) / len(xs)
    sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5
    assert abs(m - 5.0) < 0.15 and abs(sd - 2.0) < 0.15


def test_entry_rate() -> None:
    assert nulls.entry_rate(4, 40) == pytest.approx(0.1)
    assert nulls.entry_rate(4, 0) == 0.0


@pytest.mark.parametrize("null,bh,want", [
    (True, True, True), (True, False, False), (False, True, False),
    (None, True, False), (True, None, False),
])
def test_pass_mark_requires_every_named_comparison(null: bool | None, bh: bool | None,
                                                   want: bool) -> None:
    v = {"random": null, "buy and hold": bh, "diagnostic": True}
    assert nulls.pass_mark(v, ("random", "buy and hold")) is want


def test_pass_mark_ignores_rows_it_was_not_told_to_require() -> None:
    assert nulls.pass_mark({"diagnostic": True}, ("random",)) is False


def test_ladder_judges_and_applies_the_pass_mark() -> None:
    lad = nulls.Ladder(required=("null",), salts=("s1", "s2"), k=3, resamples=300)
    base = [nulls.stable_normal(0.0, 1.0, f"b|{i}") for i in range(60)]
    treat = [x + 3.0 for x in base]
    assert lad.judge("null", base, treat) is True
    assert lad.judge("empty", [], treat) is None
    assert lad.passed is True
    assert "INCONCLUSIVE" in lad.described["empty"]
    lad2 = nulls.Ladder(required=("null", "empty"), salts=("s1",), k=3, resamples=300)
    lad2.judge("null", base, treat)
    lad2.judge("empty", [], treat)
    assert lad2.passed is False, "an unmeasurable required baseline is a FAIL"
