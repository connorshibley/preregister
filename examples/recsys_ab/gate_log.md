# Recommender A/B — gate log

The append-only record of every measured decision in this example. Trial
count starts at zero. Nothing here is edited after the fact; corrections are
appended as dated addenda.

Method rules:

* **Pre-register.** The rule is written down before the run, not after the
  numbers are seen.
* **Declare EDGE or CAPACITY before measuring.** EDGE needs a CI excluding
  zero; CAPACITY only needs to rule out being worse.
* **Correct for the trial count, cumulatively.**
* **Controls spend no budget and can never be adopted** — only invalidate.

## §1 — EDGE: two ranking tweaks against the current ranker

**Claim class: EDGE. K: 0 → 2. Committed BEFORE the assignment salt is drawn.**

### The hypothesis

    H: at least one of the two candidate rankers raises mean engagement per
       user over the incumbent, on a population assigned before either
       ranker is built.

### Exactly what is being tested, fixed now

Two arms, A and B. No other variant is tested; no threshold is swept. The
assignment salt is `ab-2026-01`, fixed here. `simulate.py` is committed in
the same change as this section and contains no results.

### Falsification criteria, declared before the numbers

1. The Bonferroni-corrected CI on the difference in means excludes zero.
2. At least 1,000 users in each arm (below that, the interval is a shrug).

### The negative control, declared in advance

The same engagement values, re-assigned under `relabel|ab-2026-01`. No
treatment is applied to anything, so a "significant" result there means the
pipeline manufactures effects and invalidates the arms above. The control
does not increment K and cannot be adopted.

### Prediction, stated now

Both arms come back INCONCLUSIVE. The generator draws every arm from one
distribution; if the protocol says otherwise, the protocol is broken.

### §1 RESULT — INCONCLUSIVE, both arms

Neither CI excludes zero at K=2. The control is also inconclusive, which is
what makes the two results above readable rather than merely disappointing.

**Prediction scored:** ✓ direction, ✓ both arms, ✓ control quiet.

### §1 tally

**2 trials, zero adopted.** Two arms declared, two trials spent.

## §2 — CAPACITY: serve the recommender to twice as many users

**Claim class: CAPACITY. K: 2 → 3. Committed BEFORE the wider cohort is drawn.**

The claim is NOT that engagement per user improves. It is that doubling the
served population does not make engagement per user *worse* — a reach claim,
carried by the deterministic clauses, with the interval only refusing it if
the wider arm is significantly worse.

### Falsification criteria

1. The corrected CI's upper bound is above zero (`not_worse`).
2. At least 1,000 users in the wider arm.

### §2 RESULT — not worse, and that is all it claims

The upper bound is above zero. Adoption is a product decision, not a gate
pass; nothing is adopted here.

### §2 tally

**3 trials, zero adopted.**

## §3 — CONTROL: the relabel ladder over five pre-registered salts

**Claim class: CONTROL. K unchanged: 3.** Null arms are instruments, not
candidates: a control spends no budget, and a PASS on a control cannot be
adopted — it can only invalidate.

### The arms, fixed now

Five salts: `abl-1` … `abl-5`. Never extended after a result is seen —
adding a sixth salt because the first five were quiet would turn the
variance band into a fabrication.

### Pass mark, fixed in advance

The treatment must beat the pooled relabelled null AND the control arm's own
mean, each with a CI excluding zero at K=3.

### §3 RESULT — FAIL

The treatment sits inside the null's range. This is a RESULT, not a
malfunction: a null generator that produced a PASS here would mean the
ladder measures the pipeline rather than the treatment.

### §3 tally

**3 trials, zero adopted.** A control spends no budget, and nothing was adopted.

### §3 addendum — the control was broken on its first run, and said so

**Appended the same day. Claim class: METHOD. K unchanged: 3.**
Correcting §3's construction, not replacing it.

The first `relabelled()` generated engagement under the *relabel* salt and
over a 800-user slice, rather than reusing the experiment's own values. That
moved the cohort offsets, which moved the mean, and the control returned
**SIGNIFICANT** — an effect manufactured entirely by the control's own
construction.

Read the other way round, this is the control working: it fired on a
pipeline that had no treatment in it at all, which is precisely the signal a
negative control exists to give. Had it stayed quiet while mis-built, the
two INCONCLUSIVE arms in §1 would have rested on an instrument nobody had
checked.

A control must change the LABELS and nothing else. Recorded here rather than
edited into §3, per this log's own append-only rule.

**3 trials, zero adopted.** A method correction is not a trial.
