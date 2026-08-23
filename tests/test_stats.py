"""Ported from the source bot's `tests/test_significance.py` (14 tests) plus
the bootstrap/concentration tests from `tests/test_gate_script_helpers.py`,
with the `$`/trade wording removed and two bit-exactness pins added so the
bot's later re-export has a known target.
"""
import random

import pytest

from preregister import stats


def _noise(n: int, seed: int, scale: float = 10.0) -> list[float]:
    rng = random.Random(seed)
    return [rng.gauss(0.0, scale) for _ in range(n)]


# ---- bit-exactness against the source (computed 2026-08-22 in repete1's venv):
#   .venv/bin/python -c "import sys; sys.path.insert(0,'src'); import significance as s;
#     r = s.compare(B, C, n_comparisons=66, resamples=2000, seed=20260723); print(r.ci_low, r.ci_high, r.alpha)"
_B = [1.0, -2.0, 3.5, 0.25, -1.25, 2.0, -0.5, 4.0, -3.0, 1.5, 0.75, -0.25]
_C = [2.0, -1.0, 4.5, 1.25, -0.25, 3.0, 0.5, 5.0, -2.0, 2.5, 1.75, 0.75]


def test_compare_is_bit_identical_to_the_source_implementation() -> None:
    r = stats.compare(_B, _C, n_comparisons=66, resamples=2000, seed=20260723)
    assert r.ci_low == -0.41666666666666674
    assert r.ci_high == 2.3333333333333335
    assert r.alpha == 0.0007575757575757576


def test_identical_arms_are_inconclusive() -> None:
    a, b = _noise(200, 1), _noise(200, 2)
    c = stats.compare(a, b, n_comparisons=1)
    assert c.verdict == "INCONCLUSIVE"
    assert c.ci_low < 0 < c.ci_high
    assert not c.significant


def test_large_real_difference_is_detected() -> None:
    """If this had no power, every INCONCLUSIVE below would be meaningless."""
    base = _noise(200, 3, scale=50.0)
    cand = [x + 200.0 for x in _noise(200, 4, scale=50.0)]
    c = stats.compare(base, cand, n_comparisons=1)
    assert c.verdict == "SIGNIFICANT" and c.ci_low > 0


def test_worse_candidate_is_named_as_worse() -> None:
    base = [x + 200.0 for x in _noise(200, 5, scale=50.0)]
    cand = _noise(200, 6, scale=50.0)
    c = stats.compare(base, cand, n_comparisons=1)
    assert c.verdict == "SIGNIFICANTLY WORSE" and c.ci_high < 0


def test_bonferroni_widens_the_interval() -> None:
    """More arms tried -> a wider interval -> a higher bar. If K stopped
    mattering the correction would be decorative."""
    base = _noise(150, 7)
    cand = [x + 40.0 for x in _noise(150, 8)]
    narrow = stats.compare(base, cand, n_comparisons=1)
    wide = stats.compare(base, cand, n_comparisons=10)
    assert wide.ci_high - wide.ci_low > narrow.ci_high - narrow.ci_low
    assert wide.alpha < narrow.alpha


def test_k_can_come_from_anything_with_a_k_method() -> None:
    class Reg:
        def k(self) -> int:
            return 10

    base, cand = _noise(150, 7), [x + 40.0 for x in _noise(150, 8)]
    assert stats.compare(base, cand, n_comparisons=Reg()) == \
        stats.compare(base, cand, n_comparisons=10)
    assert stats.resolve_k(0) == 1, "K below 1 is clamped, never a division by zero"


def test_deterministic_across_runs() -> None:
    base, cand = _noise(100, 9), _noise(100, 10)
    assert stats.compare(base, cand, n_comparisons=3) == stats.compare(base, cand, n_comparisons=3)


def test_block_length_is_sqrt_n() -> None:
    assert stats.block_length(100) == 10
    assert stats.block_length(1) == 1
    assert stats.block_length(0) == 1


def test_blocks_preserve_clustering() -> None:
    """A series that is all-losses-then-all-wins keeps its runs under block
    resampling, so replicate means vary MORE than under iid resampling.
    That extra variance is the point."""
    series = [-100.0] * 50 + [100.0] * 50
    rng = random.Random(11)
    block_means = [stats.resample_mean(series, rng) for _ in range(400)]
    rng2 = random.Random(11)
    iid = [sum(rng2.choice(series) for _ in range(100)) / 100 for _ in range(400)]

    def spread(xs: list[float]) -> float:
        m = sum(xs) / len(xs)
        return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5

    assert spread(block_means) > spread(iid)


def test_empty_arm_rejected() -> None:
    with pytest.raises(ValueError):
        stats.compare([], [1.0, 2.0])


def test_describe_carries_the_units_it_was_given() -> None:
    c = stats.compare(_B, _C, resamples=200, unit="$", per="trade")
    assert "$" in c.describe() and "/trade" in c.describe()
    d = stats.compare(_B, _C, resamples=200)
    assert "$" not in d.describe() and "/obs" in d.describe()


# ---- CAPACITY vs EDGE --------------------------------------------------------

def _cmp(ci_low: float, ci_high: float) -> stats.Comparison:
    return stats.Comparison(n_baseline=50, n_candidate=50, baseline_mean=0.0,
                            candidate_mean=0.0, diff=0.0, ci_low=ci_low,
                            ci_high=ci_high, alpha=0.01, n_comparisons=5, resamples=2000)


def test_edge_needs_the_interval_to_exclude_zero_in_its_favour() -> None:
    assert _cmp(1.0, 5.0).significant is True
    assert _cmp(-1.0, 5.0).significant is False
    assert _cmp(-5.0, -1.0).significant is False


def test_capacity_only_needs_to_rule_out_being_worse() -> None:
    inconclusive = _cmp(-1.0, 5.0)
    assert inconclusive.significant is False and inconclusive.not_worse is True


def test_capacity_fails_when_the_candidate_is_significantly_worse() -> None:
    worse = _cmp(-5.0, -1.0)
    assert worse.not_worse is False and worse.verdict == "SIGNIFICANTLY WORSE"


def test_capacity_is_strictly_weaker_than_edge_never_stronger() -> None:
    for lo, hi in [(1.0, 5.0), (0.01, 0.02), (-1.0, 5.0), (-5.0, -1.0), (0.0, 0.0)]:
        c = _cmp(lo, hi)
        if c.significant:
            assert c.not_worse, f"edge passed but capacity failed at CI[{lo},{hi}]"


def test_a_zero_width_interval_at_zero_passes_neither() -> None:
    c = _cmp(0.0, 0.0)
    assert c.significant is False and c.not_worse is False


# ---- one-sample bootstrap and concentration ---------------------------------

def test_bootstrap_mean_ci_brackets_the_mean_and_is_deterministic() -> None:
    xs = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
    lo, hi, share = stats.bootstrap_mean_ci(xs, alpha=0.05, resamples=500, seed=1)
    assert lo <= 3.0 <= hi and share == 1.0
    assert stats.bootstrap_mean_ci(xs, alpha=0.05, resamples=500, seed=1) == (lo, hi, share)


def test_bootstrap_mean_ci_narrows_with_larger_alpha() -> None:
    xs = [(-1) ** i * (i % 7) for i in range(80)]
    lo5, hi5, _ = stats.bootstrap_mean_ci(xs, alpha=0.05, resamples=800, seed=3)
    lo20, hi20, _ = stats.bootstrap_mean_ci(xs, alpha=0.20, resamples=800, seed=3)
    assert hi20 - lo20 <= hi5 - lo5


def test_bootstrap_mean_ci_refuses_an_empty_series() -> None:
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci([])


def test_concentration_of_one_dominant_winner() -> None:
    c = stats.concentration([100.0, 1.0, 1.0, 1.0, -2.0])
    assert c.top1_pct == pytest.approx(100 / 103 * 100)
    assert c.topn_pct == pytest.approx(102 / 103 * 100)
    assert c.pf_ex_topn == pytest.approx(0.5) and c.median == 1.0


def test_concentration_with_no_winners_is_zero_not_an_error() -> None:
    c = stats.concentration([-1.0, -2.0, -3.0])
    assert (c.top1_pct, c.topn_pct, c.pf_ex_topn, c.median) == (0.0, 0.0, 0.0, -2.0)
    assert stats.concentration([]).median == 0.0


def test_pf_ex_topn_is_infinite_when_nothing_remains_to_lose() -> None:
    assert stats.concentration([5.0, 4.0, 3.0, 2.0]).pf_ex_topn == float("inf")
    assert stats.concentration([5.0, 4.0, 3.0, 2.0, -1.0], n=1).pf_ex_topn == 9.0


def test_describe_reports_the_sample_size_of_each_arm() -> None:
    """Dropped in the first extraction and restored in 0.1.3. A verdict
    without its n is not readable evidence."""
    c = stats.compare(_B, _C, resamples=200)
    assert f"(n={len(_C)})" in c.describe() and f"(n={len(_B)})" in c.describe()
