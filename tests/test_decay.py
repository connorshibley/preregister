"""Ported from the bot's `test_decay_stats.py` (percentile rank, the three
bands, determinism, the min-n short circuit) with the synthetic-trade
mechanics replaced by an injected draw."""
import random

import pytest

from preregister import decay


def _draw(rng: random.Random) -> float | None:
    return rng.gauss(0.0, 1.0)


def test_percentile_rank_is_strict_fraction_below() -> None:
    assert decay.percentile_rank(2.5, [1, 2, 3, 4]) == 50.0
    assert decay.percentile_rank(2.0, [1, 2, 3, 4]) == 25.0
    assert decay.percentile_rank(9.0, []) == 0.0


def test_null_distribution_is_deterministic_and_seed_sensitive() -> None:
    a = decay.null_distribution(_draw, 10, n_samples=50, seed=1)
    b = decay.null_distribution(_draw, 10, n_samples=50, seed=1)
    c = decay.null_distribution(_draw, 10, n_samples=50, seed=2)
    assert a == b and a != c and len(a) == 50


def test_an_unusable_draw_is_retried_never_substituted() -> None:
    seen = {"none": 0}

    def flaky(rng: random.Random) -> float | None:
        if rng.random() < 0.5:
            seen["none"] += 1
            return None
        return 1.0

    dist = decay.null_distribution(flaky, 5, n_samples=20, seed=3)
    assert seen["none"] > 0 and all(m == 1.0 for m in dist)


def test_a_draw_that_never_succeeds_is_bounded_and_yields_nothing() -> None:
    dist = decay.null_distribution(lambda rng: None, 5, n_samples=3, seed=3, max_draws_per_obs=4)
    assert dist == []


@pytest.mark.parametrize("pct,want", [
    (4.9, "WORSE_THAN_RANDOM"), (5.0, "INDISTINGUISHABLE_FROM_RANDOM"),
    (94.9, "INDISTINGUISHABLE_FROM_RANDOM"), (95.0, "BEATS_RANDOM"),
])
def test_bands(pct: float, want: str) -> None:
    assert decay.band(pct, low=5.0, high=95.0) == want


def test_verdict_short_circuits_below_min_obs_without_simulating() -> None:
    def boom(rng: random.Random) -> float | None:
        raise AssertionError("must not be called")

    v = decay.verdict_for("s", [1.0] * 19, boom, min_obs=20, n_samples=10, seed=1, low=5, high=95)
    assert v.verdict == "INSUFFICIENT_DATA" and v.percentile is None and not v.alert


def test_a_planted_edge_is_detected_and_a_planted_loss_alerts() -> None:
    good = [3.0 + 0.01 * i for i in range(40)]
    bad = [-3.0] * 40
    kw = dict(min_obs=20, n_samples=300, seed=7, low=5.0, high=95.0)
    assert decay.verdict_for("g", good, _draw, **kw).verdict == "BEATS_RANDOM"  # type: ignore[arg-type]
    v = decay.verdict_for("b", bad, _draw, **kw)  # type: ignore[arg-type]
    assert v.verdict == "WORSE_THAN_RANDOM" and v.alert


def test_noise_is_indistinguishable_through_the_real_entry_point() -> None:
    rng = random.Random(11)
    noise = [rng.gauss(0.0, 1.0) for _ in range(60)]
    v = decay.verdict_for("n", noise, _draw, min_obs=20, n_samples=300, seed=5, low=5, high=95)
    assert v.verdict == "INDISTINGUISHABLE_FROM_RANDOM"
