# preregister

Pre-registration, multiple-comparison budgets and null ladders — as code,
not as a checklist. Pure Python 3.12, no dependencies.

## Where it comes from

A cryptocurrency paper-trading bot ran **66 pre-registered trials** over two
months and **adopted zero** of them. Every trial declared its hypothesis, its
arms, its falsification criteria and its negative control before the data was
touched; every result was appended to a log that was never edited, only
corrected by dated addenda; every significance test was Bonferroni-corrected
against the *cumulative* trial count. The strategies had no edge. The method
said so, 66 times, and was right.

Two things in that discipline were still held together by a human:

1. **The trial count K was a hand-copied integer** across fifteen scripts,
   under three different conventions, pinned by no test.
2. **The log's own grammar** — claim class, `K: 65 → 66`, "committed before
   the run", controls spend nothing, predictions scored — was enforced
   entirely by prose.

This package is the arithmetic for both, plus the statistics and
reproducibility primitives that log relied on, with the trading removed.

## The two new pieces

**A budget ledger.** K comes from the record, not from a literal:

```python
from preregister.budget import Registry
from preregister import stats

reg = Registry.load("gate_verdicts.json")     # the bot's own file loads unchanged
reg.spend("§53", 1, cls="EDGE", committed_before="any gate code exists")
reg.control("§58", cls="CONTROL")             # a control spends nothing

c = stats.compare(baseline, candidate, n_comparisons=reg)
c.significant     # EDGE: the corrected CI excludes zero
c.not_worse       # CAPACITY: it is not demonstrably worse
```

`spend()` refuses a class that shouldn't spend, refuses zero arms, and
refuses to record a trial that doesn't say what it was committed *before*.

**A gate-log linter.** It reads a log's structure and checks what used to be
prose: that the claim class is in the enum, that K's arithmetic adds up
across every section, that each tally line agrees with the running count,
that spending sections say they were committed first, that an EXPERIMENT
states kill criteria — and, via a lock file, that nothing above the last
heading was ever edited.

```
python -m preregister.gatelog LOG.md --strict --lock LOG.lock.json
```

Run it against the bot's real log, vendored here verbatim:

```
python -m preregister.gatelog examples/repete1_gate_log.md \
  --lock examples/repete1_gate_log.lock.json \
  --registry examples/repete1_gate_verdicts.json
```

**Zero errors, 25 warnings, 8 info** — and the warnings are the interesting
part. Sixteen early sections predate the claim-class convention. Five tally
lines are in a form the bot's own consumer regex cannot read. `§54` uses a
class word (`ENABLEMENT`) that was never in the enum. `§22` was numbered and
never written. `§58` self-reports that its spec was transcribed after the
first smoke run. Every one of those was in the log, in prose, invisible to
every test the bot had.

## The rest

| Module | What it holds |
|---|---|
| `stats` | Moving-block bootstrap `compare()`, `bootstrap_mean_ci()`, `concentration()` |
| `gate` | Clause shapes: `floor`/`ceiling`/`all_of`/`any_of`/`both_arms`, concentration, drawdown, profit factor |
| `nulls` | `stable_uniform`/`stable_normal` (hash-seeded, order-independent), `pass_mark`, `Ladder` |
| `decay` | Is a live record distinguishable from random? Percentile bands over an injected draw |
| `trials` | Append-only trial log; `walk_forward` where the OOS number never selects |
| `snapshot`, `golden`, `fingerprint`, `embargo` | Hash-pinned inputs, "this moved no number", decision-surface stamping, outcome embargo |

**No thresholds ship.** "15 trades", "profit factor 1.3", "half the net
result" are a domain's pre-registered numbers and belong in its log, where
the linter can hold them to account. This package gives the shapes.

## What it is not

Not a backtester, not a strategy, not a claim that anything has an edge. The
worked example in [`examples/recsys_ab/`](examples/recsys_ab/) is a null
treatment put through the full protocol — every comparison comes back
INCONCLUSIVE and the ladder FAILs, which is the correct output. Its §3
addendum records a negative control that was wrong on its first run and
fired on a pipeline with no treatment in it; that is left in the record
rather than quietly fixed.

Apache-2.0. Extracted from [repete1-bot](https://github.com/connorshibley/repete1-bot).
