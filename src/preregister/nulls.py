"""Null arms that reproduce byte-for-byte, and the ladder that judges them.

Why a hash and not a seeded PRNG: a PRNG sequence depends on how many draws
came before it. Two runs that evaluate candidates in a different order — or a
live path and a simulator that evaluate a different number of them — would
disagree on every draw after the first divergence. A hash of the draw's own
identity is stable under both. The source bot had THREE copies of this idea
(`judge_model._uniform`, `ablation_arms.uniform`, `allocator._draw`); this
is the one.

`stable_uniform(a, b, salt=s)` is bit-identical to the bot's
`_uniform(a, b, s)`: the parts and the salt are joined with `|`.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from preregister.stats import KSource, compare, resolve_k


def _digest(*parts: object, salt: str) -> bytes:
    material = "|".join(str(p) for p in parts) + "|" + salt
    return hashlib.sha256(material.encode()).digest()


def stable_uniform(*parts: object, salt: str = "") -> float:
    """A draw in [0, 1) determined entirely by `parts` and `salt`."""
    return int.from_bytes(_digest(*parts, salt=salt)[:8], "big") / 2**64


def stable_normal(mean: float, sd: float, seed_material: str) -> float:
    """One Normal sample from a hash. Box-Muller on two hash-derived
    uniforms; `seed_material` is the already-joined identity string, which
    keeps this bit-identical to the source's `allocator._draw`."""
    h = hashlib.sha256(seed_material.encode()).digest()
    u1 = max(1e-12, int.from_bytes(h[:8], "big") / 2**64)
    u2 = int.from_bytes(h[8:16], "big") / 2**64
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mean + sd * z


def entry_rate(n_events: int, n_slots: int) -> float:
    """Realized events per opportunity — the rate a matched null is held to.

    A null that acts ten times more often than the treatment is a different
    experiment, not a control."""
    return (n_events / n_slots) if n_slots else 0.0


def pass_mark(verdicts: Mapping[str, bool | None], required: Sequence[str]) -> bool:
    """Every required comparison must be True. `None` (INCONCLUSIVE — an arm
    could not be measured) never rounds up to a pass. Rows not named in
    `required` are diagnostics and cannot move the verdict."""
    return all(bool(verdicts.get(r)) for r in required)


@dataclass
class Ladder:
    """The pre-registered part of an ablation ladder.

    Declare `required` (which baselines the treatment must beat) and `salts`
    (fixed, never extended after a result is seen) BEFORE running anything,
    then call `judge()` once per baseline. `passed` applies `pass_mark`.
    The arm *runner* is the domain's; this holds the verdicts.
    """
    required: tuple[str, ...]
    salts: tuple[str, ...]
    k: int | KSource
    resamples: int = 5000
    seed: int = 20260723
    verdicts: dict[str, bool | None] = field(default_factory=dict)
    described: dict[str, str] = field(default_factory=dict)

    def judge(self, label: str, baseline: Sequence[float],
              treatment: Sequence[float]) -> bool | None:
        if not baseline or not treatment:
            self.verdicts[label] = None
            self.described[label] = (f"INCONCLUSIVE — {len(treatment)} vs "
                                     f"{len(baseline)} observations")
            return None
        c = compare(baseline, treatment, n_comparisons=resolve_k(self.k),
                    resamples=self.resamples, seed=self.seed)
        self.verdicts[label] = bool(c.significant)
        self.described[label] = c.describe()
        return self.verdicts[label]

    @property
    def passed(self) -> bool:
        return pass_mark(self.verdicts, self.required)
