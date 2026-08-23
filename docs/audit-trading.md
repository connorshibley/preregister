# The trading pack

Domain specifics for [`audit.md`](audit.md) when the system under review is a
trading agent or strategy. These are the parts of the original protocol that
did not survive generalisation intact — kept here because they are where the
teeth are, and a rubric generalised until it is comfortable has stopped
working.

The original, unedited, is in
[`audit-protocol-verbatim.md`](audit-protocol-verbatim.md).

---

## Gate 2 — the delisting fraction

The general form says "report the fraction of observations from entities that
exit within the sample." In equities that number is concrete and easy to
check:

> **If the delisting fraction is zero on a multi-year equity backtest, the
> universe is survivor-conditioned and the gate FAILS.**

There is no ambiguity about this one. A US equity universe over any
multi-year window contains delistings, mergers and bankruptcies. A backtest
whose universe contains none of them has excluded exactly the regime that
produces the losses it claims to survive.

This is worth stating because it is the gate most likely to fail silently on
an otherwise careful project. In the audit that produced this document, the
sibling equities bot was scored **INVALID** on precisely this: a universe of
~3.9M bars over 26 years containing **0 symbols that ever failed** — 0.00%.

Selection driven by news volume or present-day prominence is the same defect
wearing a different hat. If the ticker list was assembled from "names people
were talking about", it was assembled with knowledge of who survived.

## Phase 2.1 — the statistics that have names here

Trading has a mature literature on exactly the multiple-testing problem this
rubric cares about. Use it rather than reinventing:

- **Probabilistic Sharpe Ratio (PSR)** — the probability the true Sharpe
  exceeds a benchmark, given skew and kurtosis.
- **Deflated Sharpe Ratio (DSR)** — PSR corrected for the number of trials N,
  sample length T, and the empirical moments. This is the number that matters.
- **The implied Sharpe threshold** given N, T, skew and kurtosis. State it,
  then state whether the headline clears it.
- **Probability of Backtest Overfitting (PBO)** via combinatorially symmetric
  cross-validation. **PBO above roughly 0.5 means the selection process
  itself was the source of the result.**

If N was not tracked, all four are uncomputable and the reported Sharpe is
uninterpretable. Say that plainly; do not estimate N charitably.

## Phase 2.3 — the two regime signatures

Split returns by bull, bear, sideways, high-volatility and any crisis window
in the sample. Two failure signatures are empirically common in model-driven
timing strategies and worth looking for by name:

- **Overly conservative in bull markets**, so it loses to simply holding.
- **Overly aggressive in bear markets**, so it takes outsized losses.

Both produce a respectable-looking full-sample number.

## Phase 2.4 — factor attribution

Decompose into market beta, size, value, momentum and residual. State how
much of the claimed alpha survives. Positive performance may be beta, style
exposure, or a favourable window — none of which is skill, and all of which
are cheaper to buy.

## Phase 2.5 — the ladder, in trading terms

| Arm | Trading form |
|---|---|
| (i) | the full agent |
| (ii) | same scaffold, signal replaced by a random entry at matched trade count |
| (iii) | same scaffold, signal replaced by a simple deterministic rule (e.g. an SMA cross) |
| (iv) | buy and hold |
| (v) | the risk layer alone, no signal |

Two details that matter and are easy to get wrong:

**Match the rate, not just the arm.** A null that trades ten times more often
than the treatment is a different experiment. Match the null's trade count to
the treatment's realised count — `preregister.nulls.entry_rate` exists for
this.

**Fix the salts in advance and never extend them.** Adding a sixth random
seed because the first five were quiet turns the variance band into a
fabrication.

## Gate 5 — the costs specific to trading

- **5a** Signal-time fills on anything short-horizon is a **FAIL**. Trades
  execute at the price prevailing after full decision latency.
- **5b** Spread, commissions, slippage and market impact, each specified and
  applied — not a single blended number.
- **5c** Token and inference cost expressed as **annualised basis points of
  drag on the capital base**. A strategy whose edge is smaller than its own
  inference bill is not a strategy.
- **The stress arm.** Re-run the whole gate at a cost multiplier (1.5× is a
  defensible default) and require **both** arms to pass. A strategy that
  passes at 1.0× and fails at 1.5× has not "nearly passed" — it has told you
  its edge is smaller than the uncertainty in the cost model, which is a
  more useful fact than a marginal return number.

## Gate 4 — abstention in a trading context

The action space must contain an explicit **"no trade"**, and choosing it
must be scored as a valid outcome rather than a missed opportunity. An
evaluation that forces a directional call on every bar converts ignorance
into false precision, and the resulting confidence will be consumed by
position sizing.

## A clause the general rubric does not have: concentration

Not in the original protocol — added to the source project as its §37 after a
strategy cleared **every** deterministic gate on a single trade.

> Return +65.93%, profit factor 3.379, 36 trades, against a benchmark of
> −4.64%. One trade was **118.5% of the net result**. Remove it and the same
> 36 trades lose money at profit factor 0.542.

So check it explicitly: **the largest single trade's share of the net
result.** A mean-based control does not catch this — the same outlier that
fools the gate fools the mean, which is why the project's random-entry
control passed it too.

`preregister.gate.concentration_clause` implements this. It takes no default
threshold, because the source project's 0.5 was chosen *after* seeing 1.185
and says so in its own log.

## What the trading pack does not cover

Market microstructure, venue-specific behaviour, funding and borrow costs,
and anything about crypto perpetuals. The audit that produced this document
covered spot crypto and US equities only, and a rubric should not claim
range it has not been run against.
