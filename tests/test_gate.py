"""Ported from the bot's `test_backtest.py` (metrics, the enablement truth
table) and `test_concentration_clause.py`, on plain floats and with every
threshold supplied BY THE TEST — none ship in the package."""
import pytest

from preregister import gate

# The bot's enablement gate, re-expressed from its thresholds. This is also
# the README example; if it stops reproducing the bot's verdicts, the shapes
# here have drifted from the clauses they replace.
BH_OR_RISK_ADJUSTED = gate.any_of(
    lambda s: (s["total_return_pct"] >= s["buy_hold_return_pct"], ["return < buy-and-hold"]),
    lambda s: (s["total_return_pct"] >= 0.7 * s["buy_hold_return_pct"]
               and s["max_drawdown_pct"] <= 0.5 * s["buy_hold_max_drawdown_pct"],
               ["not risk-adjusted better"]),
    label="beats neither benchmark",
)
ENABLEMENT = gate.all_of(
    gate.floor("total_return_pct", 0.0, strict=True, label="OOS return"),
    gate.floor("n_trades", 15, fmt="{:.0f}"),
    gate.floor("profit_factor", 1.3),
    BH_OR_RISK_ADJUSTED,
)


def _oos(**over: float) -> dict[str, float]:
    base = {"total_return_pct": 12.0, "n_trades": 20, "profit_factor": 1.6,
            "buy_hold_return_pct": 8.0, "max_drawdown_pct": 5.0,
            "buy_hold_max_drawdown_pct": 20.0}
    base.update(over)
    return base


def test_a_clean_result_passes_with_no_reasons() -> None:
    assert ENABLEMENT(_oos()) == (True, [])


@pytest.mark.parametrize("over,fragment", [
    ({"total_return_pct": -1.0, "buy_hold_return_pct": -5.0}, "OOS return"),
    ({"n_trades": 14}, "n_trades 14 not >= 15"),
    ({"profit_factor": 1.29}, "profit_factor 1.29 not >= 1.30"),
    ({"total_return_pct": 3.0, "max_drawdown_pct": 15.0}, "beats neither benchmark"),
])
def test_each_clause_names_itself_on_failure(over: dict[str, float], fragment: str) -> None:
    ok, why = ENABLEMENT(_oos(**over))
    assert ok is False and any(fragment in r for r in why), why


def test_every_failure_is_reported_not_just_the_first() -> None:
    ok, why = ENABLEMENT(_oos(n_trades=3, profit_factor=0.9))
    assert ok is False and len(why) == 2


def test_risk_adjusted_escape_hatch() -> None:
    """Most of the benchmark's return at half its drawdown passes."""
    s = _oos(total_return_pct=6.0, buy_hold_return_pct=8.0, max_drawdown_pct=5.0,
             buy_hold_max_drawdown_pct=20.0)
    assert ENABLEMENT(s)[0] is True


def test_a_missing_key_fails_rather_than_passing_by_accident() -> None:
    ok, why = gate.floor("pf", 1.0)({})
    assert ok is False and "missing" in why[0]


def test_both_arms_tags_reasons_by_arm() -> None:
    clause = gate.floor("x", 1.0)
    ok, why = gate.both_arms(clause, {"x": 2.0}, {"x": 0.5}, labels=("1.0x", "1.5x"))
    assert ok is False and why == ["[1.5x] x 0.50 not >= 1.00"]
    assert gate.both_arms(clause, {"x": 2.0}, {"x": 1.0}) == (True, [])


# ---- concentration (§37 in the source) ---------------------------------------

def test_single_share_of_a_lottery_ticket() -> None:
    pnls = [939.3] + [-10.0] * 35
    assert gate.single_share(pnls) == pytest.approx(939.3 / (939.3 - 350.0))
    assert gate.single_share(pnls) > 1.0, "one trade can exceed 100% of the net"


def test_single_share_is_zero_for_a_losing_or_empty_result() -> None:
    assert gate.single_share([-1.0, -2.0]) == 0.0
    assert gate.single_share([]) == 0.0


def test_concentration_clause_fails_above_the_given_share() -> None:
    ok, why = gate.concentration_clause([939.3] + [-10.0] * 35, max_share=0.5)
    assert ok is False and "one outlier" in why[0]
    assert gate.concentration_clause([10.0] * 10, max_share=0.5) == (True, [])


def test_concentration_clause_has_no_default_threshold() -> None:
    with pytest.raises(TypeError):
        gate.concentration_clause([1.0])  # type: ignore[call-arg]


# ---- metrics ------------------------------------------------------------------

def test_max_drawdown() -> None:
    assert gate.max_drawdown([100, 120, 90, 130, 65]) == pytest.approx(50.0)
    assert gate.max_drawdown([100, 110, 120]) == 0.0
    assert gate.max_drawdown([]) == 0.0


def test_profit_factor() -> None:
    assert gate.profit_factor([10.0, -5.0, 20.0, -10.0]) == 2.0
    assert gate.profit_factor([10.0, 5.0]) == float("inf")
    assert gate.profit_factor([-1.0]) == 0.0
    assert gate.profit_factor([]) == 0.0
