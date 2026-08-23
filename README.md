# preregister

Pre-registration, multiple-comparison budgets and null ladders — as code, not
as a checklist.

## Where it comes from

A cryptocurrency paper-trading bot ran **66 pre-registered trials** over two
months and **adopted zero** of them. Every trial declared its hypothesis,
its arms, its falsification criteria and its negative control before the
data was touched; every result was appended to a log that was never edited,
only corrected by dated addenda; every significance test was Bonferroni-
corrected against the *cumulative* trial count. The strategies had no edge.
The method said so, 66 times, and was right.

Two things in that discipline were still held together by a human:

1. **The trial count K was a hand-copied integer** in every gate script —
   fifteen scripts, three different conventions, none pinned by a test.
2. **The log's own grammar** — claim class, `K: 65 → 66`, "committed
   before the run", controls spend nothing, predictions scored — was
   enforced entirely by prose.

This package is the arithmetic for both, plus the statistics and
reproducibility primitives the bot used, with the trading removed.

## What it is not

It is not a backtester, a strategy, or a claim that anything has an edge.
The worked example in `examples/recsys_ab/` is a null treatment put through
the full protocol; its verdict is INCONCLUSIVE, and that is the correct
output. `examples/repete1_gate_log.md` is the bot's real log, vendored
verbatim, with the linter's findings on it pinned.

## Status

0.1.0 — being extracted. See `CHANGELOG.md`.

Apache-2.0. Pure Python 3.12, no dependencies.
