"""Block-bootstrap comparison of two arms, corrected for the trial count.

Lifted from the source bot's `significance.py`, where it replaced an
instruction to "prefer a clear margin" — a judgement call, which is exactly
the kind of thing that bends toward whatever result you were hoping for.
This module makes it arithmetic.

Two claim types, two properties:

  * EDGE      — `Comparison.significant`: the Bonferroni-corrected CI on the
                difference in means excludes zero from below.
  * CAPACITY  — `Comparison.not_worse`: the CI's upper bound is above zero,
                i.e. the candidate is not demonstrably worse per observation.
                The deterministic clauses carry a CAPACITY decision; this
                property only refuses it.

`n_comparisons` is K. Pass an int, or anything with a `.k()` method — the
`budget.Registry` is the intended source, so K is read from the record
rather than copied into each script by hand.

Limits, stated rather than implied: the two arms are resampled
independently even when they share the same underlying series, which makes
the CI wider than a paired design would — conservative in the direction
that matters. A moving-block bootstrap preserves short-range clustering;
it cannot see regime changes longer than the block.
"""
from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

ALPHA = 0.05
DEFAULT_RESAMPLES = 5000
DEFAULT_SEED = 20260723


@runtime_checkable
class KSource(Protocol):
    """Anything that can say what K is. `budget.Registry` is one."""

    def k(self) -> int: ...


def resolve_k(n_comparisons: int | KSource) -> int:
    k = n_comparisons.k() if isinstance(n_comparisons, KSource) else int(n_comparisons)
    return max(1, k)


@dataclass(frozen=True)
class Comparison:
    n_baseline: int
    n_candidate: int
    baseline_mean: float
    candidate_mean: float
    diff: float
    ci_low: float
    ci_high: float
    alpha: float            # AFTER Bonferroni division
    n_comparisons: int
    resamples: int
    unit: str = ""          # e.g. "$"; prefixed to numbers in describe()
    per: str = "obs"        # e.g. "trade"; the thing each observation is

    @property
    def significant(self) -> bool:
        """The EDGE test: the corrected interval excludes zero from below."""
        return self.ci_low > 0

    @property
    def not_worse(self) -> bool:
        """The CAPACITY test: the candidate is not demonstrably worse."""
        return self.ci_high > 0

    @property
    def verdict(self) -> str:
        if self.significant:
            return "SIGNIFICANT"
        if self.ci_high < 0:
            return "SIGNIFICANTLY WORSE"
        return "INCONCLUSIVE"

    def describe(self) -> str:
        pct = (1 - self.alpha) * 100
        u = self.unit
        # The sample sizes are not decoration: "INCONCLUSIVE" over n=12 and
        # over n=1200 are different statements, and a reader who cannot see
        # which one this is cannot weigh it.
        return (f"{self.verdict}: candidate {u}{self.candidate_mean:+.2f}/{self.per} "
                f"(n={self.n_candidate}) vs baseline {u}{self.baseline_mean:+.2f}/{self.per} "
                f"(n={self.n_baseline}); diff {u}{self.diff:+.2f}, "
                f"{pct:.2f}% CI [{u}{self.ci_low:+.2f}, {u}{self.ci_high:+.2f}] "
                f"(Bonferroni K={self.n_comparisons})")


def block_length(n: int) -> int:
    """~sqrt(n), the standard rule of thumb; at least 1, at most n."""
    return max(1, min(n, int(round(math.sqrt(n)))))


def resample_mean(values: Sequence[float], rng: random.Random) -> float:
    """One moving-block bootstrap replicate of the mean."""
    n = len(values)
    b = block_length(n)
    out: list[float] = []
    while len(out) < n:
        start = rng.randrange(n)
        # Wrap around, so every observation has equal chance of appearing —
        # otherwise the tails of the series are systematically under-sampled.
        out.extend(values[(start + i) % n] for i in range(b))
    return sum(out[:n]) / n


def bootstrap_mean_ci(values: Sequence[float], *, alpha: float = ALPHA,
                      resamples: int = DEFAULT_RESAMPLES,
                      seed: int = DEFAULT_SEED) -> tuple[float, float, float]:
    """One-sample CI on the mean: `(lo, hi, share_of_replicates_above_zero)`.

    `alpha` is taken AS GIVEN — divide by K first (`compare()` does)."""
    if not values:
        raise ValueError("need at least one observation")
    rng = random.Random(seed)
    means = sorted(resample_mean(values, rng) for _ in range(resamples))
    lo = means[int(math.floor(alpha / 2 * resamples))]
    hi = means[min(int(math.ceil((1 - alpha / 2) * resamples)) - 1, resamples - 1)]
    return lo, hi, sum(1 for m in means if m > 0) / len(means)


def compare(baseline: Sequence[float], candidate: Sequence[float], *,
            n_comparisons: int | KSource = 1, resamples: int = DEFAULT_RESAMPLES,
            seed: int = DEFAULT_SEED, alpha: float = ALPHA,
            unit: str = "", per: str = "obs") -> Comparison:
    """Bootstrap CI on (candidate - baseline) mean per observation.

    The seed is fixed so a re-run reproduces the verdict; a verdict that
    changes when the script is run twice is not a verdict.
    """
    if not baseline or not candidate:
        raise ValueError("both arms need at least one observation")
    k = resolve_k(n_comparisons)
    corrected = alpha / k

    rng = random.Random(seed)
    diffs = sorted(resample_mean(candidate, rng) - resample_mean(baseline, rng)
                   for _ in range(resamples))

    lo_i = int(math.floor((corrected / 2) * resamples))
    hi_i = int(math.ceil((1 - corrected / 2) * resamples)) - 1
    hi_i = min(hi_i, resamples - 1)

    b_mean = sum(baseline) / len(baseline)
    c_mean = sum(candidate) / len(candidate)
    return Comparison(
        n_baseline=len(baseline), n_candidate=len(candidate),
        baseline_mean=b_mean, candidate_mean=c_mean, diff=c_mean - b_mean,
        ci_low=diffs[lo_i], ci_high=diffs[hi_i],
        alpha=corrected, n_comparisons=k, resamples=resamples,
        unit=unit, per=per)


@dataclass(frozen=True)
class Concentration:
    """How much of a result is a few observations wearing a trench coat."""
    top1_pct: float        # share of gross gain held by the single best
    topn_pct: float        # share held by the best `n`
    pf_ex_topn: float      # profit factor with the best `n` removed
    median: float
    n: int


def concentration(values: Sequence[float], n: int = 3) -> Concentration:
    ranked = sorted(values, reverse=True)
    gross_win = sum(v for v in ranked if v > 0)
    median = ranked[len(ranked) // 2] if ranked else 0.0
    if not gross_win:
        return Concentration(0.0, 0.0, 0.0, median, n)
    rest = ranked[n:]
    win = sum(v for v in rest if v > 0)
    loss = -sum(v for v in rest if v < 0)
    return Concentration(
        top1_pct=ranked[0] / gross_win * 100,
        topn_pct=sum(ranked[:n]) / gross_win * 100,
        pf_ex_topn=(win / loss) if loss else float("inf"),
        median=median, n=n)
