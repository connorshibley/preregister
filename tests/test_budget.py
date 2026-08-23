import json
import os
from pathlib import Path

import pytest

from preregister import stats
from preregister.budget import BudgetError, Registry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDORED = os.path.join(ROOT, "examples", "repete1_gate_verdicts.json")


def test_spending_classes_raise_k_by_the_arm_count() -> None:
    r = Registry()
    e = r.spend("§1", 3, committed_before="commit abc")
    assert (e.k_before, e.k_after, r.k()) == (0, 3, 3)
    r.spend("§2", 1, cls="capacity", committed_before="snapshot sha")
    assert r.k() == 4 and r.alpha() == 0.05 / 4


def test_controls_spend_nothing() -> None:
    r = Registry(trials_registered=66)
    for cls in ("CONTROL", "INFRA", "GOVERNANCE", "METHOD", "DIAGNOSTIC"):
        r.control("§58", cls=cls)
    assert r.k() == 66 and len(r.ledger) == 5


@pytest.mark.parametrize("kw", [
    dict(n_arms=0, committed_before="x"),
    dict(n_arms=1, committed_before="   "),
    dict(n_arms=1, cls="CONTROL", committed_before="x"),
])
def test_spend_refuses_what_the_log_refuses(kw: dict[str, object]) -> None:
    with pytest.raises(BudgetError):
        Registry().spend("§9", **kw)  # type: ignore[arg-type]


def test_control_refuses_a_spending_or_unknown_class() -> None:
    with pytest.raises(BudgetError):
        Registry().control("§1", cls="EDGE")
    with pytest.raises(BudgetError):
        Registry().control("§1", cls="ENABLEMENT")


def test_adoption_is_counted_separately_from_k() -> None:
    r = Registry(trials_registered=5)
    r.adopt("§5", "meanrev")
    assert (r.k(), r.strategies_adopted) == (5, 1)


def test_compare_reads_k_from_the_registry() -> None:
    r = Registry(trials_registered=66)
    c = stats.compare([1.0, 2.0, 3.0, 4.0], [2.0, 3.0, 4.0, 5.0], n_comparisons=r, resamples=200)
    assert c.n_comparisons == 66 and c.alpha == 0.05 / 66


def test_the_source_repos_verdicts_file_loads_unchanged_and_round_trips(tmp_path: Path) -> None:
    r = Registry.load(VENDORED)
    assert r.k() == 66 and r.strategies_adopted == 0 and r.ledger == []
    assert "verdicts" in r.extra and "_comment" in r.extra
    r.save(tmp_path / "out.json")
    back = json.loads((tmp_path / "out.json").read_text())
    original = json.loads(Path(VENDORED).read_text())
    for key in original:
        assert back[key] == original[key], key
    assert back["schema"] == "preregister.registry/1" and back["ledger"] == []


def test_a_ledger_that_disagrees_with_the_total_is_refused() -> None:
    with pytest.raises(BudgetError):
        Registry.from_dict({"trials_registered": 5, "ledger": [
            {"section": "§1", "cls": "EDGE", "arms": 3, "k_before": 0, "k_after": 3}]})


def test_save_load_round_trip_keeps_the_ledger(tmp_path: Path) -> None:
    r = Registry(updated="2026-08-22")
    r.spend("§1", 2, committed_before="sha 111")
    r.control("§2")
    r.save(tmp_path / "r.json")
    back = Registry.load(tmp_path / "r.json")
    assert back == r
