# <Project> — gate log

The append-only record of every measured decision in this project. Trial
count starts at zero. Nothing here is edited after the fact; corrections are
appended as dated addenda that quote what they correct.

Method rules:

* **Pre-register.** The rule is written down before the run, not after the
  numbers are seen.
* **Declare EDGE or CAPACITY before measuring.** EDGE needs a CI excluding
  zero; CAPACITY only needs to rule out being worse.
* **Correct for the trial count, cumulatively.**
* **Controls spend no budget and can never be adopted** — only invalidate.

## §1 — EDGE: <one-line title, verdict-first once known>

**Claim class: EDGE. K: 0 → 2. Committed BEFORE <the artefact that could contaminate this> exists.**

### The hypothesis

    H: <a falsifiable statement>

### Exactly what is being tested, fixed now

<Each knob: its value and how it was chosen. State "no other <window/threshold>
is tested" for each — that sentence is what makes this a pre-registration
rather than a description.>

### Falsification criteria, declared before the numbers

1. The Bonferroni-corrected CI on the difference in means excludes zero.
2. At least <n> observations in each arm.

### The negative control, declared in advance

<The mirror arm. What it would mean if it fired. Controls do not increment K
and cannot be adopted.>

### Prediction, stated now

<What you expect, stated so that being wrong is visible.>

### §1 RESULT — <VERDICT>

<Raw output, verbatim.>

**Prediction scored:** <✓/✗ per claim.>

### §1 tally

**2 trials, zero adopted.** <One clause: why K moved, or did not.>

## §2 — CONTROL: <title>

**Claim class: CONTROL. K unchanged: 2.** Null arms are instruments, not
candidates.

### The arms, fixed now

<Salts or seeds, fixed in advance. Never extended after a result is seen.>

### §2 RESULT — <VERDICT>

**2 trials, zero adopted.** A control spends no budget.
