# Quickstart

Ten minutes from nothing to a linted pre-registration log.

## Install

Not on PyPI yet. Install the release wheel — it is hash-pinnable, which
matters if you install under `--require-hashes`:

```bash
pip install https://github.com/connorshibley/preregister/releases/download/v0.1.3/preregister-0.1.3-py3-none-any.whl
```

Python 3.12+. No dependencies.

```bash
python -c "import preregister; print(preregister.__version__)"
```

## 1. Start a log

Copy the template:

```bash
mkdir -p knowledge
curl -sL https://raw.githubusercontent.com/connorshibley/preregister/main/templates/gate_log.md -o knowledge/gate_log.md
```

Or copy `templates/gate_log.md` from a checkout. Edit `<Project>` and write
your first section **before you run anything**.

## 2. Lint it

```bash
python -m preregister.gatelog knowledge/gate_log.md --strict
```

You will get one warning: no append-only lock. Fix that next.

## 3. Freeze the lock

The lock hashes everything above the last heading in the file. Appending a
section moves the boundary; editing history breaks the hash.

```bash
python -m preregister.gatelog knowledge/gate_log.md --lock knowledge/gate_log.lock.json --freeze
python -m preregister.gatelog knowledge/gate_log.md --lock knowledge/gate_log.lock.json --strict
```

Zero findings. That is the state to commit.

**The workflow from here: append a section, re-freeze in the same commit.**
If a diff ever shows the lock changing without a new section, someone edited
history.

## 4. Track the budget

```python
from preregister.budget import Registry

reg = Registry(updated="2026-08-23")
reg.spend("§1", 2, cls="EDGE", committed_before="the assignment salt is drawn")
reg.control("§2", cls="CONTROL")
reg.save("knowledge/registry.json")
```

Then cross-check the registry against the log — this catches a tally line
that disagrees with the count it sits under:

```bash
python -m preregister.gatelog knowledge/gate_log.md \
  --lock knowledge/gate_log.lock.json --registry knowledge/registry.json
```

## 5. Run the comparison

```python
from preregister import stats
from preregister.budget import Registry

reg = Registry.load("knowledge/registry.json")
c = stats.compare(baseline, candidate, n_comparisons=reg, per="user")

print(c.describe())
c.significant   # EDGE:     the corrected CI excludes zero
c.not_worse     # CAPACITY: it is not demonstrably worse
```

K comes from the record, not from a literal in your script. That is the whole
point of the `Registry`.

## 6. Put it in CI

```yaml
- name: The gate log adds up
  run: |
    python -m preregister.gatelog knowledge/gate_log.md \
      --lock knowledge/gate_log.lock.json \
      --registry knowledge/registry.json --strict
```

Exit code is 1 on any error, and on any warning under `--strict`.

---

## The rules the linter enforces

| Rule | Checks |
|---|---|
| R01 | Every `## §N` heading parses |
| R02 | Section numbers do not go backwards; gaps are flagged |
| R03 | Every section declares a claim class |
| R04 | The class is one the enum knows |
| R05 | K's arithmetic adds up across sections |
| R06 | Spending classes move K; non-spending classes do not |
| R07 | Every tally line agrees with the running count |
| R08 | Tallies are in the machine-readable form |
| R09 | A spending section says what it was committed **before** |
| R10 | An `EXPERIMENT` states kill criteria |
| R11 | A spending section eventually reports a result |
| R12 | History has not been edited (needs `--lock`) |
| R13 | Self-reported protocol deviations are surfaced, never suppressed |
| R14 | The tally's adopted count matches the registry |

**Levels.** `error` fails always. `warning` fails under `--strict`. `info`
never fails and is never suppressed — an info finding exists precisely so a
reader sees it.

**Use `--strict` on a new log.** The lenient mode exists for logs written
before the grammar did; see `docs/audit-protocol-verbatim.md` for what that
looks like in practice.

---

## Worked examples

- [`examples/recsys_ab/`](../examples/recsys_ab/) — a null A/B test run
  through the whole protocol. Every comparison comes back INCONCLUSIVE and
  the ladder FAILs, which is the correct output. Read its §3 addendum: the
  negative control was wrong on its first run and fired on a pipeline with no
  treatment in it.
- [`examples/repete1_gate_log.md`](../examples/repete1_gate_log.md) — a real
  log, 58 sections, 66 trials, zero adoptions. Lints with **0 errors and 25 warnings**, and the warnings are the interesting part.

## Next

- [`methodology.md`](methodology.md) — claim classes, picking K, what to do
  with an INCONCLUSIVE, and when not to use this at all.
- [`audit.md`](audit.md) — the rubric for reviewing someone *else's* claim.
