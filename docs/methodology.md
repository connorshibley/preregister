# The methodology

Why pre-registration, what a claim class is, how to pick K, and when not to
use any of this.

The API is in the [README](../README.md). This file is the reasoning the API
encodes — the part that was previously buried in module docstrings.

---

## The problem it solves

You try a configuration. It doesn't work. You try another. Eventually one
looks good, and you report that one.

Nothing in that story is dishonest, and the result is still worthless. The
more variants you try, the better the best one looks by luck alone — the
False Strategy Theorem, in a domain where it has a name. The defence is not
willpower. It is **writing down what you will test, and how many things you
tried, before you look.**

Everything below is bookkeeping in service of that one idea.

---

## Claim classes

A section of a log declares what kind of claim it is making. The class
determines whether it spends budget.

### Classes that spend

| Class | Claim | The test |
|---|---|---|
| `EDGE` | "this is better" | The corrected CI **excludes zero**. `Comparison.significant` |
| `CAPACITY` | "this reaches more at no worse quality" | The corrected CI's upper bound is **above zero**. `Comparison.not_worse` |
| `GATE` | "this clears a pre-registered bar" | The deterministic clause set passes |

### Classes that spend nothing

| Class | What it is |
|---|---|
| `CONTROL` | A null arm, a negative control, an ablation ladder. **An instrument, not a candidate.** |
| `MEASUREMENT` | Characterising an instrument. Nothing adopted or rejected. |
| `DIAGNOSTIC` | A signal, explicitly not a verdict. |
| `METHOD` | A finding about the protocol itself. |
| `INFRA` | A defect fix. |
| `GOVERNANCE` | An enablement or override decision. |
| `EXPERIMENT` | A forward test under pre-registered kill criteria. |
| `INTAKE` | An outside idea reviewed and parked without being tested. |

### Choosing one

Ask **"what would this section license me to do?"**

- If a good result would let you *adopt* something → it spends. EDGE if you
  claim it is better; CAPACITY if you claim only that it is not worse.
- If a good result could only ever *invalidate* something → it is a CONTROL.
- If nothing about the system changes either way → MEASUREMENT, DIAGNOSTIC or
  METHOD.

The rule that makes controls work: **a control spends no budget, and a PASS
on a control cannot be adopted — it can only invalidate.** If passing your
control would tempt you to ship it, you have written a candidate and called
it a control.

Two corollaries the source project had to state explicitly, both after being
tempted:

- *"An override is not a trial."* Deciding to disable something on
  inconclusive evidence is GOVERNANCE. Writing it up as a kill criterion
  firing would corrupt the meaning of every kill criterion you ever
  pre-registered.
- *"Infrastructure is not a trial."* Fixing a bug does not spend budget, even
  when the bug changed results.

---

## K — the trial count

`compare(baseline, candidate, n_comparisons=K)` divides α by K. K is the
number of things you tried.

### Cumulative or per-family?

**Both are legitimate and they answer different questions.** Getting this
wrong silently is the most likely way to misuse this package.

- **Cumulative** — every arm the programme has ever registered. This is the
  bar for "does this thing have an edge", because your search across months
  is one search.
- **Per-family** — the arms in *this* section only. This is the bar for
  "which of these five variants is best, given I'm going to pick one."

The source project uses cumulative for adoption decisions and per-family for
within-section selection, and **deliberately left four scripts on per-family**
during the migration rather than mechanically converting them — converting
one would have silently changed K from 3 to 66 and changed what it measured.

Whichever you use, **say which in the log.** A K with no stated basis is not
a correction, it is a number.

### Where K comes from

Not a literal in your code. `budget.Registry` reads it from the record:

```python
reg = Registry.load("gate_verdicts.json")
reg.spend("§12", n_arms=3, cls="EDGE", committed_before="the data was pulled")
compare(baseline, candidate, n_comparisons=reg)
```

`spend()` refuses a class that shouldn't spend, refuses zero arms, and
refuses a trial that does not say what it was committed *before*. That last
one is not decoration — "committed before" is the only claim in the whole
method that cannot be checked by machine, so the least you can do is force
someone to write it down.

### K only goes up

There is no mechanism for reclaiming budget, and that is deliberate. If
abandoning a line of investigation refunded its trials, the correction would
mean nothing.

---

## What to do when the answer is INCONCLUSIVE

This is the most common outcome and the least documented, so plainly:

**INCONCLUSIVE means the data cannot distinguish the arms.** It does not mean
"nearly significant", and it does not mean "try again with a different seed".

Your options, in order of honesty:

1. **Accept it and stop.** The default. Record the result, record that the
   prediction was scored, move on. Most things do not work.
2. **Collect more data and re-run — as a new trial.** Re-running the same
   hypothesis on more data is a legitimate experiment. **It spends budget
   again.** Pre-register the new n before you start.
3. **Change the hypothesis.** Also legitimate, also a new trial, also spends.

What is not available: re-running with a different threshold, a different
window, or a different subset, and reporting the run that worked. That is the
thing this whole apparatus exists to prevent, and it will not be visible to
anyone reading only your final number.

A useful reframe: **INCONCLUSIVE is a result.** The source project's log
records 66 of them and zero adoptions. That record is the reason anyone
should believe its 67th claim.

---

## When *not* to use this

Stated because a tool that claims universal applicability is making a claim
it has not tested.

**Do not use it for exploratory work.** Pre-registration is for confirming a
hypothesis, not forming one. Looking at data to work out what is interesting
is legitimate and necessary; just do not report the looking as a test. Keep
exploration out of the log entirely, or record it as MEASUREMENT.

**Do not use it when n is small enough that the CI is meaningless.** A
bootstrap CI over a dozen observations is very wide and technically correct
and practically useless. It will tell you INCONCLUSIVE forever. Fix the
sample, not the statistic.

**Do not use it where there is no natural arm.** If you cannot state what the
comparison is against, there is nothing for `compare()` to do. A single
number with no baseline is a measurement, not a claim.

**Do not use it to relitigate.** If a section is closed, it is closed. The
log is append-only; corrections are dated addenda that quote what they
correct. Editing history to make a check go green is the most damaging thing
available to a project like this.

**Do not use the block bootstrap on long-range dependence.** It preserves
short-range clustering; it cannot see regime changes longer than the block.
`stats.py` says so in its own docstring, and that limit is real.

---

## The append-only rule

The log is never edited. Corrections are appended, dated, and quote the
sentence they correct.

This feels pedantic until the first time it matters. The source project's
§56 records that its bot had fabricated every closed trade it ever reported —
and that a test had *asserted the defect was correct behaviour*. The
correction is an addendum. §56's own addendum then corrects §56, in public,
two days later, opening: **"Both halves are false."**

That is the shape of a record worth trusting: not one that was right the
first time, but one where being wrong is visible.

`AppendOnlyLock` makes it checkable — it hashes everything above the last
heading, so an edit to history fails the lint while an append does not.
