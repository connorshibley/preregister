"""Run the three sections of `gate_log.md` and print their verdicts.

Exits 0. Every comparison is INCONCLUSIVE and the ladder FAILs, because the
generator draws every arm from one distribution. A run that printed
SIGNIFICANT here would mean the package manufactures effects.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from preregister import stats                      # noqa: E402
from preregister.budget import Registry            # noqa: E402
from preregister.nulls import Ladder               # noqa: E402
from simulate import ARMS, observations, relabelled  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SALT = "ab-2026-01"
SALTS = ("abl-1", "abl-2", "abl-3", "abl-4", "abl-5")


def build_registry() -> Registry:
    """The ledger the log declares, rebuilt in code. §1 and §2 spend; §3 does not."""
    reg = Registry(updated="2026-01-01")
    reg.spend("§1", 2, cls="EDGE", committed_before="the assignment salt is drawn")
    reg.spend("§2", 1, cls="CAPACITY", committed_before="the wider cohort is drawn")
    reg.control("§3", cls="CONTROL", note="relabel ladder over five fixed salts")
    return reg


def main() -> int:
    reg = build_registry()
    obs = observations(SALT)
    print(f"K = {reg.k()}, alpha = {reg.alpha():.5f}, "
          f"arm sizes {[len(obs[a]) for a in ARMS]}\n")

    print("§1 EDGE — two rankers vs the incumbent")
    for arm in ("A", "B"):
        c = stats.compare(obs["control"], obs[arm], n_comparisons=reg, per="user")
        print(f"  {arm}: {c.describe()}")
        assert not c.significant, "the arms are null by construction"

    print("\n§2 CAPACITY — twice the population, not worse per user")
    wide = observations(SALT, n=8_000)
    c2 = stats.compare(obs["control"], wide["control"], n_comparisons=reg, per="user")
    print(f"  {c2.describe()}")
    print(f"  not_worse = {c2.not_worse}  (this is the CAPACITY test, not EDGE)")

    print("\n§3 CONTROL — the relabel ladder, five pre-registered salts")
    lad = Ladder(required=("relabelled null", "control arm"), salts=SALTS, k=reg)
    pooled = [v for s in SALTS for v in relabelled(SALT, s)["A"]]
    lad.judge("relabelled null", pooled, obs["A"])
    lad.judge("control arm", obs["control"], obs["A"])
    for label, text in lad.described.items():
        print(f"  vs {label:<18} {text}")
    print(f"\n  PASS MARK: beat both, CI excludes zero at K={reg.k()}")
    print(f"  RESULT   : {'PASS' if lad.passed else 'FAIL'}")
    if not lad.passed:
        print("\n  A FAIL here is the correct output: every arm was drawn from the "
              "same distribution.\n  The protocol found nothing because there is "
              "nothing to find.")

    reg.save(os.path.join(HERE, "registry.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
