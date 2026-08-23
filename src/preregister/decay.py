"""Is a live track record distinguishable from random entries?

The bot ran this nightly against every enabled strategy: synthesise
`n_samples` track records of random entries with the strategy's own holding
periods and costs, and ask where the real mean lands in that distribution.
Here the "one synthetic observation" step is an injected `draw` — the
package does not know what an observation is.

Deliberate leniency, inherited and stated: a null built without the
strategy's exits is biased toward the strategy. A verdict of WORSE_THAN_RANDOM
under a lenient null is therefore strong.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

VERDICTS = ("INSUFFICIENT_DATA", "WORSE_THAN_RANDOM",
            "INDISTINGUISHABLE_FROM_RANDOM", "BEATS_RANDOM")

#: One synthetic observation, or None meaning "this draw was unusable, draw
#: again" — never wrap, never substitute.
Draw = Callable[[random.Random], float | None]


@dataclass(frozen=True)
class Verdict:
    name: str
    n: int
    percentile: float | None
    actual_mean: float | None
    verdict: str
    n_samples: int
    seed: int
    note: str = ""

    @property
    def alert(self) -> bool:
        return self.verdict == "WORSE_THAN_RANDOM"


def percentile_rank(value: float, distribution: Sequence[float]) -> float:
    """Fraction of `distribution` strictly below `value`, as 0-100. Empirical,
    not parametric."""
    if not distribution:
        return 0.0
    below = sum(1 for x in distribution if x < value)
    return below / len(distribution) * 100.0


def null_distribution(draw: Draw, n_obs: int, *, n_samples: int, seed: int,
                      max_draws_per_obs: int = 50) -> list[float]:
    """`n_samples` synthetic track-record means of `n_obs` draws each."""
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(n_samples):
        values: list[float] = []
        draws = 0
        max_draws = max(n_obs, 1) * max_draws_per_obs
        while len(values) < n_obs and draws < max_draws:
            draws += 1
            v = draw(rng)
            if v is not None:
                values.append(v)
        if values:
            means.append(sum(values) / len(values))
    return means


def band(percentile: float, *, low: float, high: float) -> str:
    if percentile < low:
        return "WORSE_THAN_RANDOM"
    if percentile >= high:
        return "BEATS_RANDOM"
    return "INDISTINGUISHABLE_FROM_RANDOM"


def verdict_for(name: str, actual: Sequence[float], draw: Draw, *, min_obs: int,
                n_samples: int, seed: int, low: float, high: float,
                note: str = "") -> Verdict:
    """`n < min_obs` short-circuits BEFORE the seed is touched: a verdict
    nobody should trust does not get to look like one that ran."""
    n = len(actual)
    if n < min_obs:
        return Verdict(name, n, None, None, "INSUFFICIENT_DATA", n_samples, seed, note)
    mean = sum(actual) / n
    dist = null_distribution(draw, n, n_samples=n_samples, seed=seed)
    pct = percentile_rank(mean, dist)
    return Verdict(name, n, pct, mean, band(pct, low=low, high=high), n_samples, seed, note)
