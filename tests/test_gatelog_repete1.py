"""The source bot's real log, vendored verbatim, is the first worked example.

The bar is ZERO errors. Warnings and info are pinned in a findings file so
they can only be removed by fixing the linter's understanding — never by
editing the log, which is append-only and says so in its own preamble.
"""
import json
import os
import subprocess
import sys

from preregister.budget import Registry
from preregister.gatelog import AppendOnlyLock, final_k, lint, parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "examples")
LOG = os.path.join(EX, "repete1_gate_log.md")
LOCK = os.path.join(EX, "repete1_gate_log.lock.json")
FINDINGS = os.path.join(EX, "repete1_gate_log.findings.json")
VERDICTS = os.path.join(EX, "repete1_gate_verdicts.json")


def _text() -> str:
    with open(LOG, encoding="utf-8") as f:
        return f.read()


def test_the_log_lints_with_zero_errors_and_its_lock_is_intact() -> None:
    reg = Registry.load(VERDICTS)
    fs = lint(_text(), lock=AppendOnlyLock.load(LOCK), registry_adopted=reg.strategies_adopted)
    errors = [f for f in fs if f.level == "error"]
    assert errors == [], errors


def test_final_k_agrees_with_the_registry_and_is_66() -> None:
    """What the bot's own `test_gate_verdicts.py` asserts, through this package."""
    assert final_k(parse(_text())) == Registry.load(VERDICTS).k() == 66


def test_findings_match_the_pinned_file() -> None:
    """A ratchet. To change it, re-run the CLI and commit the diff WITH the
    reason; the diff is the review."""
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
    r = subprocess.run([sys.executable, "-m", "preregister.gatelog", LOG, "--lock", LOCK,
                        "--registry", VERDICTS, "--json"], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout[-2000:]
    with open(FINDINGS, encoding="utf-8") as f:
        assert json.loads(r.stdout) == json.load(f)


def test_the_predicted_findings_are_present() -> None:
    """The extraction map predicted these before the linter existed."""
    with open(FINDINGS, encoding="utf-8") as f:
        fs = json.load(f)["findings"]
    by = {(x["rule"], x["section"]) for x in fs}
    assert ("R02", "§23") in by, "the §22 gap"
    assert ("R04", "§54") in by, "ENABLEMENT is not a class"
    assert ("R13", "§58") in by, "§58's self-reported deviation"
    assert sum(1 for x in fs if x["rule"] == "R08") >= 5, "tallies the consumer regex cannot read"
    assert ("R06", "§4") in by, "§4-§10 spent trials with no K statement"


def test_the_parser_sees_every_section() -> None:
    log = parse(_text())
    assert [s.number for s in log.sections] == [n for n in range(1, 59) if n != 22]
    assert log.sections[-1].classes[0] == "CONTROL"
    assert "EXPERIMENT" in next(s for s in log.sections if s.number == 51).classes
