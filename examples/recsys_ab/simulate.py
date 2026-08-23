"""A synthetic recommender A/B test. No market data, no network, no clock.

Every arm draws engagement from the SAME distribution: the treatments are
null by construction. That is the point — the example shows what the
protocol says when there is nothing to find, which is what it said 66 times
in the log this package was extracted from.

Users belong to cohorts, and a cohort carries a shared offset. Engagement
is therefore clustered, not independent, which is why the comparison uses a
moving-block bootstrap: treating 4,000 correlated users as 4,000
independent observations would report a confident answer to a question the
data cannot settle.
"""
from __future__ import annotations

from preregister.nulls import stable_normal, stable_uniform

ARMS = ("control", "A", "B")
N_USERS = 4_000
N_COHORTS = 40


def users(n: int = N_USERS) -> list[str]:
    return [f"u{i:05d}" for i in range(n)]


def cohort(user_id: str) -> str:
    return f"c{int(user_id[1:]) % N_COHORTS:02d}"


def assign(user_id: str, salt: str) -> str:
    """Deterministic, order-independent assignment. Re-running the analysis
    cannot reshuffle who was in which arm."""
    return ARMS[int(stable_uniform(user_id, salt=salt) * len(ARMS))]


def engagement(user_id: str, arm: str, salt: str) -> float:
    """Minutes of engagement. The arm is NOT an input to the mean — only to
    the noise term, so the arms differ in draw and not in distribution."""
    shared = stable_normal(0.0, 2.0, f"cohort|{cohort(user_id)}|{salt}")
    idio = stable_normal(0.0, 1.0, f"user|{user_id}|{arm}|{salt}")
    return 12.0 + shared + idio


def observations(salt: str, n: int = N_USERS) -> dict[str, list[float]]:
    """{arm: [engagement, ...]} for one assignment salt."""
    out: dict[str, list[float]] = {a: [] for a in ARMS}
    for uid in users(n):
        arm = assign(uid, salt)
        out[arm].append(engagement(uid, arm, salt))
    return out


def relabelled(salt: str, relabel_salt: str, n: int = N_USERS) -> dict[str, list[float]]:
    """The negative control: the SAME engagement numbers as the experiment,
    re-assigned to arms under `relabel_salt`. Any 'effect' this finds is an
    artefact of the pipeline, because no treatment was applied to anything.

    NOTE, and it is the whole point of having written this twice: the first
    version generated engagement under `relabel_salt` too, and over a smaller
    slice of users. That moved the cohort offsets, which moved the mean, and
    the control came back SIGNIFICANT — an "effect" entirely manufactured by
    the control's own construction. A control must change the LABELS and
    nothing else. `engagement` here is keyed on the experiment's `salt`, and
    the arm label passed to it is fixed, so relabelling cannot touch a value.
    """
    base = {uid: engagement(uid, "control", salt) for uid in users(n)}
    out: dict[str, list[float]] = {a: [] for a in ARMS}
    for uid, value in base.items():
        out[assign(uid, f"relabel|{relabel_salt}")].append(value)
    return out
