# Changelog

## 0.1.3 — 2026-08-23

**Fix:** `Comparison.describe()` had dropped the per-arm sample sizes that
the source implementation printed. "INCONCLUSIVE at n=12" and "INCONCLUSIVE
at n=1200" are different statements; a reader who cannot see which one this
is cannot weigh it. Caught by diffing the extracted output against the
original rather than trusting that a lift was faithful.

## 0.1.2 — 2026-08-23

**Fix:** the parser read K statements and tallies inside quotations as
declarations. A log that discusses its own history quotes earlier sections,
and one that did was reported as restating K at 48 inside a section running
66 -> 66. Inline code spans and quoted phrases are now masked before the K
and tally patterns run, positions preserved. Found by running the linter
against a live log rather than the vendored snapshot.

## 0.1.1 — 2026-08-23

Publishing only; no code change. Adds Trusted Publishing (OIDC) so releases
carry no API token, and a step that refuses to publish when the tag and the
built version disagree.

## 0.1.0 — 2026-08-22

First extraction from `connorshibley/repete1-bot`.

**New in this package** (did not exist in the source):

- `budget.Registry` — the K ledger. `compare()` reads K from the record
  instead of a hand-copied literal. Spending classes must declare what they
  were committed before; controls spend nothing.
- `gatelog` — a linter for pre-registration logs: claim-class enum, K
  arithmetic across sections, tally agreement, committed-before, EXPERIMENT
  kill criteria, and an append-only lock. 14 rules, each with a firing and a
  quiet fixture and a meta-test that refuses a rule without both.

**Lifted, bit-identical** (pinned against values computed in the source
repo's own venv): the block-bootstrap comparison, the hash-seeded uniform and
normal draws (three copies in the source, one here), the gate clause shapes,
the decay bands, the snapshot/golden/fingerprint/embargo primitives.

**Examples**: the bot's real gate log, vendored verbatim, linting with zero
errors; and a null recommender A/B that runs the whole protocol and correctly
finds nothing.
