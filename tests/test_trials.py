import json
from pathlib import Path

from preregister import trials


def test_every_variant_is_logged_and_oos_is_run_once(tmp_path: Path) -> None:
    """Ported from the bot's `test_walk_forward_logs_every_variant`."""
    log = trials.TrialLog(tmp_path / "t.jsonl")
    calls = {"validate": 0}

    def fit(p: int) -> dict[str, float]:
        return {"score": float(p % 3)}

    def validate(p: int) -> dict[str, float]:
        calls["validate"] += 1
        return {"score": -1.0}

    wf = trials.walk_forward([1, 2, 3, 4, 5], fit, validate, lambda r: r["score"], log)
    rows = log.read()
    assert [r["phase"] for r in rows] == ["in_sample"] * 5 + ["oos"]
    assert wf.best == 2 and wf.n_variants == 5 and calls["validate"] == 1
    assert wf.oos_result == {"score": -1.0}
    assert all("logged_at" in r for r in rows)


def test_log_is_append_only_and_tolerates_a_missing_file(tmp_path: Path) -> None:
    log = trials.TrialLog(tmp_path / "sub" / "t.jsonl")
    assert log.read() == []
    log.append({"a": 1}, phase="x")
    log.append({"a": 2}, phase="x")
    assert [r["a"] for r in log.read()] == [1, 2]
    assert len((tmp_path / "sub" / "t.jsonl").read_text().splitlines()) == 2


def test_unserialisable_params_are_recorded_by_repr_not_dropped(tmp_path: Path) -> None:
    log = trials.TrialLog(tmp_path / "t.jsonl")
    log.append({"params": trials._jsonable_params(object)}, phase="p")
    assert "object" in json.dumps(log.read())
