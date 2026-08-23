from pathlib import Path

from preregister.golden import Golden, jsonable


def test_inf_survives_serialisation() -> None:
    assert jsonable({"pf": float("inf"), "n": [float("-inf"), float("nan"), 1.0]}) == \
        {"pf": "inf", "n": ["-inf", "nan", 1.0]}


def test_write_then_check_is_clean_and_a_moved_number_produces_a_diff(tmp_path: Path) -> None:
    state = {"v": 1.0}
    g = Golden(tmp_path / "g.json", lambda: {"result": state["v"]}, note="toy")
    g.write()
    assert g.check() == []
    assert '"what": "toy"' in (tmp_path / "g.json").read_text()
    state["v"] = 2.0
    diff = g.check()
    assert diff and any(line.startswith("-") and "1.0" in line for line in diff)
    assert any(line.startswith("+") and "2.0" in line for line in diff)
