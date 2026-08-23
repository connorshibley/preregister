# The claim audit

**Is this result evidence?**

A rubric for reviewing whether a reported result — a model's benchmark score,
an agent's track record, an A/B test's lift — is evidence of what it claims,
or an artifact of leakage, selection, or unpriced cost.

It is adversarial by default. The prior is that any reported effect is an
artifact until the evidence rules that out. It does not soften findings to be
agreeable, and it does not fill gaps with assumptions favourable to the
system under review.

This is the generalised form. The version actually run against a live system
— including its trading-specific parts and the verdict it returned — is
preserved unedited in [`audit-protocol-verbatim.md`](audit-protocol-verbatim.md),
so you can check this generalisation against the original rather than take it
on trust. Domain specifics for trading are in
[`audit-trading.md`](audit-trading.md).

---

## How to read a result from this

Three currencies, and **they never convert into each other**:

| Phase | Currency | Rule |
|---|---|---|
| 1 — Structural gates | PASS / FAIL / MISSING | Binary. Never averaged, never partially credited. |
| 2 — Statistical validity | Numbers | Only meaningful if Phase 1 passed. |
| 3 — Mechanics | 0–3 per dimension | Every score needs a quoted citation. |
| 4 — Deployment readiness | Present / absent | Binary. |
| 5 — Verdict | One tier | Determined by the worst of the above, not the average. |

**If any Phase 1 gate fails, the reported number cannot support a
deployability claim, however good it looks.** Say so plainly in the verdict.
A gate failure is not offset by a strong Phase 2.

**MISSING is not PASS.** A gate you could not evaluate is recorded as
MISSING, and that is a finding about the system's auditability — which is
itself a property worth knowing.

---

## Inputs

Request these before evaluating. If any are unavailable, record them MISSING
and carry that forward into the gates. **Do not proceed as if a missing input
were a passing one.**

1. **Architecture** — topology, models used with version and stated training
   cutoff, tools, memory, retrieval sources, orchestration, prompt templates.
2. **Decision interface** — the exact action space, including whether
   abstention exists.
3. **Data and population provenance** — where the evaluation set came from,
   how it was assembled, and as of when.
4. **The full outcome series**, not a summary — every decision, not the
   winners.
5. **At least 20 decision traces**, sampled without cherry-picking.
6. **Search history, including N** — the number of configurations,
   prompts, thresholds or hyperparameters actually tried.
7. **Cost model** — including inference cost and latency.
8. **The control layer** — what enforces limits, and whether a model sits in
   the enforcement path.

Item 6 is the one most often missing and the most consequential. Without N,
no significance claim can be interpreted at all.

---

## Phase 0 — Classify

Three sentences: what the system claims to do, what the claimed effect is,
and **what would have to be true about the world for that effect to persist.**
Name the class (model-native, classical/statistical, hybrid). Name the
decision horizon. This framing determines which diagnostics bind.

---

## Phase 1 — Structural validity gates

### Gate 1 — Temporal sanitation

*Does every decision at time t use only information that existed and was
accessible at t — through weights, retrieval, and tools alike?*

- **1a** Is the model's training cutoff disclosed, and does the evaluation
  window sit entirely after it? A nominal cutoff is weak evidence, not proof:
  published cutoffs are opaque and models frequently surface post-cutoff
  material.
- **1b** Is the retrieval corpus built from archived snapshots with
  verifiable as-of timestamps, or is it querying present-day search? **Live
  search during a historical evaluation is an automatic FAIL.** Documents get
  edited while keeping their original publication dates, and modern rankers
  use engagement signals that did not exist at t.
- **1c** Are structured inputs point-in-time, or restated after the fact?
- **1d** Are per-decision traces logged well enough that an independent
  auditor could verify temporal consistency action by action?

For model-native and hybrid systems, **also** require Diagnostic A
(memorisation probe) and Diagnostic B (entity substitution). Absent those,
this gate is MISSING, not PASS.

### Gate 2 — Population validity

*Is the evaluation population defined as of each decision date, including
cases that later disappeared?*

- **2a** Report the fraction of observations from entities that exit within
  the sample — churned accounts, delisted instruments, deprecated items,
  patients lost to follow-up, deleted content. **If that fraction is zero
  over a multi-period sample, the population is survivor-conditioned and the
  gate FAILS.**
- **2b** If case selection was driven by present-day prominence — popularity,
  traffic, news volume, "the examples we had lying around" — that is
  survivorship through the back door. FAIL.

A population with no failures in it cannot support any claim about downside
risk, because it has excluded the regime that produces downside risk.

### Gate 3 — Rationale robustness

*Are the system's stated reasons testable objects rather than decoration?*

- **3a** Do key factual claims in each rationale trace to a specific
  retrieved passage or structured field?
- **3b** What is the **measured violation rate** — references to things that
  did not exist, wrong quantities, facts that postdate t? Report the rate,
  not examples.
- **3c** Diagnostic C (negative control). If the system produces confident
  outputs with clean causal stories on scrambled input, FAIL.

Treat chain-of-thought as **an output to be tested, never a window into the
decision process.** Fluent reasoning is not evidence of a real driver.

### Gate 4 — Epistemic calibration

*Does the system make uncertainty visible and abstention legitimate?*

- **4a** Does the action space contain an explicit "insufficient evidence"
  option, and is choosing it scored as a valid outcome rather than a miss?
- **4b** Does the system emit a confidence a downstream controller can
  consume?
- **4c** Is that confidence calibrated? Report a Brier score or reliability
  curve. **Uncalibrated confidence is worse than none**, because downstream
  logic will consume it.

An evaluation that forces a call on every case converts ignorance into false
precision.

### Gate 5 — Realistic cost

*Is the reported number net of everything it takes to produce it?*

- **5a** Are decisions applied at the state prevailing **after full decision
  latency**, or at the state at signal time?
- **5b** Are the frictions of acting specified and applied?
- **5c** Are inference and token costs included, expressed as a rate against
  whatever the effect is measured in?
- **5d** Is the latency **distribution** reported, or only a best case?
- **5e** **Are baselines budget-matched?** A heavy multi-step pipeline
  compared against a cheap baseline on gross outcome is not a comparison.

*Output Phase 1 as a table: gate, verdict, the single specific piece of
evidence that drove it, and what would flip it.*

---

## Phase 2 — Statistical validity

Only meaningful if Phase 1 passed. If it did not, still compute these, but
label the whole section **"conditional on gates that currently fail."**

**2.1 Multiple testing.** Using N — the count of configurations tried — state
the corrected significance threshold and whether the headline clears it.
**If N was not tracked, say so and treat the headline as uninterpretable.**
`preregister.budget.Registry` exists so that N is a number read from a record
rather than remembered.

**2.2 Sample adequacy.** Is the record long enough for the claimed effect to
be distinguishable from zero? A short window supports no claim at all,
whatever the number.

**2.3 Subgroup decomposition.** Split results by the regimes or segments that
exist in the sample and report separately. **A system that only works in one
regime has not been shown to work.**

**2.4 Attribution.** Decompose the outcome into known baseline factors and
residual. State how much of the claimed effect survives. Raw outcome is a
noisy proxy for skill.

**2.5 The ablation ladder.** Five runs on identical data, costs and
population:

| Arm | What it isolates |
|---|---|
| (i) the full system | the claim |
| (ii) same scaffold, decision replaced by a random draw | whether the model does anything |
| (iii) same scaffold, decision replaced by a simple deterministic rule | whether the model beats a heuristic |
| (iv) the do-nothing baseline | whether acting beats not acting |
| (v) the guardrails alone, no signal | whether the rails are the result |

**If (i) does not beat (ii) and (iii) by a margin exceeding run-to-run
variance, the model is decoration and you should say so directly.** This
single test kills more systems than everything else combined.

**2.6 Variance.** Report across at least 5 seeds. **If the spread across runs
is comparable to the claimed effect, the effect is noise.**

---

## Phase 3 — Mechanics

Score each 0–3. **You must quote specific trace evidence before assigning any
score. A score without a citation is invalid — write INSUFFICIENT EVIDENCE
instead.**

`0` absent or actively broken · `1` present but unreliable, would fail under
mild stress · `2` sound, with known and bounded limitations · `3` robust,
tested and instrumented.

1. **Information handling** — does it distinguish signal from noise, or react
   to every input? Check for reaction to stale or duplicate material.
2. **Tool-use correctness** — well-formed calls, right arguments, results
   actually used. Check for calls whose output is ignored in the rationale.
3. **Plan coherence** — a consistent thesis across steps, or post-hoc
   justification of a decision already made?
4. **Sizing discipline** — is commitment a function of conviction and
   uncertainty, or effectively constant?
5. **State fidelity** — does the system correctly track its own state across
   steps? Drift here is common and expensive.
6. **Adversarial robustness** — Diagnostic G. Procedural systems can collapse
   catastrophically under state tampering while looking fine on clean data.
7. **Bias audit** — check for preference for the familiar under ambiguous
   evidence, confirmation bias within multi-agent debate, and optimising a
   proxy metric at the expense of the real one.
8. **Determinism where it matters** — is anything that must be exact handled
   by code rather than by the model?

---

## Phase 4 — Deployment readiness

Binary. Present or absent.

1. A **deterministic control layer**, evaluated after the model proposes and
   before the action executes, **with no model in the enforcement path**.
   *"The prompt tells it not to" is not a control.*
2. Limits enforced **in code and versioned**.
3. A **circuit breaker** with a defined trigger.
4. A **kill switch** with named human owners, defined triggers, and evidence
   it has actually been tested.
5. **Full decision reconstruction** — which signals fired, what each
   component argued, which guardrails were evaluated and what they returned.
6. A **manual override** exercisable independently of the main path.
7. **Silent-degradation monitoring** — drift in effect size, cost, abstention
   rate, average confidence.

---

## Phase 5 — Verdict

Assign exactly one tier.

| Tier | Meaning |
|---|---|
| **INVALID** | One or more Phase 1 gates failed. The result is not evidence of anything and cannot be repaired by better numbers. State which gate and the minimum fix. |
| **PROOF OF CONCEPT** | Gates pass but Phase 2 is weak: short sample, unclear N, no ablation, or the effect does not clear the multiple-testing threshold. Interesting; not evidence of an effect. |
| **PILOT CANDIDATE** | Gates pass, statistics defensible, ablation shows the system adds something — but no forward out-of-sample record. Specify the minimum forward period and what would constitute failure. |
| **LIMITED DEPLOYMENT** | All of the above, plus a live deterministic control layer, a tested kill switch and full auditability. Specify a cap and the conditions that force a halt. |

Then produce, in order:

1. The **three most likely reasons this number is wrong**, ranked, each with
   the specific evidence that made you rank it there.
2. The **single cheapest experiment** that would most change the verdict.
3. A **fix list ordered by impact/effort**, no more than seven items.

---

## Standing rules

1. **Evidence precedes score.** Quote the trace, the log line, or the number
   before judging it. No citation means INSUFFICIENT EVIDENCE, not a middling
   score.
2. **Never use a model judgement where a deterministic check exists.** Limit
   breaches, timestamp ordering, schema validity and argument correctness are
   closed-form. Check them; do not opine on them.
3. **Do not reward length or fluency.** A longer trace with more tool calls
   is not a better one. Penalise steps that add cost without changing the
   decision.
4. **A missing input is a finding, not a blank.** Say what is missing and
   what it blocks.
5. **Do not average a gate failure away.** Gates and scores live in different
   currencies.
6. **If the headline is strong and the gates fail, lead with the gate
   failure.** The reader's instinct is to look at the number first, and your
   job is to stop that being the last thing they remember.

---

## The diagnostics

> **Added 2026-08-23.** The original protocol referenced Diagnostics A, B, C
> and G as binding on Gates 1, 3 and mechanics 3.6, but **never defined
> them** — a real gap, recorded here rather than quietly filled. These
> definitions are an addition to the original, not a recovery of it.

**Diagnostic A — memorisation probe.** Ask the model about specific outcomes
in the evaluation window without providing them. If it can recall them, the
window is inside its training data and Gate 1 fails regardless of the stated
cutoff.

**Diagnostic B — entity substitution.** Re-run decisions with entity
identifiers replaced by consistent pseudonyms, holding all other features
constant. A large performance drop indicates the system is keyed on identity
recall rather than on the features it claims to use.

**Diagnostic C — negative control.** Run the system on scrambled or
label-shuffled input where no real signal exists. **If it still produces
confident outputs with clean causal stories, its rationales are
manufactured.** This is the single most informative cheap test available, and
the one most often skipped.

**Diagnostic G — state tampering.** Corrupt the system's view of its own
state — wrong balances, stale positions, duplicated records — and observe
whether it detects the inconsistency or proceeds confidently. Procedural
systems frequently look excellent on clean data and fail catastrophically
here.

---

## What this rubric cannot do

It cannot tell you a system *works*. Every tier above LIMITED DEPLOYMENT is
still a statement about **evidence quality**, not about the world. A system
that passes every gate with a defensible Phase 2 has earned the right to be
tested forward — nothing more.

It is also biased toward saying no, deliberately. If most candidates fail
it, that is the instrument reading correctly in a domain where most
candidates do not work. The failure mode to watch for is the opposite one: a
rubric that never fails anything is not measuring.
