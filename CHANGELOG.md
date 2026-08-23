# Changelog

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
