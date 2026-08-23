"""Every rule fires on a fixture built to violate it and stays quiet on one
built to satisfy it. A meta-test fails if a rule is registered without
both — a linter rule that cannot fire is a comment."""
import textwrap

import pytest

from preregister.gatelog import (RULES, AppendOnlyLock, Finding, fails, final_k,
                                 lint, parse)

GOOD_B = textwrap.dedent("""\
    # Log

    Trial count restarts at zero here.

    ## §1 — EDGE: two arms, committed first

    **Claim class: EDGE. K: 0 → 2. Committed BEFORE the assignment salt is drawn.**

    ### Falsification criteria, declared before the numbers
    1. CI excludes zero.

    ### §1 RESULT — INCONCLUSIVE
    **2 trials, zero adopted.**

    ## §2 — CONTROL: a null ladder

    **Claim class: CONTROL. K unchanged: 2.** Null arms are instruments.

    **2 trials, zero adopted.** A control spends no budget.

    ## §3 — EXPERIMENT: forward test with kill criteria

    **Claim class: EXPERIMENT. K unchanged: 2.**
    Kill criteria: K1 performance, K2 data.
    **2 trials, zero adopted.**
    """)


def _levels(text: str, rule: str, **kw: object) -> list[str]:
    return [f.level for f in lint(text, **kw) if f.rule == rule]  # type: ignore[arg-type]


def test_a_well_formed_era_b_log_has_no_errors_or_warnings_except_the_lock() -> None:
    fs = lint(GOOD_B)
    assert [f.rule for f in fs if f.level != "info"] == ["R12"]
    lock = AppendOnlyLock.freeze(GOOD_B)
    assert not fails(lint(GOOD_B, lock=lock), strict=True)
    assert final_k(parse(GOOD_B)) == 2


# ---- one firing fixture per rule -------------------------------------------------

FIRES: dict[str, str] = {
    "R01": GOOD_B + "\n## §4 this heading has no em dash\n",
    "R02": GOOD_B + "\n## §2 — CONTROL: numbered backwards\n\n**Claim class: CONTROL. K unchanged: 2.**\n",
    "R03": GOOD_B + "\n## §4 — a section with no class anywhere\n\ntext\n",
    "R04": GOOD_B + "\n## §4 — ENABLEMENT: not a class\n\ntext\n",
    "R05": GOOD_B + "\n## §4 — EDGE: wrong arithmetic\n\n**Claim class: EDGE. K: 5 → 6. Committed BEFORE x.**\n",
    "R06": GOOD_B + "\n## §4 — CONTROL: a control that spends\n\n**Claim class: CONTROL. K: 2 → 3.**\n",
    "R07": GOOD_B + "\n## §4 — CONTROL: tally drift\n\n**Claim class: CONTROL. K unchanged: 2.**\n**9 trials, zero adopted.**\n",
    "R08": GOOD_B + "\n## §4 — CONTROL: loose tally\n\n**Claim class: CONTROL. K unchanged: 2.**\n2 registered trials. Zero adopted.\n",
    "R09": GOOD_B + "\n## §4 — EDGE: never committed\n\n**Claim class: EDGE. K: 2 → 3.**\n### §4 RESULT — FAIL\n",
    "R10": GOOD_B + "\n## §4 — EXPERIMENT: no stop rule\n\n**Claim class: EXPERIMENT. K unchanged: 2.**\n",
    "R11": GOOD_B + "\n## §4 — EDGE: registered, never run\n\n**Claim class: EDGE. K: 2 → 3. Committed BEFORE x.**\n",
    "R12": GOOD_B,
    "R13": GOOD_B + "\n## §4 — CONTROL: honest\n\n**Claim class: CONTROL. K unchanged: 2.** There is one deviation to disclose.\n",
    "R14": GOOD_B,
}
EXTRA_KW: dict[str, dict[str, object]] = {"R14": {"registry_adopted": 1}}


@pytest.mark.parametrize("rule", sorted(RULES))
def test_every_rule_fires_on_its_fixture(rule: str) -> None:
    assert rule in FIRES, f"{rule} has no firing fixture — a rule that cannot fire is a comment"
    assert _levels(FIRES[rule], rule, **EXTRA_KW.get(rule, {})), f"{rule} did not fire"


@pytest.mark.parametrize("rule", sorted(RULES))
def test_every_rule_is_quiet_on_the_good_log(rule: str) -> None:
    lock = AppendOnlyLock.freeze(GOOD_B)
    quiet = [f for f in lint(GOOD_B, lock=lock, registry_adopted=0) if f.rule == rule]
    assert quiet == [], f"{rule} fired on a well-formed log: {quiet}"


def test_every_registered_rule_has_both_fixtures() -> None:
    assert set(FIRES) == set(RULES)


# ---- specific semantics ------------------------------------------------------------

def test_r12_catches_an_edit_above_the_last_heading() -> None:
    lock = AppendOnlyLock.freeze(GOOD_B)
    edited = GOOD_B.replace("Null arms are instruments.", "Null arms are candidates.")
    assert _levels(edited, "R12", lock=lock) == ["error"]
    appended = GOOD_B + "\n### §3 addendum — more\n\ntext\n"
    assert _levels(appended, "R12", lock=lock) == []


def test_r12_catches_truncation() -> None:
    lock = AppendOnlyLock.freeze(GOOD_B)
    assert _levels(GOOD_B[:200], "R12", lock=lock) == ["error"]


def test_r07_accepts_a_tally_stated_before_the_spend() -> None:
    """The bot's §37 declares +1 → 64 at registration, tallies 63 there, and
    64 in its RESULT: a tally may equal K before OR after its section."""
    text = GOOD_B + textwrap.dedent("""
        ## §4 — EDGE: pre-registered

        **Claim class: EDGE. K: 2 → 3. Committed BEFORE x.**
        **2 trials, zero adopted.** K becomes 3 when the gate runs.

        ## §4 RESULT — FAIL
        **3 trials, zero adopted.**
        """)
    assert _levels(text, "R07") == []


def test_strict_promotes_era_a_warnings_to_errors() -> None:
    era_a = "## §1 — a title\n\n**Type: EDGE claim.** pre-registered in a script.\n"
    assert _levels(era_a, "R06") == ["warning"]
    assert _levels(era_a, "R06", strict=True) == ["error"]


def test_absolute_k_resynchronises_in_era_a_as_info_and_errors_in_era_b() -> None:
    era_a = "## §1 — something\n\n**Type: EDGE claim.** pre-registered. Cumulative K: 5.\n"
    assert _levels(era_a, "R05") == ["info"]
    era_b = "## §1 — EDGE: something\n\n**Claim class: EDGE.** Committed BEFORE x. Cumulative K: 5.\n"
    assert _levels(era_b, "R05") == ["error"]


def test_k_never_decreases() -> None:
    text = GOOD_B + "\n## §4 — CONTROL: rewinds\n\n**Claim class: CONTROL.** Cumulative K: 1.\n"
    assert "error" in _levels(text, "R05")


def test_findings_are_sorted_deterministic_and_serialisable() -> None:
    a, b = lint(FIRES["R05"]), lint(FIRES["R05"])
    assert a == b == sorted(a)
    assert all(isinstance(f, Finding) and set(f.to_dict()) == {"line", "rule", "level", "section", "message"}
               for f in a)


def test_class_normalisation_examples() -> None:
    from preregister.gatelog.grammar import normalise_classes as n
    assert n("MEASUREMENT, not a gate") == ["MEASUREMENT"]
    assert n("GATE (re-run of §4 against a corrected input) + EDGE claim") == ["GATE", "EDGE"]
    assert n("INFRA CLOSE-OUT") == ["INFRA"]
    assert n("EDGE claim, declared before the run") == ["EDGE"]
    assert n("ENABLEMENT") == ["ENABLEMENT"]
    assert n("INFRA + METHOD") == ["INFRA", "METHOD"]


def test_cli_exit_codes(tmp_path: "pytest.TempPathFactory") -> None:
    import os
    import subprocess
    import sys
    p = os.path.join(str(tmp_path), "log.md")
    lockp = os.path.join(str(tmp_path), "lock.json")
    with open(p, "w") as f:
        f.write(GOOD_B)
    env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-m", "preregister.gatelog", p, *args],
                              capture_output=True, text=True, env=env)

    assert run("--lock", lockp, "--freeze").returncode == 0
    assert run("--lock", lockp, "--strict").returncode == 0
    assert run("--strict").returncode == 1, "no lock is a warning, and strict fails on warnings"
    with open(p, "a") as f:
        f.write("\n## §4 — CONTROL: spends\n\n**Claim class: CONTROL. K: 2 → 9.**\n")
    r = run("--lock", lockp, "--json")
    assert r.returncode == 1 and '"rule": "R06"' in r.stdout
