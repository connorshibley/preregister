"""Deterministic gate clauses: dict in, `(ok, reasons)` out.

A clause never returns a bare boolean. The source bot's gate ran six clauses
and a strategy cleared every one of them on a single +939% trade worth 118%
of the net result; the reasons list is how that was noticed, and
`concentration_clause` is how it was closed.

What does NOT ship here: any threshold. "15 trades", "profit factor 1.3",
"half the net result" are the consumer's pre-registered numbers and belong
in its gate log, where a linter can hold them to account. This module gives
the shapes — `floor`, `ceiling`, `all_of`, `both_arms` — and the two
metrics that are arithmetic rather than policy.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

Summary = Mapping[str, Any]
Clause = Callable[[Summary], tuple[bool, list[str]]]


def floor(key: str, minimum: float, *, label: str = "", fmt: str = "{:.2f}",
          strict: bool = False) -> Clause:
    """`summary[key] >= minimum` (or `>` when strict). A missing key FAILS —
    a clause that cannot read its input must not pass by accident."""
    name = label or key

    def clause(s: Summary) -> tuple[bool, list[str]]:
        if key not in s:
            return False, [f"{name}: missing from summary"]
        v = float(s[key])
        ok = v > minimum if strict else v >= minimum
        if ok:
            return True, []
        op = ">" if strict else ">="
        return False, [f"{name} {fmt.format(v)} not {op} {fmt.format(minimum)}"]
    return clause


def ceiling(key: str, maximum: float, *, label: str = "", fmt: str = "{:.2f}",
            strict: bool = False) -> Clause:
    name = label or key

    def clause(s: Summary) -> tuple[bool, list[str]]:
        if key not in s:
            return False, [f"{name}: missing from summary"]
        v = float(s[key])
        ok = v < maximum if strict else v <= maximum
        if ok:
            return True, []
        op = "<" if strict else "<="
        return False, [f"{name} {fmt.format(v)} not {op} {fmt.format(maximum)}"]
    return clause


def all_of(*clauses: Clause) -> Clause:
    """Every clause must pass; every failure is reported, not just the first."""
    def clause(s: Summary) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        for c in clauses:
            _ok, why = c(s)
            reasons.extend(why)
        return (not reasons), reasons
    return clause


def any_of(*clauses: Clause, label: str = "no alternative cleared") -> Clause:
    """At least one must pass (the bot's 'beats benchmark OR risk-adjusted OR
    exposure-matched' escape hatch). On failure every branch's reason is
    listed under one heading, so the reader sees what was tried."""
    def clause(s: Summary) -> tuple[bool, list[str]]:
        whys: list[str] = []
        for c in clauses:
            ok, why = c(s)
            if ok:
                return True, []
            whys.extend(why)
        return False, [f"{label}: " + "; ".join(whys)]
    return clause


def both_arms(clause: Clause, base: Summary, stressed: Summary,
              labels: tuple[str, str] = ("base", "stressed")) -> tuple[bool, list[str]]:
    """The mandatory second arm. A result that passes at base cost and fails
    under stress has not "nearly passed" — it has said its edge is smaller
    than the uncertainty in the cost model. Both must pass; reasons are
    tagged by arm so the reader sees which one spoke."""
    ok_a, why_a = clause(base)
    ok_b, why_b = clause(stressed)
    reasons = [f"[{labels[0]}] {r}" for r in why_a] + [f"[{labels[1]}] {r}" for r in why_b]
    return (ok_a and ok_b), reasons


def single_share(values: Sequence[float]) -> float:
    """Largest single observation as a share of the NET total. 0.0 when the
    total is not positive — concentration of a loss is a different question.
    The caller decides which observations count (the bot excludes open
    trades); this takes the list it is given."""
    total = sum(values)
    if not values or total <= 0:
        return 0.0
    return max(values) / total


def concentration_clause(values: Sequence[float], max_share: float) -> tuple[bool, list[str]]:
    """Is this result one lottery ticket wearing a strategy's name?

    A mean-based control does not catch this: the same outlier that fools
    the gate fools the mean. `max_share` has no default because the bot's
    0.5 was chosen AFTER seeing 1.185, and says so in its log."""
    share = single_share(values)
    if share > max_share:
        return False, [
            f"concentration: the best observation is {share * 100:.1f}% of the "
            f"net result (limit {max_share * 100:.0f}%) — this is one outlier, "
            f"not a result"]
    return True, []


def max_drawdown(curve: Sequence[float]) -> float:
    """Largest peak-to-trough decline, as a positive percentage."""
    peak, worst = float("-inf"), 0.0
    for v in curve:
        peak = max(peak, v)
        if peak > 0:
            worst = max(worst, (peak - v) / peak * 100)
    return worst


def profit_factor(values: Sequence[float]) -> float:
    """Gross gains / gross losses. inf when there are gains and no losses."""
    wins = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return wins / losses
