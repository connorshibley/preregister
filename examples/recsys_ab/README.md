# A null recommender A/B, run through the whole protocol

No market data, no network, no clock — `simulate.py` draws engagement from
one distribution for every arm, so **the treatments are null by
construction**.

    python run.py

Every comparison prints INCONCLUSIVE and the ladder FAILs. That is the
correct output, and it is the point of the example: this is what a
pre-registration protocol says when there is nothing to find. The log this
package was extracted from said it 66 times.

Three sections in `gate_log.md`, each a claim class the package knows:

| § | Class | K | What it shows |
|---|---|---|---|
| §1 | EDGE | 0 → 2 | Two arms; the CI must exclude zero. It does not. |
| §2 | CAPACITY | 2 → 3 | A reach claim: `not_worse` passes where `significant` does not. |
| §3 | CONTROL | unchanged | A relabel ladder over five fixed salts. Spends no budget. |

`gate_log.md --strict` lints clean, and `gate_log.lock.json` is its
append-only lock: edit anything above the last heading and the linter fails.

**Read §3's addendum.** The control was wrong on its first run and came back
SIGNIFICANT on a pipeline with no treatment in it — because the control
changed the data as well as the labels. It is left in the record rather than
quietly fixed, because a negative control that fires on a broken instrument
is the control doing its job.
