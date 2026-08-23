"""The toy example runs, stays null, and its log lints clean under --strict."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "examples", "recsys_ab")
ENV = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))


def test_the_example_runs_and_finds_nothing() -> None:
    r = subprocess.run([sys.executable, os.path.join(EX, "run.py")],
                       capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, r.stderr[-2000:]
    assert r.stdout.count("INCONCLUSIVE") >= 4
    assert "SIGNIFICANT:" not in r.stdout, "a null generator must not produce an effect"
    assert "RESULT   : FAIL" in r.stdout
    assert "not_worse = True" in r.stdout, "CAPACITY passes where EDGE does not"


def test_its_gate_log_lints_clean_in_strict_mode() -> None:
    r = subprocess.run([sys.executable, "-m", "preregister.gatelog",
                        os.path.join(EX, "gate_log.md"), "--strict",
                        "--lock", os.path.join(EX, "gate_log.lock.json")],
                       capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, r.stdout
    assert "0 errors, 0 warnings" in r.stdout


def test_the_declared_ledger_matches_the_logs_tally() -> None:
    sys.path.insert(0, EX)
    from preregister.gatelog import final_k, parse
    from run import build_registry  # type: ignore[import-not-found]
    with open(os.path.join(EX, "gate_log.md"), encoding="utf-8") as f:
        assert build_registry().k() == final_k(parse(f.read())) == 3


def test_the_control_changes_only_the_labels() -> None:
    """The §3 addendum, as an assertion: relabelling must not move a value."""
    sys.path.insert(0, EX)
    from simulate import ARMS, observations, relabelled  # type: ignore[import-not-found]
    a = relabelled("s", "r1", n=300)
    b = relabelled("s", "r2", n=300)
    assert sorted(v for arm in ARMS for v in a[arm]) == \
        pytest.approx(sorted(v for arm in ARMS for v in b[arm])), \
        "a different relabel salt moved the VALUES, not just the labels"
    assert [len(a[x]) for x in ARMS] != [len(b[x]) for x in ARMS] or a != b, \
        "the relabel must actually reassign"
    exp = observations("s", n=300)
    assert sorted(v for arm in ARMS for v in exp[arm]) != \
        pytest.approx(sorted(v for arm in ARMS for v in a[arm])), \
        "the control pools control-arm engagement; it is not the experiment's own draw"
