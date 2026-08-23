# Repete1 crypto gate log

The append-only record of every measured decision in the crypto programme.

**Trial count restarts at zero here.** Nothing in
`EQUITIES_ARCHIVE_backtest_candidates.md` counts toward the Bonferroni
correction, and nothing in it is evidence about crypto. That archive is kept for
METHOD — pre-registration, one frozen snapshot per comparison, EDGE vs CAPACITY
declared up front, correction against the cumulative trial count. Read it for how
to decide, never for what was decided.

Method rules carried over verbatim:

* **Pre-register.** The rule is written down before the run, not after the
  numbers are seen.
* **One frozen snapshot** for every comparison in a section. Live re-fetches of
  the same window drift intraday; the equities project lost the §1–§13 snapshot
  entirely and those numbers are permanently unreproducible.
* **Declare EDGE or CAPACITY** before measuring (METHOD NOTE 5). EDGE → the
  confidence interval must exclude zero. CAPACITY → deterministic clauses carry
  the decision and the CI only has to show per-trade P&L is not significantly
  worse.
* **Correct for the trial count**, cumulatively, via `significance.compare`.

---

## §1 — The cost model, and what it does to a strategy (Phase 2)

**Type: MEASUREMENT, not a gate.** Nothing was adopted or rejected here. This
section exists because the number is large enough to change what is worth
attempting, and because every later section is denominated in it.

### What changed

The inherited harness charged `fee_per_trade_usd: 0.0` and 5 bps of slippage.
Every equities gate verdict in the archive was measured at **literally zero
commission**. Phase 2 replaces that with a percentage model:

| | value | note |
|---|---|---|
| `fees.taker_bps` | 40 | Kraken retail spot (0.40%) |
| `fees.maker_bps` | 25 | carried, never applied — all orders are market orders |
| `fees.min_taker_bps` | 25 | floor: a promo tier must not make a strategy look good |
| `slippage.base_impact_bps` | 5 | paid even on a trivially small order |
| `slippage.impact_k` | 10 | `impact = base + k·sqrt(notional / top_of_book)` |
| `slippage.synthetic_half_spread_bps` | 3 | backtest only — a bar is not a book |

**A taker round trip therefore costs ~80 bps before impact**, against the ~0 bps
the archive assumed.

### The measurement

Identical fixture, identical strategies, identical rails. The ONLY change is the
cost model. `tests/golden/fixture.py`, 5 symbols × 900 bars, seed 11.

| strategy | trades | return @0 bps | return @40 bps | Δ | PF @0 | PF @40 |
|---|---|---|---|---|---|---|
| ma_crossover | 77 | +4.809% | **−0.611%** | −5.42 | 1.976 | 0.924 |
| tsmom | 105 | +0.201% | **−6.753%** | −6.95 | 1.034 | 0.381 |
| xsmom | 19 | +0.887% | **−0.370%** | −1.26 | 1.280 | 0.898 |
| meanrev | 88 | −0.583% | **−7.798%** | −7.22 | 0.847 | 0.058 |
| donchian | 19 | +0.674% | **−0.658%** | −1.33 | 1.219 | 0.836 |
| **ensemble** | **136** | **+2.130%** | **−7.302%** | **−9.43** | 1.247 | **0.503** |
| buy & hold | 1 | +20.123% | **+19.198%** | −0.93 | — | — |

### Cost accounting, once the instrumentation existed

`Result` gained derived cost properties in the same phase. They make the damage
legible in a way a return number does not:

| strategy | trades | fees | fees as % of GROSS edge | cost multiple |
|---|---|---|---|---|
| donchian | 19 | $1,205 | 220% | 0.454 |
| ma_crossover | 77 | $4,889 | 114% | 0.875 |
| xsmom | 19 | $1,207 | 144% | 0.693 |
| meanrev | 88 | $6,723 | 625% | −0.160 |
| tsmom | 105 | $6,452 | **2145%** | −0.047 |
| ensemble | 136 | $8,668 | 635% | 0.158 |

Read the third column carefully. **Every value is above 100%**, which means the
venue takes more than the entire gross edge — before the strategy has kept a
cent. tsmom's fees are twenty-one times its gross P&L.

The `cost_multiple` column is the Phase 8 clause, pre-registered at **>= 2.0**.
The best strategy here scores 0.875. Nothing is within a factor of 2.3 of
passing, and two are negative (no gross edge to divide at all).

### What this does and does not show

**It is NOT a verdict about crypto strategies.** The fixture is a seeded random
walk, not market data. No strategy has been gated, and the parameters are still
the equities ones, which are void.

**What it does show is the mechanism, and the mechanism is brutal:**

1. **Every strategy crossed from positive to negative.** Not narrowed — crossed.
   Every profit factor fell below 1.0, meaning each one now loses money gross of
   nothing at all.
2. **The damage scales with trade count, not with quality.** meanrev (88 trades)
   and tsmom (105 trades) lost ~7 points each; xsmom and donchian (19 trades
   each) lost ~1.3. The correlation with turnover is nearly perfect, and it is
   the only thing that predicts the damage.
3. **Buy-and-hold barely moved** — 20.123% → 19.198%. It pays the round trip
   ONCE. Every strategy here pays it 19 to 105 times.

Point 3 is the one that matters for the gate. `beats_bh` was already a clause;
under crypto costs it becomes the dominant one, because the benchmark's cost is
fixed while the strategy's is proportional to how often it trades. A strategy
must now out-earn buy-and-hold by *enough to pay for its own turnover*.

### Consequences, adopted as design (not as gate results)

* **"Trade more often" is not a lever, it is the cost.** The archive's §21 spent
  a section exhausting velocity levers and concluded "what remains is calendar
  time". Under an 80 bps round trip that conclusion is not merely reaffirmed, it
  is enforced by arithmetic.
* **Daily bars, not minutes.** A 4h strategy takes ~6× the round trips of a
  daily one and must find ~6× the gross edge to clear the same net. `SIX_HOUR`
  is pre-registered as the first timeframe candidate and must pass on its own.
* **The benchmark must use the identical cost function.** `buy_and_hold_return`
  now calls `fills.simulate_fill`, the same function the trades use. Charging a
  strategy a percentage while the benchmark paid a flat $0 would have rigged
  `beats_bh` in the strategy's favour, and under these costs the rigging would
  have been worth several points.

### Pre-registered for Phase 8, written before any crypto data is fetched

Three clauses are added to `backtest.enablement_gate`, and they are recorded
here **now**, before a single real bar has been loaded, so they cannot be tuned
to a result:

1. **Cost multiple.** `avg_gross_pnl_per_trade >= 2.0 × avg_cost_per_trade`.
   `profit_factor >= 1.3` is computed NET and is not sufficient alone — a
   strategy can be PF 1.3 gross and deeply negative net.
2. **Fee stress arm, mandatory.** Every gate runs twice, at `taker_bps` and at
   `1.5 ×`. **Both must pass.** A strategy whose edge evaporates at 1.5× cost was
   never an edge; it was a measurement of the fee schedule.
3. **Turnover ceiling.** Reject above a pre-registered round-trips-per-month
   regardless of return. Turnover multiplies every modelling error in the cost
   function, and the table above is what that looks like.

### Honest expectation

Given the above, **the most likely outcome of Phase 8 is that no strategy
passes.** That is the gate working, not the build failing. The correct response
is a slower timeframe or a different mechanism — not a looser gate.

### Golden re-baselined

`tests/golden/backtest_baseline.json` was re-captured here **deliberately**, and
this section is the record of why. It is the second and last sanctioned
re-capture before Phase 8. Phase 1's contract was that the Decimal refactor moved
nothing, and it moved nothing; Phase 2's contract is that the cost model moves
everything, and the table above is the diff.

---

## §2 — First contact with the real venue (Phase 3)

**Type: MEASUREMENT.** Nothing gated. `scripts/probe_venue.py` against live
Kraken public endpoints, 2026-07-27.

| | BTC/USD | ETH/USD |
|---|---|---|
| `base_increment` | 1e-8 | 1e-8 |
| `quote_increment` | 0.1 | 0.01 |
| `min_base_size` | 0.00005 | 0.001 |
| `min_quote_size` | $0.50 | $0.50 |
| 300 daily bars contiguous | yes | yes |
| observed spread | 0.0 bps | 0.4 bps |
| backtest ASSUMES | 6.0 bps | 6.0 bps |

### Three things worth recording

**1. The equities small-account problem does not exist here.** The archive
records a $10k account being rejected because "only 5 of 38 symbols cost under
$100", leaving two of three strategies ~87% disabled by whole-share arithmetic.
Kraken's minimum BTC order is 0.00005 BTC — about **$3.24** at the probed price —
with a $0.50 notional floor. Position sizing is effectively continuous, so
account size no longer decides which strategies can function.

**2. The backtest's spread assumption is conservative by an order of
magnitude — on the two deepest markets.** 6 bps assumed against 0.0 and 0.4
observed. That is the RIGHT direction to be wrong (`synthetic_half_spread_bps`
should be pessimistic, because assuming a tight spread that was not there
produces a backtest that cannot be reproduced live), and it is not a reason to
tighten it. BTC and ETH are the two tightest books on the venue; the assumption
has to survive the alts too, and it must survive them during a liquidation
cascade rather than on a quiet Monday. **Unchanged at 6 bps.**

**3. Kraken serves no 6h candle.** Available: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w,
2w. The plan's pre-registered "SIX_HOUR candidate" is therefore **4h**, and 4h
takes ~6× the round trips of daily — so it must find ~6× the gross edge to clear
the same net. `venue/market.ALLOWED_TIMEFRAMES` is restricted to `1d/4h/1h` in
code: anything faster is refused with the cost reason, because at ~80 bps a
round trip a minute-bar strategy cannot clear its own fees and no gate should
have to discover that one run at a time.

### The new rail this phase required

`risk.bars_contiguous` — a rail the equities bot never needed.

`bars_fresh` checks the NEWEST bar and cannot see a hole in the middle. A
daily-bar broker returned one window per call, so a gap meant a vendor outage
you would notice. Repete1 assembles a series from many paginated calls against a
24/7 market, where a dropped page is silent and looks exactly like a shorter
series.

A hole is dangerous rather than untidy because **every indicator here counts
BARS, not time**: SMA200 over a series missing forty of them is a 240-day
average wearing a 200-day label, RSI(2) compares two closes that may be a week
apart, and neither reports anything wrong. Being 24/7 is what makes the check
possible at all — on equities a weekend is a legitimate gap and this rail could
not exist without a market calendar.

Polarity matches `bars_fresh`: BTC discontiguous aborts the cycle, one alt
discontiguous drops that alt.

### A bug the fixtures caught before the venue could

The first pagination implementation started at `now − limit × granularity` and
paged forward. That assumes the venue's data runs to now. When the newest candle
is older — a halted market, a lagging venue, a fixture — the first request lands
past the end of the data and the whole series comes back EMPTY for a market with
years of history. "No data" and "no RECENT data" are different facts.

Rewritten to request the most recent page first and walk backwards, which has
neither problem: the first call always lands on real data if any exists, and
`limit` is satisfied from the newest end, which is the end that matters.

---

## §3 — The regime axis was a constant, and the data proves it (Phase 7)

**Type: MEASUREMENT.** Nothing gated. Kraken BTC/USD, 721 daily bars
(2024-08-06 .. 2026-07-27), 20-day realized vol.

### The annualisation was wrong before the thresholds were

`TRADING_DAYS = 252` assumes non-trading days. Crypto has none, so every
annualised vol was understated by sqrt(365/252) = **1.20x**. Fixed to 365 first,
because re-deriving thresholds against a 20%-wrong scale would have baked the
error into the fix.

### The measured distribution

| | 252 (equities) | 365 (correct) |
|---|---|---|
| min | 13.0% | 15.7% |
| p33 | 28.6% | **34.5%** |
| median | 33.6% | 40.5% |
| p67 | 37.9% | **45.6%** |
| max | 80.2% | 96.5% |

### What the inherited thresholds did to it

Equities buckets were `vol_low: 0.15`, `vol_high: 0.25`. Against real BTC data:

| bucket | share of days |
|---|---|
| low | **0.0%** |
| mid | 5.7% |
| high | **94.3%** |

**The vol axis was a constant wearing a feature's name.** Worse than useless:
`lessons.py` scopes staleness by regime and `memory.py` retrieves similar setups
by regime, so the learning loop would have kept segmenting evidence by a field
with one value and concluded that regime does not matter — a false negative
produced by a config default nobody re-derived.

### After (measured terciles: low <0.345, high >0.456)

Replayed over 340 historical days:

| label | share | | vol axis | share |
|---|---|---|---|---|
| down/high | 26.5% | | low | 36.2% |
| down/mid | 25.0% | | mid | 34.7% |
| up/low | 21.2% | | high | 29.1% |
| down/low | 15.0% | | | |
| up/mid | 9.7% | | | |
| up/high | 2.6% | | | |

Each bucket now carries roughly a third of history, which is what a regime axis
has to do to discriminate at all.

### Breadth, added as a NUMBER not an axis

Fraction of the universe closing above its own SMA. Computed from bars the cycle
already fetches — zero new vendor, zero new outage class. Rejected: BTC dominance
(needs a market-cap vendor for one number) and funding rates (perps only).

It is deliberately NOT part of `label`. `trend x vol` is 6 buckets; adding
breadth makes 18, and both the staleness tiers and similar-setup retrieval need
a bucket to hold enough observations to mean anything. Fragmenting the
statistics to gain an axis costs more than the axis is worth. It rides along as
a number on the record and in the judge's context.

It says something `trend` cannot: today's regime is `up/low` with **75% of the
universe above its SMA** — a broad advance. The same `up/low` label with breadth
at 20% would be BTC carrying a market that is otherwise falling, and a breakout
strategy entering an alt there is fighting the tape.

### The cross-check became two exchanges, not two vendors

Alpaca-vs-yfinance compared two republications of largely the same tape, which
agree by construction and so rarely disagree usefully. Kraken vs Coinbase is
genuine independent price discovery. Three changes forced by 24/7:

* **mid, not close** — there is no close;
* **a 5-second window, not "same session"** — the old guard was `ts[:10]`
  equality, which on a 24/7 market spans 24 hours, so two prices 18 hours apart
  would have been compared as simultaneous and any real move between them read
  as a feed lying;
* **two consecutive divergent samples before blocking** — a single wide print on
  a thin book is a thin book, and `ops.max_degradations_per_day` escalates on
  volume, so a noisy check does not merely cry wolf, it trips the SLO alarm.

Plus a fourth check the equities bot never needed: **own-feed staleness**. Its
cross-check fired only when both vendors REPORTED AND DISAGREED, so a feed that
simply went quiet was invisible. With a closing bell that was fine — quiet was
expected 17 hours a day. On a 24/7 market silence is never expected, and a stale
mark is what stops are evaluated against.

### Finding that constrains Phase 8

**Kraken serves ~721 daily bars (~2 years), not the 3+ years the plan assumed**
for universe admission. Phase 8's "≥3 years of history or excluded" rule cannot
be met on this venue and must be revised — either to ~2 years, or by sourcing
deeper history elsewhere and accepting a second data provenance. Recorded here
rather than discovered mid-gate.

---

## §4 — The first crypto gate. Nothing enabled, and one near-miss worth reading

**Type: GATE. Pre-registered in §1, before any crypto bar was fetched.**

Snapshot `crypto_bars_20260727.json.gz`, sha `c6216738baa74dc6`.
Universe BTC/ETH/LINK/LTC, >=2588 daily bars, IS 1811 / OOS 777.
Cost 40 bps taker (~80 bps round trip), stress arm at 1.5x.

| strategy | OOS ret | PF | trades | cost mult | fees/gross | verdict |
|---|---|---|---|---|---|---|
| ma_crossover | −8.54% | 0.668 | 47 | −2.24 | 45% | FAIL |
| tsmom | −2.04% | 0.754 | 19 | −0.77 | 130% | FAIL |
| xsmom | −9.16% | 0.164 | 13 | −13.22 | 8% | FAIL |
| **meanrev** | **+2.63%** | **1.798** | **21** | **2.68** | **37%** | **FAIL** |
| donchian | −1.82% | 0.759 | 14 | −1.23 | 81% | FAIL |
| *buy & hold* | *−30.90%* | | | | | |

**ENABLED: NONE.**

### The near-miss is the whole point

`meanrev` cleared **every single clause at 1.0x cost**: positive return, PF 1.798
against a 1.3 bar, 21 trades against a 15 bar, cost multiple 2.68 against a 2.0
bar, and it beat buy-and-hold by 33 percentage points in a window where simply
holding lost 30.9%.

Under the inherited equities gate — the one with no cost clauses — **meanrev
would have been enabled today.**

It failed on one thing:

    [1.5x cost] cost multiple 1.72 < 2.0 — the gross edge per trade ($191.73)
    is not twice the cost of capturing it ($111.35). Fees are 58% of gross.

That is precisely what the stress arm was pre-registered to catch, and the
distinction it draws is not "nearly passed". A strategy that clears the bar at
40 bps and misses it at 60 has told you something specific: **its edge is
smaller than the uncertainty in our own cost model.** We do not know Kraken's
fee tier to within 50%; we do not know the spread on LINK during a cascade to
within 50%; `synthetic_half_spread_bps: 3` is an assumption, not a measurement.
An edge that survives only the optimistic end of our own guesses is a bet on the
guess.

Note also what meanrev is NOT failing on: turnover (21 trades over 777 days is
~0.8 round trips/month, comfortably inside the ceiling of 8) or trade count. It
is a slow, selective strategy with a real gross edge. It is the best candidate
this project has produced in either asset class. It still does not pass.

### What the other four say

Three of the four have a **negative cost multiple** — no gross edge at all, so
the fees are not the problem, they are merely the visible part of it.

`tsmom` at 130% and `donchian` at 81% fees-as-%-of-gross are strategies whose
entire edge is consumed by the act of capturing it.

`xsmom` is the interesting failure: only 8% of gross went to fees, and it still
returned −9.16% with PF 0.164. Its problem is not cost, it is direction — and
with a 4-symbol universe, cross-sectional momentum is ranking almost nothing.
It should be re-run if the universe widens, and its verdict here treated as
uninformative rather than negative.

### Two constraints discovered, both recorded rather than worked around

**1. Kraken cannot supply gate data.** Its OHLCV endpoint returns ~720 candles
and does not paginate back. With 721 daily bars and a 0.7 split, OOS is 217 bars
— of which SMA200 spends 200 on warmup, leaving **17 tradeable days**. `xsmom`
gets zero. A gate run on that produces something that looks exactly like a
verdict and is noise.

Resolved by splitting provenance from execution: **gated on Coinbase (2765 bars,
7.5 years), traded on Kraken (80 bps round trip vs Coinbase's 120).** The
divergence this introduces is measured at build time and recorded in the
manifest: **3.0 bps max**, against a gate denominated in 80. Declared, bounded,
and auditable — not hidden.

**2. The plan's "≥3 years of history" universe rule was revised to 1000 bars.**
Not to fit a result: SOL, ADA, AVAX and DOGE returned no usable Coinbase daily
history through this path and were dropped with reasons; XRP had 694 bars and
was dropped. The four that remain are the four with depth.

### What happens next, and what must not

The correct response to "nothing passed" is a slower timeframe or a different
mechanism. It is **not** lowering the cost multiple to 1.7 so meanrev fits —
that number was written down in §1 before any data existed precisely so it could
not be moved afterwards.

Pre-registered candidates, in order:

1. **meanrev at a slower cadence.** Its gross edge is real ($191.73/trade). If
   fewer, larger, more selective trades raise the edge faster than they raise
   the cost, the multiple improves. This is a parameter re-gate, and it counts
   against the cumulative trial count.
2. **Widen the universe and re-run xsmom.** Its verdict here is uninformative.
3. **Maker orders.** The model carries `maker_bps: 25` and never applies it
   because every order is a market order. Limit entries would cut the round trip
   from 80 bps to 50 — which alone would move meanrev's stressed multiple above
   2.0. That is a real execution change with its own failure modes (unfilled
   orders, adverse selection) and needs its own gate, not an assumption.

Trial count after §4: **5**. Every future comparison corrects against it.

---

## §5 — The fee input was wrong. meanrev ENABLED, and its edge is still not proven

**Type: GATE (re-run of §4 against a corrected input) + EDGE claim.**

### The correction

§4 was run at `taker_bps: 40`, taken from a web search describing Kraken's FLAT
retail rate. Queried from the venue's own schedule via `ccxt.load_markets()`:

| | flat (what §4 used) | **tiered (what API spot pays)** |
|---|---|---|
| taker | 40 bps | **26 bps** at <$50k/30d |
| maker | 25 bps | **16 bps** |
| round trip | 80 bps | **52 bps** |

**§4 was run against a cost the bot would never actually pay** — pessimistic by
54%. Corrected to tier 0 deliberately: a new account's rate, not an aspirational
one. Volume tiers improve it (24 at $50k, 22 at $100k, 20 at $250k) and none of
that is assumed. `min_taker_bps` floor set to 20.

This is correcting an INPUT, not moving a threshold. The cost multiple stays at
2.0 and the stress arm stays mandatory. Before touching the fee number I ran a
sensitivity sweep so the correction could not be mistaken for a search for a
pass — meanrev clears the stressed arm at <=30 bps and fails at 35+, and 26 was
what the venue said, not what the sweep wanted.

### The re-run

| strategy | OOS ret | PF | trades | cost mult | fees/gross | verdict |
|---|---|---|---|---|---|---|
| ma_crossover | −6.57% | 0.738 | 49 | −2.66 | 38% | FAIL |
| tsmom | +2.54% | 1.197 | 36 | 2.80 | 36% | FAIL (PF < 1.3) |
| xsmom | −8.94% | 0.169 | 13 | −20.35 | 5% | FAIL |
| **meanrev** | **+3.18%** | **2.01** | **21** | **4.12** | **24%** | **PASS** |
| donchian | −1.53% | 0.792 | 14 | −1.89 | 53% | FAIL |
| *buy & hold* | *−30.73%* | | | | | |

meanrev clears every clause at BOTH arms. It beat buy-and-hold by 34 points in a
window where holding lost 30.7%, with a 71.4% win rate, a POSITIVE median trade
(+$130.20), and its top-3 trades are 48.3% of gross profit — not concentrated.
That last number matters: the equities audit found ma_crossover's profit factor
was 54.7% three trades, and this is not that.

### And it is still not proven

Moving-block bootstrap on per-trade P&L, Bonferroni-corrected at K=5:

    99% CI on the per-trade edge:  [−125.88, +437.31]
    significant: FALSE

**The interval straddles zero.** 21 trades cannot establish an edge, and the
point estimate being good does not change that. This is the same verdict the
equities audit reached across five strategies, arrived at honestly rather than
avoided.

### Enabled anyway — and exactly why that is not a contradiction

`meanrev` is set `enabled: true`. Three reasons, and the third is the real one:

1. It passed the **pre-registered deterministic gate**, which is this project's
   standing enablement rule. Refusing a strategy that cleared the rule written
   before the data would be moving the goalposts in the other direction.
2. **Nothing is at risk.** Repete1 has no exchange credential and fills are
   simulated. The cost of being wrong is a bad line in a ledger.
3. **Trading it is the only way to resolve the question.** An edge that cannot
   be distinguished from zero at n=21 needs more n, and more n only comes from
   trading. Leaving it off guarantees the CI never narrows — the strategy stays
   permanently unproven and permanently unfalsified, which is the worse outcome.

`risk.live_kill` is the pre-registered other side of this: >=15 live closed
trades at PF < 0.8 stops it ENTERING, exits unaffected. It was registered before
any strategy was near the threshold and applies here unchanged.

**What must NOT happen:** meanrev's live results being cited as confirmation
because they are positive. The CI above is the standing claim until enough
closed trades narrow it. Any future section reporting on meanrev must restate
this interval.

### The other four

`tsmom` is now the interesting one: +2.54% and cost multiple 2.80, failing only
on PF 1.197 < 1.3. At 36 trades it is the highest-n strategy here. It is NOT
enabled — the bar is the bar — but it is the second candidate if a re-gate is
ever run, and it moved from −2.04% to +2.54% purely on the fee correction.

`xsmom` remains uninformative: 5% of gross to fees means cost is not its
problem, and cross-sectional ranking across 4 symbols is barely ranking.

### Universe

`config.yaml` symbols set to the four that cleared admission: BTC/USD, ETH/USD,
LINK/USD, LTC/USD. Trial count after §5: **5** (this is a re-run of §4's arms
against a corrected input, not five new trials — the strategies tested are the
same five).

---

## §6 — The allocator (Phase 9). Built, tested, and switched OFF

**Type: COMPONENT, not a gate.** No strategy's status changed.

`src/allocator.py` is the numeric half of the brain. The hypothesis book plus
LLM judge already learned in WORDS and could only veto or downsize; this learns
in NUMBERS from closed trades and moves capital.

### The property that makes it safe

    mult = min(1, K * weight)

`weight` sums to 1 over K arms, so `K * weight` is a ratio-to-uniform. Clamping
at 1.0 makes it a **de-allocator**: the best arm gets exactly its
config-sanctioned size, worse ones get less, nothing gets more. It is applied in
`risk.size_order` **before** `ceiling = min(caps)`, so being <=1 and pre-caps it
cannot breach a rail however wrong it becomes. That is invariant #4 satisfied by
arithmetic rather than by review, and two tests pin the ordering.

### Design choices that are not arbitrary

* **Posterior, not a scoreboard.** Ranking arms by realized P&L is the standard
  way an adaptive allocator destroys an account: at n=5 it ranks noise, and it
  compounds — the lucky arm gets capital, which makes its next result louder. A
  posterior carries the uncertainty, so five good trades barely move the
  allocation and fifty do.
* **Prior centred at ZERO.** The honest reading of this project's evidence: the
  equities audit found no edge distinguishable from zero across five strategies,
  and §5 found meanrev's 99% CI straddling zero at n=21.
* **`pnl_pct`, never dollars.** Dollar P&L scales with position size, which this
  module controls — a downsized arm would look worse BECAUSE it was downsized,
  and the allocator would confirm its own decision.
* **Calendar-age discount, not per-trade.** Regime change is a calendar
  phenomenon; per-trade decay would make a fast strategy forget ten times
  quicker than a slow one for no reason.
* **Hash-seeded draws**, copied from `judge_model._uniform`: a PRNG sequence
  depends on how many draws preceded it, so live and sim would diverge the
  moment they evaluated a different number of arms. That is divergence #10.
* **Floor at 0.5x uniform.** Zeroing a strategy is NOT this module's job — that
  is `risk.live_kill`, a pre-registered rail, kept separate so a LEARNED
  quantity can never fully switch off a GATED one.

### The test that decides whether it ships

`test_null_control_does_not_lose_to_uniform`: 300 independent worlds, all arms
drawn from the SAME zero-edge distribution, future independent of history.
Thompson sampling still picks winners there — that is what sampling does. The
question is whether ACTING on those picks costs money. **If an allocator fed
pure noise underperforms uniform, it is a machine for converting randomness into
losses and must not ship, however elegant the maths.** It passes.

The safety tests were then verified by mutation: an unbounded, aggressive
variant (floor 0, ceiling 99x, multiplier x3) was substituted and three tests
failed — exactly the three guarding "can only shrink". The guarantee is
demonstrated, not asserted.

### Off, and why that is the correct state

`allocator.enabled: false`. It requires 20 effective trades per arm before an
arm participates at all, and below two eligible arms it returns EXACTLY uniform
without calling the sampler. Today one strategy is enabled with 21 out-of-sample
trades and no live ones. There is nothing to allocate between and nothing to
learn from.

It turns on when there is evidence to act on, and its own replay gate
(`allocator-on` vs `allocator-off` through `significance.compare`) must pass
first — the same discipline as any strategy.

---

## §7 — meanrev's PASS was measured on a universe produced by a bug. REVERTED.

**Type: GATE. Reverses §5.**

### The bug

`build_crypto_snapshot.py` walked pages forward from 2019-01-01 and treated an
empty page as end-of-data:

    if not got:
        break

An empty page does not mean "no data" — it means no data IN THIS WINDOW. Every
market listed after 2019 returns nothing for 2019, so the walk exited on its
first request. SOL, ADA, AVAX, DOGE, DOT, UNI and ATOM were reported as having
**zero bars** when they each have 1,700–2,400.

A second, smaller bug preceded it: symbols were mapped `BTC/USD -> BTC-USD` on
the assumption Coinbase needed its native dash format. ccxt normalises to
BASE/QUOTE, so only BTC resolved (by alias) and the rest silently missed.

**§4 and §5 therefore ran on four markets. The correct universe is twelve.**

The drops were reported WITH REASONS, which is the only thing that made this
findable — a silent omission would have been indistinguishable from a real
constraint, and the four-market result would have stood indefinitely.

### The corrected gate

Snapshot `ca82e795c5943e03`, 12 markets, >=1762 bars, IS 1233 / OOS 529.

| strategy | OOS ret | PF | trades | cost mult | verdict |
|---|---|---|---|---|---|
| ma_crossover | −10.59% | 0.369 | 23 | −11.57 | FAIL |
| tsmom | +0.36% | 1.016 | 60 | 1.15 | FAIL |
| xsmom | −11.55% | 0.476 | 32 | −8.70 | FAIL |
| meanrev | +2.56% | 1.353 | 30 | 2.71 | **FAIL** |
| donchian | −4.62% | 0.603 | 20 | −4.94 | FAIL |
| *buy & hold* | *−58.08%* | | | | |

meanrev fails the stress arm: PF 1.214 < 1.3 and cost multiple 1.72 < 2.0.

**ENABLED: NONE.** `meanrev` is set back to `false`.

### Why the wider universe made it worse

Not noise — dilution. meanrev went from 21 trades to 30 while its gross edge per
trade fell from $191.73 to $128.85. The eight added markets are thinner and
more erratic than BTC/ETH/LINK/LTC, and the strategy took more trades of lower
quality. Turnover rose, edge per unit of turnover fell, and the cost multiple
followed.

### The temptation, named so it can be refused

The four-market universe is sitting right there, and meanrev passes on it.

**That universe was produced by a bug.** Selecting it now would be choosing the
data that gives the answer I want, which is the single most consequential thing
this project exists to prevent. The equities history has the precedent exactly:
§20a was adopted on numbers measured in the wrong symbol order, stood four
hours, and was reverted by §22 — and the note there reads "the owner had
approved it on numbers I measured wrong."

The admission rule (>=1000 bars, >=$1m/day) was pre-registered. Twelve markets
satisfy it. Twelve is the universe.

### What this changes about the earlier sections

* **§5's PASS is void.** meanrev was enabled on 2026-07-27 and disabled the same
  day. It never traded — no live trade was taken under the void verdict.
* **§4's "nothing passed" was right for the wrong reason** (it used the wrong
  fee AND the wrong universe). §7 is the first verdict with both inputs correct.
* **§5's significance finding stands and is reinforced.** The 99% CI on
  meanrev's per-trade edge straddled zero at n=21; at n=30 on the correct
  universe it does not even clear the deterministic gate.

### xsmom is now informative, and the news is bad

At four markets its verdict was uninformative — cross-sectional ranking across
four names is barely ranking. At twelve it has a real cross-section, 32 trades,
and returns **−11.55% with PF 0.476**. Only 12% of gross went to fees, so cost
is not the problem: the signal is. That is a genuine negative result rather than
an absence of one.

### Standing position

**No strategy in this project has passed a correctly-specified gate.** Five
arms, two asset classes, and the honest count of demonstrated edges is zero.

Remaining pre-registered candidates, unchanged:
1. **maker orders** — 52 bps round trip becomes 32, which would move meanrev's
   stressed multiple above 2.0. It needs its OWN gate: a limit order that does
   not fill is not a cheaper trade, it is a different strategy, and assuming
   100% maker fills is exactly the optimism that produces unreproducible
   backtests.
2. **meanrev parameter re-gate on crypto data** — its params are still the
   equities RSI(2)/SMA200 values, never re-derived. This is the most likely
   source of a real improvement and has not been attempted.
3. **4h timeframe** — takes ~6x the round trips and must find ~6x the edge.

Trial count after §7: **5** (the same five arms, re-measured on corrected
inputs — not new trials).

---

## §8 — The parameter re-gate. Searching made it worse. REJECT.

**Type: EDGE claim, declared before the run. Pre-registered in
`scripts/regate_meanrev.py`, committed with the procedure written above the
numbers.**

meanrev's parameters were still the equities RSI(2)/SMA200 values, never
re-derived on crypto data. §7 named this the most promising untried candidate.
It was tried. It failed, and the way it failed is the useful part.

**Grid:** 36 variants — `rsi_buy_below` (5/10/15/20) x `trend_sma_period`
(50/100/200) x `max_hold_days` (3/7/14). `rsi_period` held at 2 and
`exit_sma_period` at 5, because Connors' RSI-2 IS the mechanism and varying it
would be testing a different strategy under the same name.

**Procedure:** winner picked IN-SAMPLE ONLY, validated out-of-sample ONCE.

### In-sample top five

| params | IS return | PF | trades |
|---|---|---|---|
| **rsi<20, SMA200, hold 7** | **+10.15%** | 1.256 | 107 |
| rsi<20, SMA200, hold 14 | +8.39% | 1.211 | 105 |
| rsi<15, SMA200, hold 7 | +6.28% | 1.161 | 95 |
| rsi<15, SMA200, hold 14 | +4.76% | 1.117 | 96 |
| rsi<15, SMA200, hold 3 | +4.66% | 1.092 | 129 |

### Out of sample, once

| | |
|---|---|
| return | **−7.29%** (buy & hold −58.08%) |
| PF | 0.611 |
| trades | 49 |
| cost multiple | −2.10 (stressed −1.49) |
| deterministic gate | **FAIL** |
| EDGE test, Bonferroni K=41 | CI [−591.67, +310.98], **not significant** |

**VERDICT: REJECT.**

### What actually happened, and why it is instructive

Look at which variant won in-sample: **`rsi_buy_below: 20`, the LOOSEST
threshold in the grid.** Relaxing "how deep a dip must be" from 10 to 20 buys
far more dips — 107 in-sample trades against the default's ~60 — and more trades
means more opportunity to fit in-sample noise. It scored best precisely because
it was the least selective.

Out of sample that reverses completely: −7.29% at PF 0.611.

**The un-searched equities default scored +2.56% on the same out-of-sample data
(§7).** Thirty-six variants of searching produced a parameter set materially
WORSE than not searching at all. That is the False Strategy Theorem in one
table, and it is the reason this project logs every variant tried and raises the
correction bar with the trial count rather than reporting the best number found.

### The cost of having looked

The cumulative trial count goes from 5 to **41**. Every future EDGE claim in
this project is now corrected against 41 trials, not 5 — a permanently higher
bar, paid for by this search, and it applies whether or not the search found
anything. That is the honest accounting: you cannot search for free and then
report the winner as though you had guessed it first.

### Standing position, unchanged and now better evidenced

**No strategy in this project has passed a correctly-specified gate.** Five
arms, 36 parameter variants, two asset classes. Zero demonstrated edges.

Of the three candidates §5 pre-registered:

1. ~~wider universe~~ — tried in §7. Diluted rather than helped: more trades,
   lower edge per trade.
2. ~~parameter re-gate~~ — tried here. Overfit; worse than the default.
3. **maker orders** — still untried, and now the only one left. It would cut the
   round trip from 52 bps to 32, which is a real mechanical improvement rather
   than a search. But it requires a FILL-PROBABILITY assumption: a limit order
   that does not fill is not a cheaper trade, it is a different strategy, and
   assuming 100% maker fills is exactly the optimism that produces backtests
   nobody can reproduce live. Gating it honestly needs order-book data this
   project does not currently collect.

### The conclusion this log now supports

The evidence says these five strategies, on daily crypto bars, at a 52 bps round
trip, do not have an edge. That is a finding, not a failure of the search. The
machinery built here — the frozen snapshot, the cost-stressed gate, the trial
counter, the significance correction — exists to produce exactly this answer
cheaply and early, instead of a drawdown producing it slowly and expensively.

What would change the answer is a different MECHANISM, not another parameter:
maker execution, a slower timeframe, or a signal none of these five expresses.
Each needs its own pre-registration.

---

## §9 — Maker entries. Best deterministic result yet, and still REJECT.

**Type: EDGE claim, pre-registered in `scripts/gate_maker.py` with the fill rule
and the expectation written above the numbers.**

The last of the three candidates §5 named. A taker buy crosses the spread at 26
bps; a maker buy rests at the bid at 16 bps — a 32 bps round trip instead of 52.

**The fill rule, modelled from bars rather than assumed:** a limit buy placed at
the bid on bar *i* fills IFF bar *i+1*'s LOW reaches it. No fill-rate parameter
to tune; the price path decides.

### Result

| | taker (§7) | **maker 1.0x** | maker 1.5x |
|---|---|---|---|
| return | +2.56% | **+5.06%** | +4.28% |
| PF | 1.353 | **1.636** | 1.522 |
| trades | 30 | 48 | 48 |
| win rate | — | 67% | 67% |
| signals missed | — | 2% | 2% |

**Nearly double the return, PF up from 1.353 to 1.636, and it survives the
stress arm.** The best deterministic numbers this project has produced.

    EDGE test, Bonferroni K=42: CI [-192.30, +459.46]  not significant

**VERDICT: REJECT.**

### My prediction was wrong, and the way it was wrong matters more than the result

I predicted heavy adverse selection: a passive bid on a dip should fill when
price keeps falling and miss when it bounces, systematically costing a
mean-reversion strategy its winners. I expected the lost signals to cost more
than the 20 bps saved.

**Only 2% of signals were missed.** That is not adverse selection being absent —
it is my limit being placed too aggressively to be a real maker order. The bid
here is `close x (1 - 3bps)`, three basis points under the signal bar's close,
and in crypto's volatility the next bar reaches three bps below the prior close
almost always. **I modelled an order that pays maker fees while behaving like a
taker.** That is not a maker strategy; it is a fee assumption wearing one.

A real resting bid sits at the actual book bid, which moves, can be several bps
away, and gets queued behind other orders. Modelling that needs order-book data
this project does not collect. So the +5.06% is not wrong arithmetic — it is
arithmetic about an order that would not exist.

**It fails the edge test anyway**, which is why the verdict is REJECT rather
than "promising but unmodelled". Both reasons stand independently.

### Where this leaves the programme

All three pre-registered candidates are now exhausted:

1. ~~wider universe~~ (§7) — diluted
2. ~~parameter re-gate~~ (§8) — overfit, worse than the default
3. ~~maker entries~~ (§9) — best numbers, unrealistic fill model, still fails

**Standing position: no strategy in this project has passed a
correctly-specified gate.** Five arms, 36 parameter variants, one execution
change, two asset classes, cumulative trial count 42. Zero demonstrated edges.

### What would actually be next, stated so nobody has to guess

Maker execution is the most promising direction found and deserves a real
attempt, but a real attempt starts with DATA, not another backtest:

1. **Collect order-book snapshots** at the decision cadence for the twelve
   markets — top-of-book bid/ask and depth, stored alongside the bar snapshot.
   This is weeks of passive collection and needs no trading.
2. **Re-run §9 against observed books**, with the limit at the real bid and fills
   determined by whether the book traded through it.
3. Only then is the fee saving separable from the fills it costs.

Everything else — a slower timeframe, a different signal family — is a new
mechanism and needs its own pre-registration and its own section. The trial
counter is at 42 and every future EDGE claim pays that correction.

---

## §10 — Volatility targeting. The research was right about the direction and it still is not enough. REJECT.

**Type: EDGE claim, pre-registered in `scripts/gate_voltarget.py`.**

The one mechanism the crypto literature points at hardest — risk-managed
momentum — and the one this project had never tested. `risk.vol_scale` existed
and sat disabled since the fork. A within-strategy variant (same signals, same
entries, same exits; only SIZE changes), so 3 trials, not a new family.
`max_scale` capped at 1.0: de-lever only, because vol targeting that levers UP
into low-vol regimes is how a vol-managed strategy becomes a leveraged one at
the worst moment.

| strategy | arm | return | PF | maxDD | n | cost mult |
|---|---|---|---|---|---|---|
| meanrev | baseline | +2.56% | 1.353 | 3.74 | 30 | 2.71 |
| meanrev | vol_target 0.40 | +2.56% | 1.353 | 3.74 | 30 | 2.71 |
| meanrev | vol_target 0.60 | +2.56% | 1.353 | 3.74 | 30 | 2.71 |
| **tsmom** | baseline | +0.36% | 1.016 | 11.14 | 60 | 1.15 |
| **tsmom** | **vol_target 0.40** | **+1.21%** | 1.081 | **8.30** | 71 | **1.67** |
| **tsmom** | **vol_target 0.60** | **+1.91%** | 1.091 | 10.29 | 67 | **1.79** |
| donchian | baseline | −4.62% | 0.603 | 11.90 | 20 | −4.94 |
| donchian | vol_target 0.40 | −2.66% | 0.663 | **8.10** | 23 | −3.75 |
| donchian | vol_target 0.60 | −2.68% | 0.712 | 10.10 | 21 | −2.84 |

**NOTHING CLEARED. REJECT.**

### The literature was right about the direction

On tsmom, vol targeting improved **every metric simultaneously**: return
+0.36% → +1.91%, PF 1.016 → 1.091, drawdown 11.14 → 8.30, cost multiple
1.15 → 1.79. That is not a tradeoff — it is more return at less risk and better
cost efficiency, which is exactly what "volatility management is what makes
crypto momentum survivable" predicts. Same on donchian, from a deeply negative
base.

It is still not enough. tsmom's cost multiple reaches 1.79 against a 2.0 bar.

### One arm was never actually tested, and that is a finding

**vol_target is INERT on meanrev** — identical numbers across all three rows.
`risk_sizing` supersedes it for that strategy (the equities config records the
supersession: both normalise by realized vol and compounding them would
double-count). So the row reading "vol_target 0.40" on meanrev is measuring the
baseline. Recorded rather than quietly dropped, because three identical rows in
a results table are exactly what a silent no-op looks like.

### The search is over

Four candidates, all pre-registered, all run to completion:

| § | candidate | outcome |
|---|---|---|
| 7 | wider universe | diluted — more trades, less edge per trade |
| 8 | parameter re-gate | overfit — 36 variants beaten by not searching |
| 9 | maker entries | best numbers, unrealistic fill model, fails edge test |
| 10 | volatility targeting | right direction, insufficient magnitude |

Cumulative trial count: **45**. Every future EDGE claim is corrected against 45
trials.

**And that number is now the argument for stopping.** Each additional search
raises the bar for everything that follows, so continued searching against this
snapshot is not neutral — it actively makes a real edge harder to demonstrate.
The False Strategy Theorem is not a formality here; §8 measured it directly, in
a search that produced something worse than not searching.

### The standing conclusion

**These five strategies, on daily crypto bars, at a 52 bps round trip, do not
have an edge that this data can demonstrate.** Five arms, 36 parameter variants,
one execution change, one sizing overlay, two asset classes, 45 trials, zero
demonstrated edges.

That is a finding. Producing it cost weeks of compute and no capital, which is
what the frozen snapshot, the cost-stressed gate, the trial counter and the
significance correction were built to do.

### What would change it — and none of it is another backtest

1. **Order-book data.** §9 is the most promising mechanism found and is
   currently unmodellable. Weeks of passive collection, no trading, no risk.
2. **A different signal family.** All five arms are price-only. Nothing here
   reads funding, basis, on-chain flow or order-flow imbalance — the things the
   crypto literature actually attributes edge to.
3. **More history.** 529 OOS bars across 12 markets is thin for a 45-trial
   correction. This grows on its own.

Repete1 ships with `enabled: NONE` and that is the correct state, not a failure
to finish.

---

## §11 — PRE-REGISTRATION. Funding-rate entry filter on meanrev. Written before the run.

**This section was committed BEFORE the gate was executed.** Check the git history:
the commit that adds this text contains no results, and the commit that adds
results does not modify this text above the RESULTS heading.

### What the §10 diagnostic actually showed, and why it redirects the search

Ten sections of "fail" hid a distinction I had not reported precisely. Running
`enablement_gate` and printing the REASONS, rather than the boolean:

    meanrev  1.0x fees: PASS  ret +2.56%  PF 1.353  n 30  cm 2.71  (B&H -58.08%)
    meanrev  1.5x fees: FAIL  ret +1.84%  PF 1.246  n 30  cm 1.82
             - OOS profit factor 1.246 < 1.3
             - cost multiple 1.82 < 2.0 (fees are 55% of gross)

**meanrev clears the entire deterministic gate at the real Kraken fee schedule.**
It is in the market 1.2% of the time and returned +2.56% across an OOS window in
which buy-and-hold lost 58%. It fails only the 1.5x fee stress arm, and there it
misses by 0.054 on PF and 0.18 on cost multiple.

The stress arm is not being relaxed. It was pre-registered in §1, 26 bps x 1.5 is
approximately Kraken's worst retail tier, and "an edge that dies at 1.5x cost was
a measurement of the fee schedule" is correct. But it names the binding
constraint exactly: **meanrev's problem is gross edge per trade versus cost, not
signal direction.** It needs roughly 10% more edge per trade. That is a filter
problem, and it is the first time in eleven sections the target has been this
specific.

### The hypothesis

Every arm in this repo is PRICE-ONLY. 45 trials, five strategies, and not one
reads anything but OHLCV. The crypto literature does not put edge there; it puts
it in funding and basis, which measure what price cannot — how much leveraged
positioning is stacked on one side and what it costs to hold.

    H: meanrev buys dips. A dip bought while perpetual funding is extremely
       positive is a dip bought into a crowded, levered long book, where the
       marginal seller is a liquidation rather than a discretionary trader.
       Those entries should be disproportionately bad. Removing them should
       raise gross edge per trade and therefore the cost multiple.

Repete1 trades SPOT, long/flat, and will never hold a perp. Funding enters as an
INPUT. The trading surface does not change.

**CLAIM TYPE: EDGE.** CI must exclude zero at the cumulative trial count.

**It is a within-strategy FILTER, not a sixth arm** — same signals, same exits,
same sizing, a veto on entry only. Three thresholds tested, so **3 trials.
Cumulative K after this run: 48.**

### Data, frozen and hashed

`data/funding_20260727.json.gz`, sha256 `a2ee0d7f8abceaa3...`, manifest at
`data/FUNDING_MANIFEST.json`. Binance USDT-margined perps, 12 symbols, 2019-09-10
onward. Provenance is split a second time and declared: bars from Coinbase,
funding from Binance, execution on Kraken. Kraken reports
`fetchFundingRateHistory: False` and cannot be the source.

**The look-ahead rule is the whole ballgame.** Funding pays at 00:00/08:00/16:00
UTC; bars are stamped with their OPEN time, so bar D closes at D+1 00:00.

    funding_by_date[D] = sum of payments in [D 00:00, D+1 00:00)

Every payment in that window has settled by the instant bar D closes, and not one
second later. `test_funding_has_no_lookahead` pins it.

### Exactly what is being tested, fixed now

- **Signal** `f_t` = mean of `funding_by_date` over the trailing **3 days ending
  at the bar's own date, inclusive**. Three days is one full cycle of payments,
  chosen to smooth 8h noise; no other window is tested.
- **Threshold** `θ` ∈ {p80, p90, p95} of the trailing-3-day funding distribution
  computed on the **IN-SAMPLE window only**, pooled across symbols. The RULE is
  pre-registered here; the numeric value is derived from IS data and is therefore
  not contaminated by the OOS result.
- **Action** if `f_t > θ` at a bar where meanrev would enter, the entry is
  vetoed. Exits, stops, trails and sizing are untouched.

### Falsification criteria, declared before the numbers

The filter is ADOPTED only if **all** of:

1. Both fee arms pass `enablement_gate` — the 1.5x arm must reach PF ≥ 1.3 **and**
   cost multiple ≥ 2.0. Passing the 1.0x arm alone is what meanrev already does
   and is not news.
2. `n_trades` stays ≥ 15 at both arms. A filter that "passes" by shrinking the
   sample below the floor has not found anything.
3. Cost multiple RISES relative to unfiltered meanrev. If n falls and the cost
   multiple does not rise, the filter is cutting trades at random — **REJECT**.
4. The EDGE test at K=48 excludes zero.

### The negative control, which decides whether any of this is real

The mirror arm: veto entries when funding is **extremely NEGATIVE** (`f_t < ` the
IS p05/p10/p20). Under H that is the *favourable* state — capitulation, shorts
paying longs — so blocking it should make results **worse**.

**If the negative-tail filter improves the cost multiple by a comparable amount,
the positive-tail result is INVALIDATED** and the honest reading is that any
filter reducing trade count flatters a cost-multiple metric. Declaring this now,
because it is the single most likely way for this section to fool me, and a
control that is only examined when the headline result is disappointing is not a
control.

The control arms are controls, not candidates. They do not increment K, and a
PASS on a control arm cannot be adopted — it can only invalidate.

### Honest expectation

meanrev needs about 10% more gross edge per trade at the stress arm. If funding
carries real information about which dips are traps, removing the worst decile of
entries should clear that comfortably. If it moves the cost multiple by a few
percent, the signal is not there and eleven sections is the answer.

### §11 RESULTS — the control fired. REJECT.

```
arm                        ret     PF    n      cm |     ret     PF    n      cm | cover veto  gate
                           ---- 1.0x fees ----      |     ---- 1.5x fees ----      |
baseline (no filter)     +2.56  1.353   30    2.71 |   +1.84  1.246   30    1.82 |   —    0v   fail
CANDIDATE above p80      +3.11  1.427   30    3.06 |   +2.34  1.311   30    2.04 | 100%   2v   PASS
CANDIDATE above p90      +2.56  1.353   30    2.71 |   +1.84  1.246   30    1.82 | 100%   0v   fail
CANDIDATE above p95      +2.56  1.353   30    2.71 |   +1.84  1.246   30    1.82 | 100%   0v   fail
CONTROL   below p20      +4.33  2.064   26    4.32 |   +3.69  1.862   26    2.89 | 100%  24v   PASS
CONTROL   below p10      +2.56  1.353   30    2.71 |   +1.84  1.246   30    1.82 | 100%   0v   fail
CONTROL   below p05      +2.56  1.353   30    2.71 |   +1.84  1.246   30    1.82 | 100%   0v   fail
```

IS percentiles, bps/day: p05 −3.83  p10 −1.37  p20 +0.47  p80 +5.56  p90 +12.51  p95 +20.84

**The candidate passed.** `block_above p80` cleared BOTH fee arms — the first arm
in this entire programme to do so. Stress cost multiple 1.82 → 2.04, stress PF
1.246 → 1.311, both over the bar meanrev has been missing since §1.

Without the pre-registered control this section would be reporting Repete1's
first enabled strategy.

**The control destroyed it.** `block_below p20` blocks entries in what §11 called
the FAVOURABLE state — capitulation, shorts paying longs. Under the hypothesis it
should have made things worse. It produced a stress cost multiple of **2.89**
against the candidate's 2.04, and PF 2.064 against 1.427.

A filter that is *more* effective when pointed backwards is not measuring what it
claims to measure. Invalidated, by a rule written down before the run.

### Three things the coverage counter caught that the summary table would have hidden

1. **p90 and p95 vetoed ZERO entries.** Two of three candidate arms were
   completely inert — the OOS window never saw funding above IS p90 at a meanrev
   entry bar. Their identical-to-baseline rows are not weak evidence of no
   effect; they are no evidence at all. Without the veto count they would have
   read as two independent confirmations.
2. **The candidate's entire result is 2 trades.** 2 vetoes out of 30. A gate
   cleared by removing two observations at a cumulative trial count of 48 is a
   coin flip that landed well, and it would have been reported as a PASS.
3. **Coverage was 100%.** The fail-open path never fired, so for once nothing is
   hiding there.

### The EDGE test rejects everything anyway, including the control

```
baseline       n= 30  mean $ 85.35  CI[-253.52, +543.73]  significant=False
CANDIDATE p80  n= 30  mean $103.75  CI[-254.87, +550.23]  significant=False
CONTROL   p20  n= 26  mean $166.49  CI[-167.63, +628.12]  significant=False
```

Criterion 4 fails independently of the control. At K=48, n≈30 cannot resolve an
edge of this size — the intervals are an order of magnitude wider than the means.

### What the control probably means, and why it is not being adopted

The honest reading of a control that works backwards is not "noise". It is that
**funding carries information about meanrev entries with the OPPOSITE sign to
§11's hypothesis**: dips are worse to buy when funding is negative (a genuine
bear, shorts in control, a falling knife) and better when funding is normal-to-
positive (intact bull structure where dips get bought). That is a more sensible
market story than the one pre-registered, which is exactly what makes it
dangerous.

It is not being adopted, for three reasons:

- **Reversing a hypothesis after seeing the data is the canonical overfit.** §8
  measured this project doing it: the in-sample winner scored +10.15% IS and
  −7.29% OOS, worse than not searching. Adopting the control turns it into a
  post-hoc selected 7th arm, and the correction bar rises to match.
- **It may be a worse copy of something meanrev already has.** meanrev runs
  `trend_sma_period`. If negative funding ≈ downtrend, the control is a noisier
  duplicate of an existing filter, and its apparent gain is that filter's gain
  measured twice.
- **Its own CI straddles zero.** Whatever it is, this data cannot show it.

**Recorded as a pre-registerable hypothesis for FRESH data, not a result:**

> H(§12, on data not yet collected): meanrev entries taken while trailing-3d
> perp funding is below its in-sample p20 underperform those taken above it.
> Tested only on bars after 2026-07-27, which no run in this log has touched.

That is a real, falsifiable, cheap claim. It costs nothing but waiting, and
waiting is the only thing that makes it evidence rather than a seventh search of
the same 588 bars.

### Standing position after §11

Cumulative trial count **48**. Twelve sections, five arms, 36 parameter variants,
one execution change, one sizing overlay, one non-price input. Zero adopted.

The one thing that changed: **meanrev is no longer "no edge".** It passes the
full deterministic gate at the real Kraken fee schedule (+2.56% against a −58%
buy-and-hold, in the market 1.2% of the time) and fails only the 1.5× stress arm,
by 0.054 on PF and 0.18 on cost multiple. That is a specific, named, 10%-of-edge
gap — not the diffuse "nothing works" of §7–§10. It stays disabled, because the
stress arm is the rule that stops a fee-schedule measurement being mistaken for
an edge, and it was pre-registered in §1.

---

## §12 — meanrev ENABLED IN PAPER. An owner decision, not a gate pass.

**What was decided.** `meanrev.enabled: true`, `mode: paper`, no exchange
credential, no capital at risk.

**What was NOT decided.** The stress arm was not relaxed. No gate code changed.
`enablement_gate` still returns FAIL for meanrev at 1.5× fees, and
`scripts/gate_funding.py` still prints that failure. Re-running any gate in this
log reproduces its recorded verdict exactly.

### The gap, stated precisely, because it is the whole basis of the decision

```
1.0x fees (Kraken's real schedule)   PASS   +2.56%  PF 1.353  n 30  cm 2.71
1.5x fees (pre-registered stress)    FAIL   +1.84%  PF 1.246  n 30  cm 1.82
                                            need PF 1.300           need 2.00
```

Short by **0.054 on profit factor and 0.18 on cost multiple**. For scale: the
buy-and-hold over the same window was **−58.08%**, and meanrev held a position
1.2% of the time.

The stress arm exists because "an edge that dies at 1.5× cost was a measurement
of the fee schedule." That reasoning is sound and it is why this is not being
called a pass. But it is a *margin of safety*, chosen in §1, not a fact about the
market — and the appropriate margin when the position size is zero dollars is a
different question from the appropriate margin for real capital.

### Why paper trading is the right way to resolve this and another backtest is not

The programme has extracted everything 588 OOS bars can honestly give. Trial
count is 48; each further search of the same snapshot raises the correction bar
for everything after it, and §8 measured that cost directly.

Forward paper trading has the opposite property. **It generates observations that
no gate in this log has seen, at a trial count of zero, at no risk.** It is the
only remaining action that makes the evidence base larger instead of the
significance bar higher.

It also does three things the snapshot cannot:
- tests the stress-arm gap against **realized** fills, spreads and fees rather
  than a modelled 26 bps — the cost model is the least trustworthy part of any
  crypto backtest, and this measures it
- gives the discounted-Thompson allocator its first real posterior input
- collects the forward funding record §12's hypothesis needs (see below)

### PRE-REGISTERED KILL CRITERIA — checkable from the ledger, no judgement call

Written before the first paper trade. Any ONE triggers `enabled: false`:

| # | trigger | why |
|---|---|---|
| 1 | forward closed trades ≥ 30 **and** realized PF < 1.0 | losing money forward at the sample size the gate itself used |
| 2 | forward closed trades ≥ 30 **and** realized cost multiple < 1.5 | below even the stress arm's 1.82 — the modelled cost was optimistic |
| 3 | equity drawdown > 10% from high-water mark | already a hard rail (`risk.max_drawdown_pct`); restated because a rail nobody wrote down is a rail nobody checks |
| 4 | any parity-harness failure | divergence #10. Non-negotiable and immediate. |
| 5 | realized vs modelled slippage diverges > 15 bps on a 20-fill rolling median | the fill model is wrong, so every number in this log is wrong |

**Review date: 2026-10-27** (90 days), or at 30 forward closed trades, whichever
comes first. At 1.2% deployment and the observed trade rate, 30 trades is likely
the later of the two — which is itself worth knowing before the clock starts.

### The forward hypothesis this makes testable

Restating §11's successor so it is registered before any data exists:

> **H(§12):** meanrev entries taken while trailing-3d perp funding is below its
> in-sample p20 (+0.47 bps/day) underperform those taken above it.
> **Tested only on bars after 2026-07-27.** No run in this log has touched them.

`scripts/collect_funding.py` runs daily at 04:00 UTC and appends to
`data/funding_live.jsonl`. It is **observe-only**: the trading loop does not
import it, does not read its output, and has no funding dependency —
`config.funding.enabled` is false and §11's tests pin that an unset threshold
never blocks. Putting a live Binance call in the decision path would buy a new
outage class for a hypothesis that is not yet evidence.

### What this is not

Paper P&L is not profit. It is a simulated fill against a real quote, and its
honesty is bounded by `src/fills.py` — which is exactly why kill criterion 5
measures that model against reality rather than trusting it.

Going live remains a **separate decision** governed by
`docs/go_live_checklist.md`, which still requires a clean two-arm pass. Nothing
in this section is evidence for it, and the config comment says so.

---

## §13 — A 905-day hole in XRP that every gate since §7 measured through

**Type: METHOD. No strategy's status changed. Trial count unchanged at 48.**

The test suite had 968 tests and **not one opened the frozen snapshot.** Every
test that touches bars builds its own, and a fixture constructed by the test
cannot disagree with the test's assumptions. So the question that actually
matters — what does the SHIPPED config ask the REAL venue for, against the REAL
data — had no coverage.

That is why `timeframe: '1Day'` (Alpaca's format, on a ccxt venue) reached
production on 2026-07-27, produced 24 `data_error` records and a
`stale_data_abort`, and was caught by a live cycle rather than by CI.

`tests/test_against_real_bars.py` closes it. **It found a second defect on its
first run.**

### The finding

```
XRP/USD  1805 bars   2019-02-26 .. 2026-07-27
  GAP at index 694:  2021-01-19 -> 2023-07-13   (905 days, ~904 bars missing)
    before: 694 bars      after: 1111 bars
```

Every other symbol is clean — max gap 1.0 days across the other eleven.

This is not a fetch bug. It is the **SEC lawsuit**: Coinbase suspended XRP
trading in January 2021 and relisted it in July 2023 after the Ripple ruling.
The venue genuinely has no bars for that window.

### Why it is tolerated rather than fixed, and what it does cost

The walk-forward split lands at index 1263 (2025-02-01), so:

```
OOS window   index 1263..1804   2025-02-01 .. 2026-07-27   entirely post-relisting
```

**Every OOS bar is on the clean side of the gap.** The out-of-sample numbers
this log reports for §7 through §11 are measured on contiguous series and stand.

The gap is entirely IN-SAMPLE, and in-sample is where parameters get chosen. So
it can bias:

* **§8's parameter search** — the 36-variant sweep picked its winner on IS data
  in which XRP's SMA200 spanned a 905-day discontinuity. A "200-day average"
  computed over three calendar years is not what its name says. §8 was REJECTED
  anyway, on OOS evidence, so the conclusion is unaffected.
* **§11's IS funding percentiles** — p05/p10/p20/p80/p90/p95 were derived from
  in-sample data including that XRP stretch.

Rebuilding the snapshot to drop or truncate XRP would change its SHA and make
every recorded verdict in this log unreproducible. That trade is not worth it
for a defect that does not touch the reported numbers. **The gap is recorded,
pinned by a test, and named in `KNOWN_GAPS`.**

### What the tests now enforce

| Test | Property |
|---|---|
| `test_every_shipped_timeframe_is_one_the_venue_accepts` | Both config keys that reach `venue.bars` hold a value `venue/market.py` will accept. This is the `'1Day'` outage as a unit test. |
| `test_the_two_timeframe_keys_agree` | `cfg["venue"]["timeframe"]` and `cfg["strategy"]["timeframe"]` feed the same method from different sections and nothing required them to agree. A mismatch raises nowhere — it silently compares a strategy to a benchmark on a different clock. |
| `test_the_out_of_sample_window_is_contiguous` | The load-bearing one. An IS hole biases what you pick; an OOS hole invalidates what you report. |
| `test_no_undocumented_gap_appears_anywhere` | Full-series contiguity with the one exception named. §7's snapshot builder already regressed once by treating an empty page as end-of-data. |
| `test_the_known_gap_is_still_where_we_think_it_is` | Pins the exception. A tolerated gap that is never re-measured is how "we know about that one" becomes cover for a second one nobody knows about. |

### The method lesson

**A test suite that only reads fixtures it wrote is measuring its own
assumptions.** 968 green tests, 21,144 real bars on disk, and the two defects
that reached production were both in the space between them — one caught by a
live cycle, one caught the first time a test finally opened the file.

Also renamed `test_shipped_config_runs_a_real_cycle.py` →
`..._runs_a_cycle_on_synthetic_bars.py`. It never ran a real cycle. The name
read like the missing coverage, which is worse than having no test at all,
because it stops anyone looking for the real one.

---

## §14 — PRE-REGISTRATION: is xsmom's lookback on the wrong side of a sign flip?

**Written before the run. The commit that adds this text contains no results.**

### The hypothesis

`xsmom` ranks the universe on **231 bars with a 21-bar skip** — the classic
Jegadeesh/Titman **12-1** formation. Its own config comment cites that 1993
paper, which is about **US equities**.

The crypto literature does not put momentum there. Liu & Tsyvinski find crypto
time-series momentum at a **one-to-four week** formation horizon, and the
cross-sectional work finds **significant reversal beyond one month**. On that
reading, 231 bars is not a weak momentum signal — it is a momentum signal
**aimed into the reversal zone**, which would explain §7's −11.55% better than
"no edge exists" does.

**H(§14): ranking on 7, 14 or 28 bars produces a materially different — and
less negative — OOS result than ranking on 231.**

### What is being changed, and what is not

Arms: `rank_lookback_bars` ∈ {7, 14, 28} against the shipped 231.

`skip_bars` goes to **0** on the candidate arms. This is not a second free
parameter being tuned — skipping 21 bars on a 7-bar formation would rank on
returns from 28 to 21 days ago, which is incoherent. The skip exists to dodge
equities' one-month reversal and is part of the 12-1 convention; the crypto
momentum specification does not carry it. The baseline keeps (231, 21) exactly
as shipped.

Everything else is untouched: `buy_top_fraction: 0.25`,
`exit_below_fraction: 0.50`, the frozen snapshot `ca82e795c5943e03`, the same
walk-forward split, the same two fee arms.

**THREE ARMS, DECLARED NOW, NO SWEEP.** §8 is the standing evidence for why:
36 variants produced an in-sample winner that scored −7.29% OOS, worse than not
searching at all. If none of 7/14/28 clears, the answer is that the horizon was
not the problem — not that a fourth number should be tried.

### Trial accounting

Within-strategy variants: **+3. Cumulative K after this run: 51.** Every EDGE
claim from here is corrected against 51, α = 0.05/51 = 0.00098.

### The negative control, declared in advance

Run the **reversed** rule at the same horizons: buy the BOTTOM quintile instead
of the top, everything else identical.

* If the candidate beats baseline and the control does not, that is evidence for
  short-horizon cross-sectional **momentum**.
* If the **control beats the candidate**, the signal at these horizons is
  **reversal**, not momentum — the candidate's result would be an artifact of
  the ranking direction, and per §11's rule a control that passes harder than
  the candidate **invalidates it**.
* A control PASS is never adoptable. It can only invalidate — or, here, redirect
  to §15.

That second outcome is the more interesting one and it is written down **before**
the numbers, so it cannot be claimed as a discovery afterwards. It is also
exactly what the reversal literature predicts, which is why §15 (cross-sectional
reversal as its own strategy) is already scoped.

### Falsification criteria — all must hold to adopt

1. Both fee arms pass `enablement_gate` (1.0× and 1.5×).
2. `n_trades ≥ 15` at both arms.
3. Cost multiple ≥ 2.0 at both arms.
4. Turnover ≤ 8 round trips/month.
5. Bootstrap CI on per-trade P&L excludes zero at **K=51**.
6. The negative control does **not** outperform the candidate.

**The 1.5× stress margin does not move.** It was fixed in §1 before any data
existed, precisely so it could not be moved after.

### Predicted outcome, stated so being wrong is visible

I expect the short horizons to beat 231 — the horizon argument is well
evidenced — but I expect **all four arms to fail the deterministic gate**, and I
think the **control is more likely to pass than the candidate**, because the
cost literature is more confident about reversal surviving fees than about
momentum. If the candidate passes cleanly and the control does not, my reasoning
about which direction the signal runs was wrong, and that will be recorded.

---

## §14 RESULT — REJECT. And the sign flip is real, pointing the other way.

**Snapshot `ca82e795c594`. 12 markets × 529 OOS bars. Cumulative K: 51.**

```
arm                         ret      PF   maxDD    n  costmult  stress ret      PF  gate
baseline 231/21          -11.55   0.476   12.04   32     -8.70      -12.12   0.459  fail
CANDIDATE 7/0             -4.12   0.805   10.88   52     -1.01       -5.11   0.763  fail
CANDIDATE 14/0           -11.95   0.426   12.04   40     -6.91      -12.63   0.407  fail
CANDIDATE 28/0            -0.51   0.963   11.01   27      0.55       -1.04   0.927  fail

--- NEGATIVE CONTROL: buy the BOTTOM quintile ---
CONTROL 7/0 rev           +2.10   1.072   10.33   91      1.53       +1.76   1.087  fail
CONTROL 14/0 rev          +2.05   1.085   10.44   58      1.83       +0.96   1.039  fail
CONTROL 28/0 rev          +1.07   1.048   11.05   55      1.47       -0.03   0.999  fail
```

**NOTHING CLEARED THE DETERMINISTIC GATE. VERDICT: REJECT.**

### What H(§14) got right and wrong

Right: the horizon matters. 231 → 7 bars moved the return from −11.55% to
−4.12% and the cost multiple from −8.70 to −1.01. 28 bars is nearly flat at
−0.51%. The shipped lookback is measurably the worst of the four.

Wrong, and this is the finding: **shortening the horizon does not make momentum
positive. It makes it less negative.** No candidate crosses zero.

### The control fired, exactly as pre-registered

**All four momentum arms are negative. All three reversed arms are positive.**
Every control has PF > 1 and a positive cost multiple; no candidate does.

Per §11's rule and this section's own pre-registration, a control that passes
harder than the candidate **invalidates the candidate**. It does that here — but
the more useful reading is the one written down in advance: the signal at these
horizons is **reversal, not momentum**. `xsmom` is not a weak strategy. It is a
strategy pointed the wrong way.

That prediction was recorded before the run — *"I expect the CONTROL to pass
more readily than the candidate, because the cost literature is more confident
about reversal surviving fees than about momentum"* — so it is a confirmed
forecast, not a story assembled after seeing the table.

### What this does NOT license

**The control is not adoptable, and it did not pass.** Cost multiples 1.47–1.83
against a 2.0 bar; profit factors 1.048–1.085 against 1.3. Reversed `xsmom` is
directionally right and still not good enough. Adopting it would be exactly the
post-hoc hypothesis reversal §11 named as "the canonical overfit."

No EDGE test was run: the deterministic gate is a precondition and nothing
cleared it.

### What it does license

§15 — cross-sectional reversal as a strategy in its own right — **was scoped in
this section's pre-registration, before these numbers existed.** It is not a
discovery being retrofitted. What §14 adds is that the direction is now
evidenced on this snapshot under a proper control, at three horizons, rather
than only in the literature.

§15 must be a real specification, not reversed `xsmom`: the reversal literature
uses a one-week formation with **weekly rebalance** and value weighting, and the
mechanism it attributes the return to is **illiquidity**. Reversed `xsmom`
inherits `exit_below_fraction: 0.50` and a daily decision cadence, which is why
its 91 trades cost more than they return. The turnover is the thing to fix, and
it is a different rule, not a flipped sign.

### Trial accounting

**+3 (the candidate horizons). Cumulative K: 51.** Controls do not increment it
— they cannot be adopted, so they consume no multiple-comparison budget. Every
future EDGE claim is corrected against 51, α = 0.00098.

### Method note

`_reverse_rank` was added to `xsmom.prepare` for the control and is pinned by
two tests: it must be **absent from the shipped config**, and it must genuinely
invert the ranking. A research flag that can silently reach production is how a
strategy starts doing the opposite of what its name says.

---

## §15 — PRE-REGISTRATION: cross-sectional reversal, with the turnover fixed

**Written before `src/strategies/xsrev.py` exists. This commit contains no
strategy, no gate script and no results.**

### Why this, and why it is not "reversed xsmom"

§14 established the direction on this snapshot under a proper control: all four
momentum arms negative, all three reversed arms positive. But the reversed arms
did not pass, and the reason is legible in the table — **CONTROL 7/0 took 91
trades over 529 bars** and its costs ate the return. Cost multiple 1.53 against
a 2.0 bar.

The literature's reversal specification is not a flipped momentum rule. Liu et
al. form **value-weighted, weekly-rebalanced** portfolios on quintile ranks, and
the mechanism the replication work attributes the return to is **illiquidity**.
Reversed `xsmom` inherits a daily decision cadence and `exit_below_fraction:
0.50`, so it churns. **Turnover is the defect, and it needs a different rule
rather than a different sign.**

**H(§15): a one-week formation with WEEKLY rebalance produces a materially
better cost multiple than the same signal rebalanced daily, because the edge per
trade survives while the number of trades falls.**

### The specification, fixed now

* Rank the universe on trailing **7-bar** return. No skip.
* Buy the **bottom quintile** (`buy_bottom_fraction: 0.20`).
* Exit when a holding leaves the bottom **half** (`exit_above_fraction: 0.50`).
* **Rebalance on one weekday only.** Entries and strategy-exits are considered
  on that bar; stops and take-profits remain live every bar, because a
  protective leg that only works on Mondays is not a protective leg.
* Equal-weight within the quintile — not value-weight. The literature uses
  value weighting; this bot has no market-cap feed and inventing one to match a
  paper would be adding an unverifiable dependency to chase a detail.

### Arms — THREE, declared now, no sweep

| arm | formation | rebalance |
|---|---|---|
| A | 7 bars | weekly |
| B | 14 bars | weekly |
| C | 7 bars | daily *(the turnover control — isolates the rebalance change)* |

Arm C exists so the result is attributable. If A beats C, weekly rebalance is
what did it. If A ≈ C, the cadence was not the problem and the turnover
argument above was wrong.

### Trial accounting

`xsrev` is a **NEW STRATEGY FAMILY**, not a within-strategy variant. **+3.
Cumulative K after this run: 54.** α = 0.05/54 = 0.000926.

### The negative control, declared in advance

Run the same rule pointed at the **top** quintile — i.e. momentum — at the same
horizons and cadence. §14 already predicts this should be worse; if it is not,
the reversal reading is wrong and §15's premise collapses. Controls do not
increment K and can never be adopted.

### Falsification — all must hold

1. Both fee arms pass `enablement_gate`.
2. `n_trades ≥ 15` at both arms.
3. Cost multiple ≥ 2.0 at both arms.
4. Turnover ≤ 8 round trips/month.
5. Bootstrap CI excludes zero at **K=54**.
6. The momentum control does not outperform.

**The 1.5× stress margin does not move.**

### Predicted outcome

I expect weekly rebalance to roughly halve the trade count against arm C and to
raise the cost multiple — that is close to arithmetic, since the edge per trade
is unchanged and the fee count falls. I do **not** expect it to reach 2.0.
CONTROL 7/0's 1.53 would need to rise by a third on turnover alone, and the
§14 arms were already thin.

**Most likely outcome: A and B improve on C, all three still fail.** If that is
what happens, the honest conclusion is that cross-sectional reversal is real on
this data and too small to pay a 52 bps round trip — which is a finding about
the cost floor, not about the signal.

---

## §15 RESULT — REJECT. The turnover argument was backwards.

**Snapshot `ca82e795c594`. 12 markets × 529 OOS bars. Cumulative K: 54.**

```
arm                   ret      PF   maxDD    n  costmult  stress ret      PF  gate
A  7d weekly        -5.23   0.724   11.34   29     -3.43       -5.78   0.699  fail
B 14d weekly        -7.19   0.525   11.24   18     -9.02       -7.52   0.509  fail
C  7d DAILY         -2.08   0.913   12.41   56      0.13       -3.17   0.869  fail

--- NEGATIVE CONTROL: same rule, TOP quintile (momentum) ---
CTRL A  7d weekly    -6.59   0.584   13.84   37     -3.52       -7.27   0.551  fail
CTRL B 14d weekly    -9.48   0.449   14.31   32     -6.65       -9.27   0.446  fail
CTRL C  7d DAILY     -7.59   0.784   12.17  104     -0.83       -7.21   0.784  fail
```

**NOTHING CLEARED. VERDICT: REJECT.**

### The prediction was wrong, and that is the finding

§15 predicted, in writing: *"I expect weekly rebalance to roughly halve the
trade count against arm C and to raise the cost multiple — that is close to
arithmetic, since the edge per trade is unchanged and the fee count falls."*

The trade count did fall — 56 → 29, almost exactly half, as predicted. **The
cost multiple went the other way: 0.13 → −3.43.** Weekly rebalance did not make
the strategy cheaper; it made it worse, and by more than the fee saving was
worth.

The arithmetic was right and the premise underneath it was wrong. *"The edge per
trade is unchanged"* is the assumption that failed. **Short-horizon reversal
decays faster than a week.** Waiting for Monday means buying after the bounce has
already happened, so the weekly arm is not the same edge traded less often — it
is a worse edge traded less often.

Arm C was in the pre-registration for exactly this: *"If A ≈ C, the cadence was
not the problem and the turnover argument above was wrong."* A is not ≈ C, it is
materially worse than C, so the turnover argument was not merely wrong — it was
backwards. Without arm C this would have read as "reversal fails" rather than
"the rebalance rule I chose fails."

### A discrepancy I introduced and did not declare

§14's reversed arm scored **+2.10%** at 7 bars daily. §15's arm C — nominally
the same idea, same horizon, same cadence — scores **−2.08%**. They are not
measuring the same population, and the difference is mine:

* §14's control was reversed `xsmom`, which retained `and mom > 0` from the
  original rule. Reversed, that buys the **weakest of the positive performers**
  — laggards in an up-market.
* `xsrev` requires `ret < 0`. It buys **actual losers**.

Those are different strategies wearing the same description. §14's positive
result was *"buy the laggards"*, not *"buy the losers"*, and I carried the
former forward as evidence for the latter without noticing the gate had changed.
Recorded here rather than quietly reconciled, because a spec that drifts between
the section that motivates it and the section that tests it is how a programme
convinces itself of something neither section measured.

### What still holds

**Direction.** Every momentum control is worse than its reversal counterpart at
matched horizon and cadence (−6.59 vs −5.23, −9.48 vs −7.19, −7.59 vs −2.08).
§14's finding survives §15: on this snapshot, cross-sectional momentum is worse
than cross-sectional reversal. That is now measured twice, under two different
rule sets, with a control each time.

**And neither is tradeable at 52 bps.** The best reversal arm in either section
reaches a cost multiple of 0.13 against a 2.0 bar.

### Trial accounting

`xsrev` is a new family: **+3. Cumulative K: 54.** α = 0.000926. No EDGE test
was run — the deterministic gate is a precondition and nothing cleared it.

### What this closes and what it leaves

**Closed:** the horizon (§14) and the rebalance cadence (§15) are not what is
wrong with cross-sectional signals on this data. Both were tested with controls
and both came back negative. **A third variation of the same ranking idea is not
warranted**, and at K=54 each one now costs more than it can find.

**Left open, unchanged from §10:** every arm in this programme still reads only
price. §11 tried the one exception — funding — and its control invalidated it.
The remaining untested information is order-flow: §9's maker mechanism, which
needs weeks of passive book collection and no trading, and which is the only
recorded next step that does not involve re-interrogating these 529 bars.

`xsrev` ships `enabled: false`, like every strategy that has not passed a gate.

---

## §16 — Order-book collection begins. Observe-only. No verdict.

**Type: DATA COLLECTION. No strategy's status changed. Trial count unchanged
at 54.**

§9 produced the best numbers in this programme — maker entries at +5.06% OOS,
PF 1.636 — and rejected them, because the fill model was dishonest:

> "I modelled an order that pays maker fees while behaving like a taker. That
> is not a maker strategy; it is a fee assumption wearing one."

The limit sat at `close × (1 − 3bps)`, a synthetic bid, and filled on **98% of
signals**. A real resting bid sits where the book actually is and misses the
moves that run away. §9 could not measure that tradeoff because the data did not
exist. §10 recorded the protocol; this starts it.

`scripts/collect_orderbook.py` samples Kraken's top-of-book and ten levels a
side, hourly at :05, for the twelve markets.

### Provenance splits three ways now, and it is declared

```
gated on      Coinbase daily bars   depth of history (Kraken serves ~720)
funding from  Binance perps         §11, the only venue with the history
books from    KRAKEN                §16, because that is where orders rest
```

Kraken specifically. §9's question is about **execution**, and a maker order
rests in Kraken's book at Kraken's spread. Sampling Coinbase would answer a
question nobody asked.

### Why hourly, and why the raw file is not committed

15-minute sampling is 218 MB/year and buys nothing. Whether a resting order
**filled** is already answerable from the next bar's low; the book is needed to
know **where to rest it**, which is a decision-time question. Hourly covers
00:00 UTC plus 23 intraday samples for spread context — 55 MB/year, still too
much for git.

So `data/orderbook_live.jsonl` is gitignored, and the discipline is the one the
bar snapshot already uses: **raw collection stays local; when a gate needs it,
it is compacted into a committed, hashed snapshot.** A gate run against a
mutable file is a verdict nobody can check.

Minute :05, not :00 — the bar close is when the decision cycle is fetching, and
a twelve-symbol depth sweep competing for the same rate limit is how a cycle
degrades for a reason nobody can see in the logs.

### The first sweep already measured something

12/12 markets. Observed Kraken spreads, 2026-07-28:

```
BTC 0.02   ADA 0.06   XRP 0.56   ETH 0.62   DOGE 0.92   DOT 1.31
SOL 1.35   AVAX 1.52  LINK 3.95  LTC 4.33   UNI 6.71    ATOM 9.95   bps
```

**Median half-spread 0.68 bps. `slippage.synthetic_half_spread_bps` is 3.0 —
4.4× wider than reality.**

That is conservative in the right direction for taker fills, and §2 made the
same call deliberately when the probe measured 0.0–0.4 bps against an assumed
6.0: *"the RIGHT direction to be wrong."* **It is not conservative for the
maker question.** A synthetic bid 3 bps under the close is further from the
touch than the entire real spread on most of this universe, which means §9's
limit was resting where no real order would — and still filled 98% of the time,
because the fill test used the next bar's low rather than the book.

One sweep is not a measurement. The spread distribution over weeks is, and that
is what is now being collected.

### What this does not do

**It changes no number and no verdict.** The trading loop does not import this
script, does not read its output, and has no order-book dependency.
`venue/market.py` still defines no `fetch_order_book`. Five tests pin the
collector: it defines no order method, it refuses any credential, a failed
symbol is recorded rather than dropped (§7's lesson), a crossed book is refused
rather than treated as arbitrage, and Kraken's three-element levels parse — that
last one because the first live sweep failed on all twelve symbols unpacking
`[price, amount, timestamp]` into two names.

### The bar for re-gating §9

Not "enough data" by feel. **A quarter of coverage**, then compact to a hashed
snapshot, then re-run §9's arms with the limit at the observed bid and fills
determined by whether the book traded through. The hypothesis and its negative
control get pre-registered before that run, like §11, §14 and §15.

Until then this is a file that grows. It is the only remaining line of enquiry
in this log that does not involve re-interrogating the same 529 bars.

---

## §17 — PRE-REGISTRATION. Relative-volume entry filter on meanrev. Written before the gate exists.

**This section is committed BEFORE `scripts/gate_rvol.py` is written.** Check the
git history: the commit that adds this text contains no gate script and no
results.

### The correction that starts this section

The audit that opened this line of work asserted that Repete1 is price-only and
that no strategy reads volume. **That was wrong**, and the error is worth keeping
because it was two `grep`s away from being avoided.

`strategies/base.py:78` defines `rvol()` and `risk.py:334` defines
`rvol_blocked()` — ONE implementation, called from live (`main.py:1191`) and
both simulators (`backtest.py:639`, `backtest.py:1041`), entries only,
fail-open. It sits in the same block as §11's funding filter, because it is the
same kind of object: a veto on an entry the strategy already wants.

It came from the EQUITIES project — its docstring cites §23, and this log stops
at §16. **In crypto it has never fired.** `min_rvol` is absent from
`config.yaml`, the threshold defaults to 0, and `rvol_blocked` returns False on
its first line every time it is called. The rail is built, wired, tested, and
inert.

So this section adds no strategy and no rail. It is a gate on a switch.

### Why a FILTER and not a sixth signal

Every rejection from §7 to §15 died on **cost multiple**, not on direction.
§10's diagnostic named it exactly: meanrev clears the whole gate at real Kraken
fees and misses the 1.5× arm by 0.054 on PF and 0.18 on cost multiple. It needs
roughly 10% more edge per trade.

Filters remove entries and leave the horizon alone, which raises cost multiple
mechanically at a fixed edge per trade. §15 tried to get the same effect by
halving turnover through a weekly rebalance and **destroyed the signal doing it**
— cost multiple went 0.13 → −3.43, because reversal decays faster than a week.
A veto does not touch the horizon. That is the entire ordering argument for
testing this before any new volume SIGNAL.

### The hypothesis

    H: meanrev buys dips. A dip on HIGH volume is liquidity-motivated selling —
       forced or impatient sellers paying for immediacy — and the buyer is paid
       to supply it. A dip on QUIET volume is more likely to be information
       being priced in slowly, and has no such compensation. Vetoing quiet-tape
       entries should raise gross edge per trade and therefore the cost multiple.

Campbell, Grossman & Wang (1993), "Trading Volume and Serial Correlation in
Stock Returns": price declines on high volume revert more than declines on low
volume, and the mechanism is compensation for absorbing liquidity demand. That
is the exact effect meanrev is trying to harvest, and rvol is the discriminator
it has never used.

**CLAIM TYPE: EDGE.** The CI must exclude zero at the cumulative trial count.

**Within-strategy filter, not a new arm** — same signals, same exits, same
sizing, a veto on entry only. Three thresholds, so **+3 trials. Cumulative K
after this run: 57.** α = 0.05/57 ≈ 0.00088. Controls do not increment K.

### DISCLOSURE: what I looked at before fixing the arms

Concealing this would make the pre-registration a fiction, so it is recorded.

Before fixing the thresholds I computed IS mean-PnL by threshold, not only the
IS distribution. It reads:

```
  threshold   entries kept   veto%   mean pnl kept   mean pnl vetoed
   1.00        28/68         59%          +265.39         -227.58
   1.20        19/68         72%          +313.59         -155.72
   1.30        18/68         74%          +308.46         -144.49
   1.50        10/68         85%          -290.35          +21.23
```

**The IS optimum is 1.20–1.30, and the arms below are deliberately NOT that.**
Picking 1.30 because the IS table points there is precisely §8 — 36 variants,
+10.15% IS, **−7.29% OOS**, worse than not searching. The arms are fixed instead
by a rule chosen independently of PnL, stated in the next paragraph, and the
reader can check that none of them is the IS winner.

Note also that 1.50 flips sign IS. A monotone mechanism should not do that; it
is what a small sample looks like when it is being over-read, and it is another
reason not to fit to this table.

### Exactly what is being tested, fixed now

- **Signal** `rvol(bars, 20)` — the decision bar's volume over the mean of the
  20 bars BEFORE it, `strategies/base.py:78`, unchanged. Period 20 is the shipped
  default and is NOT a second knob: no other period is tested.
- **Thresholds** the **p20 / p35 / p50 percentiles of rvol at meanrev's IS entry
  bars**, pooled across symbols. The rule is: *distribution percentiles, spaced,
  chosen so the OOS sample survives the n ≥ 15 floor.* Derived from IS only, so
  the numbers are not contaminated by the OOS result.

      arm A   min_rvol 0.623   (p20, ~20% of entries vetoed, OOS n ~24)
      arm B   min_rvol 0.737   (p35, ~35% vetoed, OOS n ~20)
      arm C   min_rvol 0.925   (p50, ~50% vetoed, OOS n ~15)

  Arm C sits exactly on the floor. That is the point of the upper bound: a
  fourth, higher arm could only pass by shrinking the sample below the level at
  which passing means anything.
- **Action** if `rvol < min_rvol` at a bar where meanrev would enter, the entry
  is vetoed. Exits, stops, trails and sizing are untouched. Fail-open on `None`
  is unchanged — a missing volume feed must not halt trading.
- **Baseline** meanrev exactly as it ships, `min_rvol` absent, rail inert.

### Falsification criteria, declared before the numbers

ADOPTED only if **all** of:

1. Both fee arms pass `enablement_gate` — the 1.5× arm must reach PF ≥ 1.3 **and**
   cost multiple ≥ 2.0. Clearing 1.0× alone is what meanrev already does and is
   not news. **The 1.5× stress margin does not move** (owner decision, §12).
2. `n_trades` ≥ 15 at both fee arms.
3. Cost multiple RISES against unfiltered meanrev. If n falls and cost multiple
   does not rise, the filter is cutting trades at random — REJECT.
4. The EDGE test at K=57 excludes zero.

### The stated prediction, so the record can be wrong

Arm A or B raises cost multiple above 2.71 while holding n ≥ 20; arm C fails on
n. I expect the 1.5× arm still to fail, on PF rather than on cost multiple.

§15's prediction was wrong in a way that taught more than a pass would have —
the trade count halved as predicted and the cost multiple went the wrong way,
which is how the horizon assumption got falsified. A prediction that cannot be
wrong is decoration.

### The negative control, which decides whether any of this is real

The **inverted** arm: veto entries when `rvol` is HIGH, keeping only quiet tape
(`rvol ≤ 0.623`, the p20). Under H that is the unfavourable state, so this
should be WORSE than baseline.

**If the inverted arm improves the cost multiple by a comparable amount, the
candidate is INVALIDATED** — that would mean any veto that thins the book helps,
and the volume story is doing no work. Per §11's rule the control can never
itself be adopted, and it runs every time, not only when the headline
disappoints. A control examined selectively is not a control.

### Counters, because an inert arm must not read as a confirmation

The gate prints, per arm, the number of entries VETOED. §11 added these after
`risk_pct` 1.0/2.0/5.0 measured byte-identical — three "results" from a rail
that never fired. An arm that vetoed nothing is inert, not confirmed.

### Provenance, declared now rather than discovered later

Coinbase daily volume is **single-venue base-currency volume**, not consolidated.
An rvol computed on it measures Coinbase activity, which is a proxy for market
activity and not the thing itself. The split widens to four and is declared:

    gated on     Coinbase daily bars   (depth of history)
    funding from Binance perps         (§11)
    books from   Kraken                (§16)
    volume from  Coinbase              (§17, same bars as the closes)

### Look-ahead

`rvol` reads the newest CLOSED bar and its 20 priors. A bar's volume is complete
at its close, and the decision is taken at that close, so no future information
enters. This is pinned by `tests/test_rvol_no_lookahead.py` rather than asserted
here — §11's funding-date convention was pinned the same way, and that test is
the reason its result is worth anything.

---

## §17 RESULT — REJECT. The best honest numbers yet, and a defect in my own criteria.

Snapshot `ca82e795c594`, 12 markets × 529 OOS bars. K=57, α = 0.00088.

```
arm                   ret      PF   maxDD    n  costmult  stress ret      PF    n  vetoed  gate
baseline            +2.56   1.353    3.74   30      2.71       +1.84   1.246   30       0  fail
CAND A  p20         +1.59   1.212    3.75   29      2.10       +0.86   1.110   29      22  fail
CAND B  p35         +3.03   1.427    3.75   29      3.09       +2.30   1.314   29      36  PASS
CAND C  p50         +4.07   1.732    2.55   28      3.91       +3.37   1.584   28      62  PASS
CONTROL inv         +2.02  12.335    1.61    6      7.32       +1.86  10.104    6     196  fail
```

### What cleared, and it is not nothing

**Arm C passes both fee arms.** +4.07% OOS, PF 1.732, cost multiple 3.91, and
under 1.5× fees it still returns +3.37% at PF 1.584 — comfortably clear of the
1.3/2.0 bar rather than the 0.054-and-0.18 miss §10 measured. Lower drawdown
than baseline too (2.55 vs 3.74).

That is the constraint §10 named, closed, by the mechanism §17 predicted would
close it. It is also the best deterministic result in this programme **that does
not depend on a dishonest fill model** — §9's +5.06%/1.636 came from a synthetic
limit that §16 has since shown rests further from the touch than the entire real
spread on most of this universe.

Criteria 1, 2 and 3 pass for B and C. And then:

### Criterion 4 fails, and it is not close

```
C  p50: candidate $+145.33/trade (n=28) vs baseline $+85.35/trade (n=30)
        diff $+59.98,  99.91% CI [$-551.12, $+682.15]   INCONCLUSIVE
B  p35: diff $+19.16,  99.91% CI [$-636.15, $+662.56]   INCONCLUSIVE
```

The interval is twenty times the width of the effect. At 28 trades, at K=57,
this is indistinguishable from zero. §17 declared "the EDGE test at K=57
excludes zero" as a condition of adoption. It does not.

**REJECT. `config.yaml` is unchanged; `min_rvol` stays absent and the rail stays
inert.**

### The negative control fired, and it did not need to

Cost multiple 7.32 against baseline's 2.71 — higher than any candidate. Read
literally, §17's invalidation condition is met.

It is also **six trades**, PF 12.3, from an arm that vetoed 196 entries. That is
not a measurement.

Both readings reach REJECT, so this does not need adjudicating, and I am not
going to adjudicate it — arguing the control away while the candidate looks good
is precisely the move §11's control exists to prevent, and the temptation to
make it is the evidence that it should not be made.

### What the control actually exposed: criterion 3 was defective

§17 criterion 3 reads *"cost multiple RISES relative to unfiltered meanrev. If n
falls and the cost multiple does not rise, the filter is cutting trades at
random — REJECT."*

**That is backwards and I wrote it.** The control thinned the book harder than
any candidate, in the direction H says is WRONG, and its cost multiple rose
further than any candidate's. So a rising cost multiple is not evidence that a
filter is selecting rather than merely thinning. Criterion 3 has no
discriminating power against the null it names.

Cost multiple is gross edge over fees. Removing trades removes fees. Any veto
raises it if the removed trades were even slightly worse than average, which
half of them are by construction.

**The correct null is a random-thinning control matched on trade count**: veto a
random 50% of entries, same seed discipline, and require the candidate to beat
*that*, not to beat unfiltered baseline. That is registered here as the repair
and applies to every filter this repo tests from now on, including §11's funding
result, whose criterion 3 was the same shape.

### Why the post-hoc bucket table does not explain the arms

```
OOS baseline trades by entry-bar rvol:
  <0.623        n= 4   mean pnl  -582.21
  0.623-0.737   n= 5   mean pnl  +311.50
  0.737-0.925   n= 8   mean pnl  -145.20
  >=0.925       n=13   mean pnl  +345.66
```

Tempting, and it does not decompose the results. Arm A vetoes the −582 bucket —
removing losers — and made things WORSE (cost multiple 2.71 → 2.10). The reason
is **path dependence**: A vetoed 22 entries while the baseline holds only 4
trades in that bucket, so most vetoes landed on entry attempts that never became
these trades, and freeing that capital changed which later signals were taken at
all. A filter is not a mask over the baseline's trade list.

The buckets are n = 4, 5, 8, 13. That is the whole finding: **the arms are being
separated on single-digit trade counts**, which is what the CI said in one line.

### What would resolve this, and what would not

Not more arms on these 529 bars. §8 is the standing evidence — 36 variants,
+10.15% IS, −7.29% OOS, worse than not searching. Arm C is either a real
mechanism or the best of three draws from noise, and this snapshot cannot tell
the difference at K=57.

**Forward trades can.** meanrev is already in paper with a review fixed at
2026-10-27 or 30 closed trades. Running `min_rvol: 0.925` alongside it would
generate the observations that separate C from baseline — and would also **reset
that clock**, because changing the entry rule mid-forward-test means the trades
before and after are not the same experiment. That is an owner decision with a
real cost on both sides, and it is not one a gate result gets to make.

### The prediction, scored

§17 predicted: *"Arm A or B raises cost multiple above 2.71 while holding n ≥ 20;
arm C fails on n. I expect the 1.5× arm still to fail, on PF rather than on cost
multiple."*

Wrong in the interesting direction. A HURT. C did not fail on n — it kept 28
trades, because vetoing an entry frees capital for a later one and the book
refills. And the 1.5× arm did not fail at all for B or C; it passed both
clauses. The thing I was most confident would not happen is the thing that
happened, and the thing I did not consider — that 28 trades cannot support any
verdict at K=57 — is what decided it.

---

## §18 — PRE-REGISTRATION. The universe widens 12 → 32, and meanrev is re-gated on it.

**Committed BEFORE the snapshot is built and before any gate is run.** Git
history verifies it: this commit adds the screening script and this text, and
contains no snapshot, no manifest and no results.

### The problem this addresses, which is not "no strategy has an edge"

Measured from the ledger and the shipped config, not asserted:

```
meanrev OOS:      30 trades / 529 bars / 12 markets
book-wide rate:   0.057 trades/day  =  1 trade every 17.6 days
live since 2026-07-27, 2 decision cycles, expected 0.11 trades, observed 0
```

Zero closed trades is the **base rate**, not a malfunction. The bot is healthy:
`src/live.py` running, heartbeat advancing, the decision cycle firing daily at
~00:02 UTC. It simply trades this rarely.

The consequence is the finding:

```
§12's forward review: 2026-10-27 OR 30 closed trades
  92 days to the date  ->  ~5 expected closed trades
  30 closed trades     ->  529 days (~1.4 years)
```

**The review lands on the date with about five trades, never on the count.**
§17 just rejected arm C on *twenty-eight* trades because the CI spanned
[-551, +682]. A five-trade forward sample settles nothing, so as specified §12
is guaranteed to return "inconclusive" three months from now.

Every bar this repo enforces — n ≥ 15, n ≥ 30, significance at K — is years away
at 0.057 trades/day. **Evidence throughput is the binding constraint**, and no
amount of re-interrogating the same 529 bars touches it.

### The change

Universe 12 → 32 markets, selected by `scripts/screen_universe.py`, which is
committed in this commit and whose rule is:

1. USD spot, active on **Kraken** (execution) **and Coinbase** (data).
2. Not a stablecoin — a dollar-pegged asset reverts by construction and would
   dominate any mean-reversion result. Excluded by name list.
3. 24h Coinbase dollar volume ≥ **$326,965** — the least liquid market ALREADY
   in the shipped universe. Not a new number chosen to admit a target count.
   The cost model charges a flat 26 bps while §16 measured real Kraken spreads
   from 0.02 to 9.95 bps, so admitting anything thinner would make the flat fee
   optimistic, which is §9's defect.
4. Bars present at **2022-09-27** (±7d) — ≥ ~1400 daily bars, so every admitted
   market carries the SMA200 warmup plus a usable OOS window.

Output frozen to `data/UNIVERSE.json`; `--verify` re-runs the screen and fails
on drift. It was run twice and returned the same 32.

Throughput at 32 markets, if the per-market rate holds: **0.057 × 32/12 ≈ 0.151
trades/day**, one trade every 6.6 days, ~14 trades by 2026-10-27. Still short of
30, and materially better than 5.

### What the rule costs, stated rather than discovered

**XRP/USD is dropped.** Coinbase suspended it during the SEC action and relisted
it 2023-07-13, so it has no bars at the cutoff — the 905-day hole §13 documented
and tolerated only because it sat entirely in-sample under the OLD split. A new
snapshot moves the split. A tolerated gap that is never re-measured is how "we
know about that one" becomes cover for one nobody knows about.

**The screen dropped ATOM/USD on its first run and ATOM demonstrably has bars at
the cutoff.** Coinbase returns an EMPTY page for a window predating a listing
rather than skipping forward, and a transient empty is indistinguishable from a
real absence in one call. That is §7's bug — *"an earlier version treated an
empty page as end-of-data and reported seven markets as having zero bars when
each had years"* — reproduced a third time, by me, in the screen written to
avoid it. Negatives are now retried, an ERROR is never folded into an absence,
and the screen refuses to emit a universe containing an unresolved market.

### The survivorship bias, which this does NOT fix

Every candidate is listed and active TODAY. Coins that listed inside the window
and died are absent, and crypto's death rate is not small. Coinbase does not
serve delisted history, so this cannot be fixed with this data.

It biases backtested returns **UPWARD**, which makes the reading asymmetric and
the asymmetry usable:

> **A REJECT on this universe is trustworthy** — the bias was helping and the arm
> failed anyway. **A PASS must be discounted** by an amount nobody here can
> quantify.

Every §18 verdict and everything gated after it inherits that caveat.

### §7's rule: a universe change invalidates every prior verdict

*"meanrev's PASS was measured on a universe produced by a bug. REVERTED."*

meanrev is in paper (§12) on numbers measured over **twelve** markets. Those
numbers do not describe a thirty-two-market book, so they do not carry over.
**meanrev is re-gated on the new snapshot before anything else is decided.**

**CLAIM TYPE: EDGE, +1 trial → K = 58**, α = 0.05/58 ≈ 0.00086. Re-testing the
same strategy against a newly drawn universe is a trial in exactly the
multiple-comparison sense that matters: re-drawing universes until something
passes is fishing, and the way to not do that is to fix ONE rule in advance and
count the draw. The rule above is that one draw.

### Kill criteria — the part that makes this not a free option

**If meanrev fails the re-gate on the 32-market universe, it comes OUT of
paper.** §12's enablement was an owner decision justified by a specific,
quantified 12-market result (+2.56%, PF 1.353, cost multiple 2.71, failing only
the 1.5× arm by 0.054 and 0.18). If those numbers do not survive the universe
change, the justification does not survive it either, and leaving meanrev
running would be keeping the decision while discarding its evidence.

Widening the universe must be able to make things worse. Otherwise it is not a
measurement.

### The stated prediction

meanrev's return and profit factor FALL on 32 markets, because the 12 were
chosen — before any of this discipline existed — as the majors, and the 20 added
names are thinner and noisier. I expect n to roughly double (30 → 60-80), the
cost multiple to fall below the 2.0 bar, and the re-gate to REJECT at 1.0× fees,
not merely at 1.5×.

If that happens the honest outcome is that meanrev leaves paper and Repete1 has
zero enabled strategies — which is a worse-looking position than today and a
more accurate one.

---

## §18 STATUS — HALTED before the gate. The universe rule is not reproducible.

**No verdict. No gate was run, and that is the finding.**

### What happened

§18 pre-registered a mechanical universe rule and claimed its central virtue was
reproducibility: *"the rule is code, the rule is committed BEFORE the snapshot is
built, and its output is reproducible."*

`screen_universe.py --verify` re-runs the screen and fails on drift. It failed:

```
UNIVERSE DRIFTED. added ['ACH/USD'], dropped ['IMX/USD']
```

Across three runs of the same rule against the same venues:

```
             run 1     run 2 (median of 3)   run 3 (median of 3)
IMX/USD      17.90            <=10.0                22.49
ACH/USD      15.27            <=10.0                  ...
COTI/USD     37.17            34.25                 63.52
FLOW/USD     18.42            18.42                 31.19
```

Rule 5's input — the live mid-price difference between Coinbase and Kraken — is
**not a stable property of a market.** For thin names it moves minute to minute
by more than the ceiling being applied to it. Taking a median of three samples
reduced the noise and did not remove it, which is exactly what a genuinely noisy
statistic does.

### Why this halts §18 rather than being a caveat on it

The snapshot built from run 2's universe reports **max divergence 18.0 bps**
against a rule 5 ceiling of **10.0 bps**. The artifact violates the rule that
produced it. A gate run on that file would be a verdict denominated in a
universe that (a) cannot be re-derived and (b) does not satisfy its own
criteria — which is §7 exactly: *"meanrev's PASS was measured on a universe
produced by a bug. REVERTED."*

So the gate was NOT run. `data/MANIFEST.json` is restored to
`crypto_bars_20260727.json.gz` (`ca82e795c5943e03`), the 12-market snapshot every
§1–§17 verdict is denominated in, and the unverified 28-market snapshot is
deleted rather than left on disk to be picked up later by something that does not
know its provenance. Suite green at 1029 passed, 1 xfailed.

**Trial count stays at 57.** §18 registered +1 for a gate that did not happen,
and counting a trial nobody ran would corrupt the correction the same way
skipping one would.

### The mistake, named

Rule 5 was right to exist. The builder had already written the condition down —
*"if this ever grows past a few basis points the split has stopped being safe and
the gate results inherit an error nobody measured"* — and COTI at 37 bps against
a 52 bps round trip is a real disqualification, not a fastidious one.

The error was the **measurement**, not the criterion: I enforced a threshold
using three spot ticks of a quantity that needs days to estimate. A filter whose
input is noisier than its own ceiling does not select markets, it samples them.

### The fix, which is deterministic and uses data already committed

Measure divergence from **daily closes over the overlapping history**, not from
live tickers:

* Kraken serves ~720 daily candles — no use for gating (§8's 17-tradeable-day
  problem) but ample for estimating a price relationship.
* Median |Coinbase close − Kraken close| / Kraken close over those ~720 days is
  a stable statistic, computed from frozen data, and identical on every run.
* It also measures the right thing. A strategy holds positions for days; what
  matters is whether the two venues agree over the horizon it trades, not
  whether they agree at the instant a screen happens to run.

That makes the screen a pure function of committed data, which is what §18
claimed and did not deliver.

### What is NOT affected

§17's REJECT, and every verdict §1–§17, were measured on `ca82e795c5943e03` and
are untouched — the snapshot was restored, not rebuilt. meanrev remains in paper
under §12 on its original evidence, because the re-gate that could have removed
it never ran. Its kill criterion is deferred, not waived, and it fires the moment
§18 completes on a reproducible universe.

The throughput finding that motivated §18 stands and is unchanged by this:
0.057 trades/day means §12's review lands on its date with ~5 trades and cannot
conclude. Fixing the universe rule is still the highest-value work available.

---

## §18 RESULT — REJECT, and the KILL CRITERION FIRED. meanrev is out of paper.

Snapshot `078438ba28ca31a8`, 21 markets, 423–831 OOS bars. K=58, α = 0.00086.

```
arm                        ret      PF   maxDD    n  costmult   stress ret      PF  gate
CONTEXT old 12 markets   +2.56   1.353    3.74   30      2.71        +1.84   1.246  fail
§18 new 21 markets       -9.90   0.553   11.34   52     -2.92       -10.13   0.532  fail
```

### It does not miss the bar. It inverts.

```
[1.0x] OOS return -9.90% not positive
[1.0x] profit factor 0.553 < 1.3
[1.0x] beats neither B&H -4.64%, the risk-adjusted bar, nor the
       exposure-matched benchmark -0.11% (at 2.4% avg deployment)
[1.0x] cost multiple -2.92 — gross edge per trade is NEGATIVE (-$141.79)
```

A negative gross edge is the part that matters. Every previous rejection in this
log was a strategy with a real but insufficient edge being eaten by costs; §10
put meanrev 0.054 of PF and 0.18 of cost multiple away from passing. **This is
not that.** At −$141.79 of gross edge per trade there is no fee schedule, no
filter and no execution improvement that rescues it. The trades are wrong before
costs are applied.

No EDGE test was run. A p-value on an arm that failed every deterministic clause
is a number shopping for a verdict.

### What was actually being measured for eighteen sections

**meanrev's +2.56% was a property of the twelve markets, not of the strategy.**

The twelve were BTC, ETH, SOL, XRP, ADA, LINK, AVAX, LTC, DOGE, DOT, UNI, ATOM —
the majors, typed into a config before any of this repo's admission discipline
existed. Run the same rules over a universe chosen by a committed, reproducible
screen and the sign flips.

§7 stated the principle after a universe bug: *"meanrev's PASS was measured on a
universe produced by a bug. REVERTED."* The universe here was not produced by a
bug. It was produced by taste, which is harder to see and had never been tested.
§18 is the test, and the strategy failed it.

Note the direction of the survivorship caveat: the 21-market universe is
markets alive TODAY, so its returns are biased **UP**. meanrev lost 9.90%
*with the bias helping it*. §18 pre-registered that a REJECT on this universe is
trustworthy, and this is one.

### The kill criterion, executed

§18 declared, before the snapshot existed: *"If meanrev fails the re-gate on the
32-market universe, it comes OUT of paper... Widening the universe must be able
to make things worse. Otherwise it is not a measurement."*

`config.yaml`: `strategies.meanrev.enabled: false`, 2026-07-29.

**Repete1 now has ZERO enabled strategies.** That is a worse-looking position
than yesterday and a more accurate one. Nothing in this repo has passed a gate.

§12's forward review is void rather than pending — it was measuring a strategy
whose enablement rested on evidence that has now been withdrawn. The ~4 hold-only
cycles it accumulated remain in the ledger and are not evidence of anything.

### The throughput result, which stands and is now moot for meanrev

```
52 trades / 423 bars = 0.1229 trades/day   (1 every 8.1 days)
was 0.0567/day on 12 markets — 2.17x
by 2026-10-27: 11 trades, was 5.   §12 needed 30.
```

The universe change did what §18 predicted mechanically — 2.17× the evidence
rate — and it still would not have reached 30 trades by the review date. Both
things are true: throughput was a real constraint, and fixing it exposed that
the strategy it was meant to serve does not work.

### Prediction, scored

§18 predicted: *"meanrev's return and profit factor FALL on 32 markets... I
expect n to roughly double (30 → 60-80), the cost multiple to fall below the 2.0
bar, and the re-gate to REJECT at 1.0× fees, not merely at 1.5×."*

Right on every count and far too gentle on magnitude. n went 30 → 52. But I
predicted a fall toward the bar and got a sign inversion, and I did not predict
a NEGATIVE gross edge, which is a different diagnosis entirely: not "this edge is
too small to pay for," but "there is no edge."

### Where this leaves the programme

58 registered trials. Zero adopted. Zero closed trades. Zero enabled strategies.

What survived tonight is method, not signal: a universe that is now the output of
a verified rule instead of taste, a snapshot whose markets provably track the
venue they trade on, and one fewer false belief. §17's rvol stamp keeps recording
against a strategy that is now switched off, which costs nothing and means the
data is there if meanrev is ever re-examined on honest ground.

The next thing that would be worth doing is NOT another variant of meanrev on
this universe. Five strategies have now been gated on hand-picked markets and
none has been re-measured on a screened one. Every prior verdict in §1–§17 is
denominated in a universe that has just been shown to carry the result.

---

## §19 — MEASUREMENT, no verdict. The liquidity floor is the wrong instrument, and the cost model just flipped sign.

No gate, no arms, **trial count stays at 58.**

§18 left an open question: rule 3's floor is $326,965/day (ATOM's current volume,
"no looser than what is already traded"), while `config.yaml` had documented the
original admission rule as **$1m/day**. ATOM's volume decayed below the rule that
admitted it, so anchoring on observed volume silently loosened the standard.

Rather than argue it, the 21 markets were measured against Kraken directly.

### Volume does not predict spread here

```
market       24h $vol      kraken spread
ATOM/USD  $    521,754        10.89 bps   below $1m
ALGO/USD  $    614,004         7.81 bps   below $1m
CRV/USD   $    781,937        10.46 bps   below $1m
BCH/USD   $    829,517         6.67 bps   below $1m
DOT/USD   $  1,172,608         6.51 bps
INJ/USD   $  1,349,127        10.92 bps   <-- WORSE than every sub-$1m market
ZEC/USD   $ 18,810,375         6.88 bps   <-- 36x ATOM's volume, 63% of its spread
BTC/USD   $507,450,263         0.02 bps
```

Below $1m: 4 markets, median 10.46 bps. At or above: 17 markets, median 4.96 bps.
The group difference is real — and INJ at $1.35m is wider than all four markets
the $1m floor would have cut.

**So neither answer to §18's question was right.** A volume floor is a proxy for
the thing rule 3 cares about, and on this universe it is a weak one. Moving it
from $327k to $1m would have cut four markets while keeping a worse one. The
floor stays where it is, doing crude work adequately, and the open question is
closed as **mis-specified** rather than decided.

### The finding that matters more

`fees.synthetic_half_spread_bps: 3` models a **6 bps** round-trip spread.
Measured on the 21:

```
WIDER than the model:  ATOM 10.89  INJ 10.92  CRV 10.46  ALGO 7.81  FET 7.22
                       AAVE 7.06  UNI 7.06  ADA 6.94  ZEC 6.88  BCH 6.67
                       DOT 6.51  AVAX 6.21          -> 12 of 21 markets
```

§16 measured the OLD twelve and found the opposite: median half-spread 0.68 bps
against a modelled 3.0, *"4.4× wider than reality"*, conservative in the right
direction. **On the screened universe the model flips from conservative to
optimistic for a majority of markets.**

### What that does and does not invalidate

**§18's REJECT is robust — strengthened, in fact.** meanrev lost 9.90% while
being *undercharged* for spread on most of the book. Correcting the cost model
makes that result worse, not better. Same asymmetry §18 declared for
survivorship: the errors were helping it and it failed anyway.

**Any future PASS on this universe is untrustworthy until the cost model is
re-grounded.** An arm that clears the bar while being undercharged has not
cleared the bar. This is §9's defect wearing its third hat — a model that
flatters the strategy — and it is now on the record before any arm passes rather
than after.

### The fix, and the mistake NOT being repeated

A spread ceiling must not be set from this table. One snapshot of a spread is
exactly as noisy as one snapshot of a cross-venue mid, and setting rule 5 from
three such samples is what halted §18 six hours ago. The lesson does not need
learning twice in one day.

`scripts/collect_orderbook.py` reads `cfg["symbols"]` (line 167), which is now
the 21, so §16's hourly sweep begins covering the screened universe on its next
run with no change required. When there is enough of it:

1. Set `synthetic_half_spread_bps` from the observed distribution, or make it
   per-symbol — the 500× range from BTC 0.02 to INJ 10.92 is not one number.
2. Replace rule 3's volume proxy with a **measured spread ceiling**, which is
   the quantity rule 3 was always trying to reach.
3. Re-run §18's re-gate under the corrected model.

Until then every gate on this universe carries a declared, directional caveat:
**REJECTs are trustworthy, PASSes are not.**

---

## §20 — PRE-REGISTRATION. Every remaining strategy, re-measured on the screened universe.

**Committed BEFORE the gate script exists.** Git history verifies it.

### Why this is mandatory rather than optional

§18 established that meanrev's entire result was a property of twelve hand-typed
markets: +2.56% on those twelve, **−9.90% with a negative gross edge** on
twenty-one chosen by a rule. The strategy did not change. The universe did.

Every other verdict in this log — §4, §5, §7 through §17 — was measured on those
same twelve. **tsmom carries a PASS from 2026-07-15** (OOS +1.45%, PF 2.56, 51
trades). §8's parameter search, §9's maker arms, §10's vol targeting, §11's
funding filter, §14, §15 and §17 were all denominated in them too.

There is no reason to assume those results are stable under the universe change
and exactly one strong reason to assume they are not: the one strategy that has
been re-measured inverted.

### The arms

One arm per strategy, each exactly as it ships, against
`crypto_bars_20260729.json.gz` (`078438ba28ca31a8`, 21 markets):

    ma_crossover   the baseline the ensemble is supposed to beat
    tsmom          THE ONE WITH A PRIOR PASS — the most informative arm here
    xsmom          FAILED on 12 (§7: -11.55%)
    xsrev          REJECTED on 12 (§15)
    donchian       never gated at all

**No parameter changes. No sweeps.** Each strategy runs with the config it has.
§8 is the standing evidence that searching costs more than it finds, and the
question here is not "can these be tuned" but "was the previous answer about the
strategy or about the universe."

**+5 trials → K = 63**, α = 0.05/63 ≈ 0.00079.

Cross-sectional note, declared in advance: 21 markets changes quintile sizes for
`xsmom` and `xsrev`. That is a genuine confound with the universe change and it
cannot be separated on this data — a bigger cross-section is a different
strategy in the way that matters. Their results are reported but **any xsmom or
xsrev movement is NOT attributable to the universe alone.**

### §19's caveat applies with full force, and it is asymmetric

`synthetic_half_spread_bps: 3` models a 6 bps spread; 12 of the 21 markets are
wider. Every arm below is therefore **undercharged for spread**.

    A REJECT is trustworthy   — the error was helping the arm and it failed anyway
    A PASS is NOT adoptable   — clearing a bar while undercharged is not clearing it

**No arm passing §20 will be enabled.** A PASS here buys a candidate for re-test
under a corrected cost model once §16's collector has covered the screened
universe, and nothing more. This is stated before the run so that a good-looking
number cannot later be argued into an enablement.

### The stated prediction

tsmom's PASS does not survive. I expect its return to fall and its profit factor
to drop below 1.3, for the same reason meanrev's did — a 63-bar momentum rule
tuned on an equity-months convention, validated on twelve majors, meeting
seventeen markets it was never measured against.

I expect ma_crossover, xsmom and xsrev to fail as they did before, and donchian
to fail on turnover. **I expect zero adoptable arms**, which would leave Repete1
where §18 left it: nothing enabled, and now with the twelve-market evidence base
retired rather than merely suspect.

If tsmom DOES survive, that is the single most interesting result in this log —
the first arm measured on a universe nobody chose by hand — and §19's caveat
still blocks enabling it.

---

## §20 RESULT — ZERO arms cleared. And tsmom's "PASS" was never a crypto result.

Snapshot `078438ba28ca31a8`, 21 markets. K=63, α = 0.00079.

```
arm                        ret      PF   maxDD    n  costmult   1.5x ret      PF  gate
[old 12] ma_crossover   -10.59   0.369   11.53   23    -11.57     -11.01   0.358  fail
§20 [21] ma_crossover   -12.00   0.000   12.00   17    -18.05     -12.30   0.000  fail

[old 12] tsmom           +0.36   1.016   11.14   60      1.15      -1.98   0.760  fail
§20 [21] tsmom           -1.87   0.814   13.12   19     -1.41      -0.15   0.981  fail

[old 12] xsmom          -11.55   0.476   12.04   32     -8.70     -12.12   0.459  fail
§20 [21] xsmom           +1.63   1.087   15.09   25      2.67      -1.60   0.927  fail  *

[old 12] xsrev           -5.23   0.724   11.34   29     -3.43      -5.78   0.699  fail
§20 [21] xsrev           -0.37   0.986   12.55   49      0.82      -1.36   0.949  fail  *

[old 12] donchian        -4.62   0.603   11.90   20     -4.94      -4.96   0.579  fail
§20 [21] donchian        -1.73   0.725   12.56    9     -3.74      -1.91   0.702  fail

* cross-sectional: 21 markets changes quintile size, confound declared in advance
```

**Every strategy in this repo has now been measured on a universe chosen by a
rule. None of them works on it.** Combined with §18's meanrev inversion, the
twelve-market evidence base is retired rather than merely suspect.

### The thing the context rows exposed

`config.yaml:74` says of tsmom: *"PASSED gate 2026-07-15: OOS +1.45%, PF 2.56,
51 trades (exposure-matched benchmark; see state/backtest_trials.jsonl)"*.

Re-run on **the same twelve markets** that claim was made about:

```
recorded:  +1.45%   PF 2.56   51 trades
measured:  +0.36%   PF 1.016  60 trades   -> fails the gate
```

Those are not the same result, and **`state/backtest_trials.jsonl` — the file the
comment cites as its evidence — does not exist.**

meanrev's config comment carries an explicit marker for exactly this situation:
`[prior, EQUITIES, void for crypto] PASSED gate 2026-07-15: OOS +1.40%, PF 2.19,
71% win, 171 trades`. Same date. tsmom's claim has no such marker.

The inference is straightforward: **tsmom's PASS is an equities result that was
never voided at the crypto fork**, and it has been sitting in the config for two
weeks as a crypto credential. It was never load-bearing — tsmom has been
`enabled: false` throughout — but it is exactly the kind of stale claim that
gets cited later by someone deciding what to enable. The comment is corrected in
the same commit as this entry.

That makes the count worse than §18 left it. It was never "one strategy passed
and one was enabled on a partial result." **Nothing in this repo has ever passed
a crypto gate.**

### What moved, and what it means

Single-asset arms got worse or stayed bad. The two cross-sectional arms
**improved markedly** — xsmom −11.55 → +1.63, xsrev −5.23 → −0.37 — which is
what §20 predicted the confound would do: ranking strategies want a bigger
cross-section, and 21 gives them one. Neither clears the bar, and per the
pre-registration their movement is not attributable to the universe alone.

xsmom is the closest thing to a signal here: PF 1.087 and cost multiple 2.67 at
1.0× fees. It fails on PF at both arms and turns negative under stress. Worth
noting, not worth acting on, and §19's undercharged-spread caveat would block
enabling it even if it had cleared.

### Prediction, scored

§20 predicted tsmom's PASS would not survive, that the others would fail, and
that there would be zero adoptable arms. All correct — but the tsmom call was
right for the wrong reason. I expected a real crypto result to degrade under the
universe change. There was no crypto result to degrade.

### Where the programme stands

**63 registered trials. Zero adopted. Zero closed trades. Zero enabled
strategies. Zero crypto gate passes, ever.**

Six strategies have been measured on a rule-chosen universe and all six fail.
That is not six near-misses: ma_crossover has a profit factor of **0.000**, and
four of six have a NEGATIVE gross edge per trade, meaning costs are not the
binding constraint — the trades are wrong before costs apply.

The honest reading is that this family of price-only rules, on daily bars, on
this universe, does not contain an edge. §17 was the only test of information
that was not price, and it could not be resolved at 28 trades. §16's order-book
collection is the only remaining line that introduces genuinely new information.

---

## §21 — Keep collecting. Fixing what "keep collecting" was actually doing.

No gate, no arms, **trial count stays at 63.**

The owner's decision after §20 was to keep Repete1 running as a data-collection
experiment while §16's order books accumulate. That is the right call on the
evidence — six strategies have now failed on a rule-chosen universe and four have
a NEGATIVE gross edge, so more arms against the same 423 OOS bars would be §8.

But "keep collecting" is worth nothing if what accumulates is thin, aimed at the
wrong universe, or silently stalled. All three were true.

### What was actually wrong

**1. Coverage was 37–50%.** The hourly order-book sweep was landing between a
third and a half of its runs, because this host sleeps and the scheduler sleeps
with it. Unlike a bar, **a book cannot be fetched later** — every missed hour is
gone. That put §22 roughly twice as far out as its schedule implied, and the only
reason anyone knew is that a person read the file by hand.

Fixed with `caffeinate -i` wrapping the scheduler in `run_repete1.sh`, guarded by
`command -v` because that file is deliberately the same launch path the container
uses and Linux has no `caffeinate`. It blocks IDLE sleep only, leaves no system
setting behind, and does **not** override a closed lid — if coverage does not
rise, the honest answer is an always-on host and `deploy/repete1.service` exists
for one.

**2. The funding collector was aimed at a universe that no longer exists.**
`collect_funding.py` carried its own hardcoded tuple of the twelve majors — the
same list §18 replaced with a rule in the snapshot builder. It had been
collecting **XRP/USD**, which §18 removed, and missing nine of the twenty-one
markets actually traded. Nothing failed; it ran green every night against a dead
universe. That is the quiet version of §7: **a collector cannot report a gap it
does not know it has.**

Now loads from `build_crypto_snapshot.load_universe()` — imported by path rather
than re-reading UNIVERSE.json, because two readers of the same file is how one of
them later grows a fallback list. Symbols with no Binance perp are now written
into the record with a reason instead of only printed to stderr, so a re-gate can
tell "funding was flat" from "there is no perp here." Checked: all 21 have perps,
so the field is currently empty and the path is defensive.

**3. Nothing surfaced any of it.** No dashboard panel, no watchdog check.

- `watchdog.collection_problems()` now reports coverage below 60% and any market
  with no book data at all. The floor is deliberately BELOW §22's 90% trigger:
  this alarm catches a collector that has stopped, not one still building, and
  this module already carries the scar of an alarm that paged for hours on a
  healthy bot.
- The dashboard gained a **Collection (§16 → §22)** card group: coverage,
  days collected against the target, markets sampled, and how many conditions
  still block the re-gate. With zero enabled strategies this is the only thing
  Repete1 is doing that matters, so it belongs on the operator's one window.

Both reuse `collect_orderbook.coverage()` rather than recomputing. Two
implementations of "how much have we collected", disagreeing, is precisely the
shape of the bug that produced nine false pages.

### The trigger, written down while nothing rides on it

§16's bar was "a quarter of coverage", which is not a number, and a bar that
cannot be measured gets satisfied by whoever is keenest to proceed.

```
REGATE_TRIGGER = min_days 30, min_coverage_pct 90.0,
                 all_symbols_sampled True, min_thinnest_frac 0.5
```

30 days × 21 markets ≈ 630 symbol-days, comparable to the 529-bar OOS window
every verdict here is denominated in. 90% rather than 100% so a venue outage does
not reset the clock.

`min_thinnest_frac` closes a hole the first draft left. When the universe went
12 → 21, ten markets appeared with **one sample each** while every hours-based
number read healthy and "all symbols sampled" was trivially true. Calibrating
INJ's spread off one observation would be exactly §19's mistake — a threshold set
from three ticks of a noisy quantity — repeated a third time. The thinnest
expected market must now carry at least half the observed hours.

Current state, from `--coverage`:

```
coverage_pct 36.8 | 0.8 / 30 days | 21 / 21 markets | §22: 3 blocking
no longer traded: ['XRP/USD']    thinnest: AAVE/USD (1)
```

### A correction to §16's stated plan

§16 said the re-gate would *"re-run §9's arms with the limit at the observed bid
and fills determined by whether the book traded through."* **That is not
possible.** §9's arms ran over 2025-02 → 2026-07 and order books for that window
do not exist and cannot be fetched — books are point-in-time, and no venue serves
their history.

§22 therefore becomes **calibrate-then-replay**: fit a per-symbol spread and
fill-probability model from the collected books, then re-run §9's maker arms on
the frozen snapshot under that model in place of the flat
`synthetic_half_spread_bps: 3`. This keeps the large OOS window and
**simultaneously repairs the §19 defect** — the same artifact fixes both, which
is why they merge.

Declared now, before any calibration code exists: §19's caveat **inverts** under
the corrected model. The current model is optimistic on 12 of 21 markets, so
re-grounding it makes every prior number *worse*, and any arm that passes §22
must pass under the corrected model or not at all.

### What this does not claim

It moves nothing toward profit. It makes the one remaining line of enquiry
actually collect what it needs, and it fixes a cost model that would have made
any future PASS false.

**63 trials, zero adopted, zero closed trades, zero enabled strategies, zero
crypto gate passes ever.** The trigger above exists so that nothing pretends
otherwise.

---

## §23 — The order path that was still there. No gate, K stays 63.

The owner asked what was needed to make Repete1 enterprise ready and chose
**audit-ready infrastructure**: production-grade and defensible to an outside
reader, independent of whether anything makes money. Host will be the Bizon
workstation. This is the code half; the hosting half waits on the machine.

### The finding

**`src/broker.py` was still the Alpaca equities wrapper, and it could place a
real order.** `market_order`, `bracket_market_order`, `replace_stop` and
`cancel_open_orders`, all over `submit_order`. Four live modules imported it:
`learn.py`, `review.py` (three times), `mark_positions.py`.

Every document in this repo says Repete1 "has no order path". That claim rested
on **one** mechanism, not two: no credential could exist, because `preflight`
fails on any `ALPACA_/KRAKEN_/COINBASE_/BINANCE_` variable. The code to place an
order was present the whole time.

`tests/test_repo_isolation.py` had tracked this honestly since Phase 0 as an
`xfail(strict=True)` — the "1 xfailed" in every suite run for weeks. The marker
was well built: strict, so the day Alpaca left, the test would start passing and
the suite would go red, forcing someone to come and delete it. It worked exactly
as designed. It just never got the work it was waiting for.

An auditor reading `deploy/SECRETS.md` — *"It holds no credential that can place
an order"* — next to a `submit_order` call in the same repository would not
accept the distinction, and would be right not to.

### What changed

`src/broker.py` **deleted**. `alpaca-py` out of `requirements.txt`. All five call
sites moved to `venue.venue_for` / `venue.data_for`. None of them ever needed to
place an order — they needed bars, positions and stops, and `PaperVenue` exposes
the same surface, which is what the parity harness has been proving all along.

`backtest.fetch_bars` was the other real site, and it was unreachable in the
worst way: a **deadlock**, not an error. It fetched US STOCK bars and required
`ALPACA_API_KEY`, so setting the key it needed stopped the bot booting while
omitting it raised `KeyError`. Either way no crypto bar arrived, and the
traceback pointed at a missing credential rather than at equities plumbing being
load-bearing in a crypto backtest. Now ccxt, via the same client the live loop
uses.

### Two things found on the way that are worth more than the cleanup

**1. A test fixture that inverted its own venue's contract.**
`tests/test_venue.py`'s `FakeExchange.fetch_ohlcv` treated `since=None` as "from
the beginning of history". **Every real venue means the opposite** — with no
`since`, Kraken, Binance and Coinbase all return the MOST RECENT `limit`
candles.

That is not a fixture detail. `venue/market.bars()` is built around precisely
this behaviour: it asks for the newest page first and walks backwards, and its
comment explains that paging forward from a computed start breaks on a lagging
market. Against the old fake, that design was handed the OLDEST page first — so
the tests exercised the reverse of production in the one dimension the function
exists to get right, and `test_bars_come_back_oldest_first_and_sliced_to_limit`
passed regardless, because it checked only count and ordering. **The ten oldest
bars satisfy both of its assertions.**

Fixture corrected; the ported regression now passes and nothing else moved,
which confirms production was right all along and the test was lying about why.
Same lesson as §13: a fixture the test wrote cannot disagree with the test's
assumptions.

**2. Deleting a regression test without checking the replacement.**
`tests/test_broker_bars.py` pinned an Alpaca bug — API-side `limit` truncating
from the oldest end, silently returning months-stale bars. Deleting it with
`broker.py` would have dropped that coverage, because the nearest crypto test
does not assert which END of the window survives. Ported to
`test_the_slice_keeps_the_NEWEST_bars_not_the_oldest` before the delete.

### A test was narrowed, and that needs justifying

`test_no_alpaca_anywhere` matched the literal string "alpaca" in **any** tracked
file, including the comments recording why it was removed. Under that rule the
only way to green is to delete the institutional memory of the migration.

It also contradicted its own docstring — *"An Alpaca import is evidence that one
was rebuilt"* — so the check was aimed at prose while claiming to be aimed at
imports. Narrowed to match imports and client construction, and **paired with a
new test that asserts `src/broker.py` does not exist**, which a regex over
imports cannot be tricked past by a lazy import built from a string.

Recording this explicitly because narrowing a test to make it pass is the exact
move `docs/go_live_checklist.md` warns about. The distinction: the guarantee got
*stronger* (the file is gone, not just unimported), and the detection now matches
what it always claimed to detect.

### Documents corrected

Wrong docs are worse than absent ones, and three were wrong:

* `docs/go_live_checklist.md` — said "12 markets", "K=5", "Five arms", "`meanrev`
  came closest". Now 21 markets, K=63, six strategies, **all failing, four with a
  negative gross edge**. Also carried the §17/§18/§19/§20 history, because the
  position has moved *against* us since that file was written and a checklist
  that only records hope is not a checklist.
* `CLAUDE.md` — still "~40 bps taker / ~80 bps round trip" (§5 corrected to
  26/52) and "Phase 8 — **meanrev enabled**" (§7 reverted it). Both fixed, plus
  §19's caveat that the flat model **undercharges 12 of 21 markets**, so every
  number in the project is optimistic rather than conservative.
* `docs/slo.md` — the cycle-completion row still specified **equities market
  hours** (15:45 / 15:55 catch-up / 16:15 ET) in a 24/7 bot whose bar closes at
  00:00 UTC, and heartbeat freshness still said "on weekdays". That file's own
  preamble says *"A documented check is not a check"*, which is exactly what
  those rows had become. §21's collection-coverage SLO added.

### Still outstanding, and it needs the owner

* **Bizon**: power on, IP, and *they* run `ssh-copy-id` — never me.
* **`ALERT_WEBHOOK_URL`**: unset, so alerts fall back to a desktop banner. On a
  headless host that is an unmonitored bot.
* **Offsite backup**: `scripts/backup.sh` defaults `DEST` to `backups/` — the
  same disk as the `state/` it protects.

### Unchanged

**63 trials, zero adopted, zero closed trades, zero enabled strategies, zero
crypto gate passes ever.** §23 makes the system defensible; it does not make it
profitable, and it does not tick a single go-live box.

### §23b — the doc sweep, and what it turned up

Deleting `broker.py` made several operator-facing documents wrong, so §23 swept
`docs/`. The sweep found more than it went looking for, and the pattern is worth
naming: **prose is the only part of this repo that nothing executes.**

**Actively harmful, both in incident paths:**

* `docs/runbooks.md`, *Stale bars* — the diagnostic step was a copy-paste block
  containing `from broker import Broker` and a fetch of `SPY`. A deleted module
  and a ticker that does not exist on a crypto venue, so the first instruction of
  that runbook would raise `ModuleNotFoundError`. At 3am, during the incident it
  exists to resolve.
* `docs/secrets_rotation.md` — listed `ALPACA_API_KEY` with a 90-day rotation
  cadence. `preflight` **refuses to start** if that variable holds a value, so an
  operator diligently following the rotation schedule would have halted the bot.
  The "assume leaked" drill also told them to check `broker.positions()` for
  unexpected orders on an account that cannot exist.

**And the sharpest one.** `CLAUDE.md`'s table titled **"What Repete1 is NOT
(deliberately removed at the fork)"** carried the row:

    src/broker.py Alpaca path (dead code; deleted with the last caller in Phase 4)

The file was still present, still exposed `market_order` and
`bracket_market_order` over `submit_order`, and was still imported by four live
modules. **A document asserted a deletion, in a table of deletions, for weeks,
while the code was there.** The credential half of the guarantee was always true;
the code-absence half was documented before it was done — which is the same
failure as §7's "documented check is not a check", pointed at a claim of removal
rather than a claim of verification.

**Citations to guarantees that resolved to nothing.** `CLAUDE.md` invariant #1
cited `tests/test_no_live_order_path.py` and invariant #9 cited
`tests/test_no_second_fill_implementation.py`. **Neither file has ever existed.**
Both guarantees are genuinely enforced — by
`tests/test_venue.py::test_the_market_client_defines_no_order_method`,
`::test_no_order_call_appears_anywhere_in_the_venue_read_path`, and
`tests/test_fill_model.py::test_no_second_fill_implementation` — so this was a
naming error rather than a missing defence. But a citation is how a document
claims a guarantee is enforced, and an unresolvable one is unverifiable.

**Equities features documented as if present:** `scripts/install_launchd.sh` (in
three places, including a restart procedure), `scripts/send_digest.py`,
`tests/test_digest_broadcast.py`, `src/daily_posts.py`, `src/earnings.py`. None
exist. Repete1 schedules in-process via `scripts/scheduler.py` under
`run_repete1.sh`, or `deploy/repete1.service` — there is no launchd and there are
no plists. `PRODUCT.md` described the equities *subscription product* end to end
(digest, subscribers, Stripe) — every surface of which CLAUDE.md itself lists as
removed at the fork. Renamed `EQUITIES_ARCHIVE_PRODUCT.md`, following the
existing `knowledge/EQUITIES_ARCHIVE_*` convention, with a header saying so.

**Equities time and vendors, still specified:** `docs/slo.md`'s cycle row wanted
a cycle "every market day (15:45, or 15:55 catch-up)" with the watchdog at
"16:15 ET", and heartbeat freshness "< 26h **on weekdays**" — in a 24/7 bot whose
bar closes at 00:00 UTC, where a quiet Saturday means the bot is dead. `runbooks`
had the same hours. `CLAUDE.md` described `datacheck.py` as "SPY close Alpaca vs
yfinance" (it is Kraken vs Coinbase) and `scorecard.py` as "vs S&P". Line 64 still
said "~80 bps round trip" after §5 corrected it to 52.

### The structural fix

`tests/test_docs_reference_real_code.py` — 25 tests. Every repo-relative path a
document cites must exist; every `file.py::test_name` node id must resolve to a
real test of that name; no fenced command may import a module `src/` does not
have. Doc rot is now a failing build rather than a discovery made by whoever
pasted the command.

A convention came with it: a reference that documents an **absence** is written
struck through (`~~src/broker.py~~`), which renders correctly and is
machine-distinguishable from a live claim. That is how §23's own correction notes
can name deleted files without tripping the check — recording a removal must not
be indistinguishable from asserting an existence.

Two false positives in my first draft of that test, both instructive:
`from venue import data_for` was flagged because the module collector read only
`*.py` and `venue` is a package — a guard that condemned the very fix it should
have blessed. And CLAUDE.md was reported as importing a module named `the`,
because a prose line inside a fenced table began "from the ledger even when no
alert fired". Fixed by requiring the whole line to have the shape of an import
statement, and by restricting the scan to fenced blocks. A test that parses
English produces noise, gets muted, and then protects nothing.

**Suite: 1065 passed, 0 xfailed.** Trial count unchanged at 63.

---

## §24 — Making the claims true. No gate, K stays 63.

§23b made *file and test citations* executable and found the pattern behind them:
prose is the only part of this repo nothing executes. §24 continues into the two
places that check could not reach, and turns the two remaining §23 blockers into
**detected conditions** rather than silent ones.

### The audit-facing document was the equities document

`docs/soc2_readiness.md` — the file you would hand a reviewer first — offered
`publisher/readonly.py` and `publisher/subscribers.py` as the evidence behind its
Logical Access and Confidentiality rows. **The entire `publisher/` tree, 18
modules, was deleted at the fork**, and CLAUDE.md says so two screens away
("Nothing to sell, nobody to sell it to"). It also named **Alpaca** and **X** as
vendors we depend on — §23 removed the last Alpaca code, `x_poster.py` does not
exist — and reasoned about "N=1 subscribers" for a bot with no product.

**§23b's check could not have caught it.** `PATH_RE` whitelists the directories
that exist (`src|tests|scripts|deploy|docs|web|knowledge`), so a reference into a
**removed** tree was invisible. A whitelist of the present cannot describe the
past, and the fork is precisely what created a past. Fixed by
`test_no_document_cites_a_directory_that_was_deleted`, which asks whether the
named directory is there at all.

Replaced by `docs/operational_controls.md`, per the owner's decision: SOC 2 is a
framework about a service sold to customers, and dropping the frame let the file
say what actually matters — eleven controls, each with the test or module that
mechanically enforces it, every citation verified. The gaps section was rewritten
too: the old one listed access reviews and pen testing; the real gaps are no
offsite backup, an unverified alert channel, running on a laptop, and zero
demonstrated edge.

### The fee correction had outlived its own correction, again

§5 fixed the model to 26 taker / 16 maker / 52 round trip.
`knowledge/EQUITIES_ARCHIVE_backtest_candidates.md`'s **header** still told every
arriving reader "~40 bps taker (an ~80 bps round trip — **24x** the cost this file
assumed)". That is the orienting sentence of the archive CLAUDE.md points agents
at for method, so anyone reading it concluded the cost bar was nearly twice what
it is.

`tests/test_docs_numbers_match_config.py` now pins it. **The first draft of that
test could not see the file either** — it scanned `.`, `docs` and `deploy`, and
the archive lives in `knowledge/`. Same shape of miss as §23b's whitelist, one
directory over.

### What must never be "fixed", written into the test

`knowledge/crypto_gate_log.md` contains ~40 and ~80 bps and **keeps them.** §1
recorded what was measured and believed then; §5 superseded it *by being later*,
not by rewriting it. That property is what let §7 establish that a PASS had been
measured on a universe produced by a bug.

So the log is excluded by name, and
`test_the_append_only_log_is_excluded_and_that_is_deliberate` asserts the
exclusion still exists AND that the log still contains the old figures — it fails
if someone "corrects" §1 to satisfy a linter. Editing an append-only audit trail
to make a check go green is the most damaging thing available in this repo, and it
now trips a test rather than passing one.

### A check was written and then deleted, on its own evidence

A universe-size check (`twelve|12 markets`) was added alongside the fee one. Its
first run flagged `docs/go_live_checklist.md:77` — *"**§18** replaced the
hand-picked twelve markets with a mechanical screen"* — which is a **true sentence
about history** in a live document, and exactly what that document should say.

Telling a live claim ("we trade 12 markets") from a narrative one requires parsing
English, and `test_docs_reference_real_code`'s own docstring already states why not
to: a test that guesses at prose produces false positives, gets muted, and then
protects nothing. The fee check survives the same objection because the superseded
VALUE is unambiguous — there is no true sentence in which Repete1 currently pays 80
bps. "Twelve" has no such property.

**Deleted, with the reasoning left in the file**, rather than weakened until it
passed.

### The two blockers are now visible

Neither is fixed — both need a value from the owner — but neither is silent.

* `alerting.channel()` answers *which channel would carry an alert* without
  sending one. Previously `send()` returned it, so the only moment you could learn
  the channel reached nobody was during an incident, via the notification you were
  not getting. `health.status()` reports it: **`log-only` is a problem** (every
  other alarm here is decorative), **`desktop` is a warning** — honest on this
  laptop, a lie on the headless Bizon. Not a problem, deliberately, because
  failing health would flip the container HEALTHCHECK on a bot that is fine, and
  `watchdog.py` already carries the scar of an alarm that fired for hours on a
  healthy one.
* `scripts/backup.sh` compares the device of `DEST` against `state/` and warns
  when they match. It **does not fail** — exiting non-zero would stop the one
  scheduled step that makes copies, which is worse than a same-device copy.
  Confirmed live: `backups` and `state/` are both on `/dev/disk3s5`.

### Also corrected in `deploy/README.md`

Option A's `flyctl secrets set` told the operator to set `ALPACA_API_KEY`,
`ALPACA_SECRET_KEY` and four `X_*` keys. **`preflight` refuses to start if any
`ALPACA_*` variable holds a value**, so following the deploy page produced a bot
that could not boot — the same defect as `docs/secrets_rotation.md`'s rotation
schedule. Also: "12 jobs, timezone America/New_York" (it is 15 jobs, UTC, and the
log line reads *"scheduler up — 15 jobs, UTC, no weekend"* — now quoted verbatim so
it is checkable), backups "after 17:00 ET", and "the first 15:45 ET weekday cycle".
A Bizon section was added, with state migration first and the reason: `PaperVenue`
is event-sourced from the ledger, so a partial copy of `state/` does not yield a
partial history, it yields a different bot.

**Suite: 1100 passed, 0 xfailed.** Trial count unchanged at 63; zero adopted, zero
closed trades, zero enabled strategies, zero crypto gate passes ever.

---

## §25 — The bot was barely running, and two of the four defects were mine.

No gate, K stays 63. §23/§24 made the documents true; this looked at what the
system had actually *done*, which nobody had.

```
2026-07-27   preflight_failure 4, cycle_crashed 3, data_error 24,
             stale_data_abort 2, cycle_complete 1
2026-07-28   ops_alert 9                     <-- ZERO cycles completed
2026-07-29   cycle_complete 1, ops_alert 21
```

**Two completed cycles in three days.** I spent 2026-07-28 reporting gate
statistics for a bot that decided nothing at all that day, while the watchdog
paged nine times saying exactly that.

### 1. The decision loop was the only thing with no supervisor

`scripts/run_repete1.sh` ran `$PY src/live.py` in the FOREGROUND as its last
line. The scheduler has 15 jobs and every one is SUPPORT work — dashboard,
watchdog, backup, restore-drill, the two collectors, weekly-learn. So the bot's
support was supervised and its decision loop was not.

The collectors kept running through the 28th *because* they live in the other
process, which is why order-book coverage accrued on a day with no cycles — and
why "collection looks fine" was never evidence the bot was.

Fixed with a backoff restart loop in the launcher (reset after a healthy run,
capped at 300s, and SIGINT/SIGTERM break out so Ctrl-C still means stop), plus
`Restart=on-failure` in `deploy/repete1.service` so both hosts behave alike.

### 2. The recovery existed, was documented, and was never invoked

`watchdog.catchup()` re-runs a cycle that never completed. It fires only under
`if "--catchup" in sys.argv`, and **nothing passed it**. The watchdog detected the
missed cycle, alerted about it, and left it missed.

Worse: in §23b I *corrected* `docs/slo.md` and `docs/runbooks.md` to name
`watchdog.catchup()` as the recovery path. That was false when I wrote it. **I
introduced a fresh instance of the exact defect class I was mid-way through
eliminating** — a documented check that is not a check.

Now a separate hourly `cycle-catchup` job at :35. **Separate, not appended to the
watchdog argv** — which was my first attempt and would have been silent: `main()`
begins `if "--catchup" in sys.argv: ...; return`, so the flag is mutually
EXCLUSIVE with checking. Adding it to `_WATCH` would have disabled all six daily
watchdog checks while looking like it added a recovery.
`tests/test_the_cycle_is_supervised.py` pins both halves, and a third test asserts
the early `return` still exists so the separation's *reason* cannot expire
unnoticed.

### 3. Nineteen of the twenty-one alerts on 2026-07-29 were mine

§21's coverage check runs inside the watchdog, which runs every ten minutes,
against a condition that moves over days. The comment above
`MIN_COLLECTION_COVERAGE_PCT` — which I wrote — says:

> *"An alarm that fires every ten minutes for a week is one an operator learns to
> skim, and this file already carries the scar."*

Then I built one. The owner asked me to "remove all these notifications" and a
large share of them were mine, from yesterday.

Deduped to once per problem per UTC day, reusing the `deploy_drift` pattern from
the equities bot (read the ledger, not memory — the watchdog is a fresh process
every ten minutes, so in-process suppression would reset every run). Keyed on
`alert_key()`, which blanks digits: the message embeds the measurement, so
"40.0%", "42.9%", "36.8%" and "45.5%" were four *distinct strings* for one
problem and plain text dedupe would have missed all of it.

The ledger still records every occurrence. Notifications are rationed; the record
is not.

### 4. I found all of this by hand-querying the ledger

Which is §21's failure one level up. `review.py` now prints an alert summary
grouped by the same `alert_key()` the dedupe uses — two implementations of "is
this the same alert" would drift, and then the summary would disagree with the
thing it explains.

That summary immediately caught a fifth defect: my coverage message contained
`"; "`, the delimiter the ledger uses to join problems, so one problem
un-split into two ("19x order-book collection…" and "19x §22 recedes by this
factor"). Removed at the source.

### The mistake worth recording most

While restarting the bot I ran `pkill -f "scripts/scheduler.py"` — and
**killed the FX bot's scheduler, repeatedly.** All three bots have a file by that
name. `com.repete2.scheduler` is a `KeepAlive` launchd job out of
`~/bots/repete2`, so launchd correctly restarted it each time and I read that as
"something keeps respawning", killed it again, and diagnosed a duplicate-scheduler
problem that did not exist. `launchctl list` showed the exit status as `-9`: me.

No lasting harm — KeepAlive did its job and repete2 was up 69s later with the
right cwd — but the blast radius was another project, and C3 of this very build
was "audit operational separation". Process selection is now done by **cwd**, not
by command name.

It also falsified something else I wrote in §23b: *"there is no launchd here and
there never was."* True for repete1 (no `com.repete1.*` plist), false for the
family — there are eight `com.trading-agent.*` plists and one for repete2. The
runbook I "corrected" was inherited from the bot where launchd IS the mechanism,
and I overreached from "not here" to "never was".

**Suite: 1110 passed, 0 xfailed.** 63 trials, zero adopted, zero closed trades,
zero enabled strategies, zero crypto gate passes ever.

The real verification is tomorrow: at most one collection alert per day, and a
`cycle_complete` for every UTC day. Two in three days is the baseline to beat.

---

## §26 — Alerts that name their sender, and a supervisor that actually works.

No gate, K stays 63.

§25's fix DID work where it was tested: `cycle_complete` at `2026-07-30T00:02:20`,
two minutes after the UTC bar close, and **zero collection alerts on 2026-07-30
against 19 the day before**. The dedupe held.

Then I tested the part I had only asserted, and it was broken.

### The supervisor was dead on arrival

§25 wrapped `live.py` in a restart loop. I verified it *started* and reported the
fix as done. It could not restart anything:

```
scripts/run_repete1.sh: line 129:  5207 Killed: 9    $PY src/live.py
```

`run_repete1.sh` runs under **`set -eu`** (line 11). Under errexit a bare command
exiting non-zero terminates the shell IMMEDIATELY, before the next line — so
`$PY src/live.py` / `RC=$?` never reached `RC=$?`. The supervisor exited with its
child. **The exact failure it was written to prevent, shipped as the fix for it**,
defeated by a line at the top of the same file.

`|| RC=$?` makes it a *tested* command, which errexit ignores. Re-tested by
SIGKILL: `live.py died (rc=137) after 22s — restarting in 5s`, new PID. That is
S2 passing, and it only passes because I stopped trusting the change and crashed
the thing.

Worth separating two behaviours that look alike: a SIGTERM produced
`live.py exited cleanly (rc=0) — not restarting`, which is CORRECT — `live.py`
finishes its tick and exits 0 on TERM, and a deliberate stop must stay stopped. My
first test used TERM and read the right behaviour as a failure.

### Two more defects, both caused by my own testing

**Orphaned children.** The trap was `TERM INT` only, so when the loop `break`s on a
clean exit the script ends and leaves the scheduler and web server running. Each
launch starts another. I accumulated **three scheduler+caffeinate pairs** —
tripling every collection sweep and watchdog run, and §25's per-day dedupe hid the
symptom. Now `trap ... EXIT`.

**No single-instance guard.** Nothing stopped a second launch from doing that in
the first place. Added, selecting by cwd — a name-based check would have seen
another bot's scheduler and refused to start this one.

### No alert said which bot sent it

All three bots on this host emitted the byte-identical titles
`"Trading agent needs attention"` and `"Trading agent: late catch-up"`, from
`src/watchdog.py`, inherited unchanged through two forks.

So a desktop banner named none of them. That is the root of the owner's
notifications reading as one undifferentiated blob — and it is why my first
attribution of their screenshot blamed the wrong bot. The convention already
existed (`"Repete1: decision cycle failed"`) and had simply never been applied to
watchdog's two, in any repo. Fixed in all three at the owner's instruction, as a
`BOT` constant rather than edited literals, so the next inherited `notify()` call
inherits the right name too.

### The footgun that started this, closed

`scripts/stop_repete1.sh`: select by **working directory**, send **TERM**, never
`pkill -f`. Documented at the top of `docs/runbooks.md` because the next agent will
reach for `pkill` exactly as I did.

### A guard caught me, and the right fix was to delete my check

`tests/test_alerts_are_attributable.py` listed the equities bot's name as a
forbidden title — and `test_repo_isolation.py` promptly failed the file for
*naming* it. The older guard is stronger: it forbids that string anywhere in this
tree, not just in alert titles. Two guards for one property is how they drift, so
mine went, along with the references my §26 comments had introduced into
`run_repete1.sh`, `watchdog.py` and `stop_repete1.sh`.

**Suite: 1116 passed, 0 xfailed.** 63 trials, zero adopted, zero closed trades,
zero enabled strategies, zero crypto gate passes ever.

The pattern across §23–§26 is worth naming: every one of these was a claim I had
written down and not executed. The docs claimed a deleted module, a recovery that
never ran, a supervisor that could not restart. **Prose and untested shell are the
two places in this repo where nothing checks whether I was right.**

---

## §27 — The suite reads shell. Now it runs it.

No gate, K stays 63.

§26's finding generalised: **five of six production shell scripts are never
executed by the suite.** The exception is `scripts/backup.sh` —
`tests/test_backup_restore.py` genuinely runs it eight times including a real
round trip, and that is the script protecting the track record, so whoever wrote
those tests picked the right one.

The only other shell execution anywhere in 1,123 tests is `sh -n`: a syntax
check. §26's broken restart loop was syntactically perfect and passed it, along
with four tests that READ the file and asserted the right strings were present.
It was found by SIGKILLing a live process by hand, which is not a repeatable
check.

And the class was already documented here. `test_container_can_actually_serve`
opens with *"entrypoint.sh backgrounds it with `&`, so `set -eu` never saw the
exit."* A known hazard, written down, that recurred anyway.

### The seam, and why it is not a copy

`SUPERVISE_ONLY=1` plus `LIVE_CMD` skips startup and runs **the same loop
production runs**. Precedent: `backup.sh`'s header says its `AGENT_ROOT` override
"exists for the offline test fixture only". A test against a duplicated loop
would prove nothing about the real one — `fills.simulate_fill`'s argument, applied
to shell.

Six executing tests now cover the supervisor's whole contract: crash → restart,
backoff grows, backoff capped, clean exit → stop, and rc 130/143 treated as
deliberate.

### The demonstration arrived by itself

Renaming the invocation to `$LIVE_CMD` broke
`test_the_restart_survives_errexit`, which had hardcoded `"src/live.py || RC=$?"`.
**The string check failed on a refactor that changed no behaviour, and would have
passed on the §26 bug that broke everything.** The executing test passed both
times. That assertion now checks the invariant instead, and points at the
executing test as the real guarantee.

### I did the thing I warned against, in the same file

The first version of the stop-script test executed `stop_repete1.sh` for real and
**stopped the running bot.** Its own docstring said, in as many words, that "a
test that stopped the RUNNING bot to check the stop script would be a test that
takes production down every time the suite runs" — and the assertion
(`or "stopping" in stdout`) was loose enough to accept the harmful path, so it
passed while doing exactly that. Confirmed by checking: four processes before,
zero after.

Fixed with `--dry-run`, which is the better design anyway: the part worth testing
is the SELECTION — does it pick this checkout and skip the other two bots? — and
that needs no signal at all. A second test now walks every pid the dry-run names
and asserts its cwd is this checkout, which is §26's cross-bot kill as a check.

The suite is verified not to stop the bot: 1,123 tests pass with all four
processes still up afterwards.

**63 trials, zero adopted, zero closed trades, zero enabled strategies.**

Three sections in a row where the defect was mine and found by running the thing
rather than reading it. §25 shipped a supervisor that could not supervise, §26
shipped a test that could not catch it, §27 shipped a test that took production
down. The common factor is not shell — it is that I keep verifying by inspection
and reporting it as verified.

---

## §28 — the collection shortfall, measured: §22 is not reachable on this host

**No gate, no trial, no profit. K stays at 63.** This section is about whether the
one remaining line of enquiry can be fed at all.

### The check I promised, and what it found

§25's dedupe was to be verified by "at most one collection alert per day". The
ledger showed **six** `ops_alert` rows on 2026-07-30 and I read that as a failure.
It was not: `watchdog.main()` writes the ledger row on **every** run by design and
rations only `notify()`, which the comment at that line states outright. The log
shows 1 notification and 5 suppressions. **The dedupe works — I measured the wrong
thing**, against a distinction I had written down myself three sections earlier.

But the alert being deduped was itself the finding.

### 15 of 25 hours missing, and the number that matters

`coverage_pct` was 44.0%. It had been reported for days as a thing that would
improve. The arithmetic says otherwise:

| | |
|---|---|
| observed / elapsed | 11 h / 25 h = 44.0% |
| §22 trigger | 30 days at ≥ 90% |
| remaining hours in that window | 695 |
| **those hours must average** | **91.7%** |
| observed rate | 44.0% |

And the decisive fact is structural, not about this week: **cumulative coverage
tends to the forward rate, so a forward rate below the floor never reaches the
floor** — at 30 days or 300. Below the floor, waiting is not a strategy; it is
what makes a structural deficit look like bad luck.

**§22 is not reachable on this laptop.** The always-on host stops being an
improvement and becomes the binding constraint on the only line of enquiry this
bot has left. `deploy/repete1.service` already exists for one.

### The mechanism, and the half of it that was fixable

`collect-orderbook` fires at HH:05. If the scheduler is not running at that
instant the hour is gone **permanently** — a book cannot be refetched, which is
§16's entire premise, and unlike a bar there is no backfill. A restart at HH:20
then sat idle for 40 minutes with the hour already forfeit.

Fixed: `--if-missing` samples only when the current hour holds no sample, and the
scheduler runs it at startup once its :05 slot has passed. Idempotence lives in
the collector (`hour_sampled()`), so the supervisor's restart loop cannot become a
request loop against Kraken. Verified by execution across all three boundaries —
started at :20 runs it, at :02 and exactly at :05 leave it to the loop.

### The false diagnosis I nearly shipped

The shortfall message said the host "was asleep or the scheduler was down" — one
phrase for two failures with different fixes, asserted without evidence for
either. Replacing a guess with a measurement was the point of `classify_gaps()`.

**The first implementation was wrong, and confidently so.** It asked the ledger
whether the bot was alive during a missed hour and reported hours with activity as
collector defects. Run against real data it flagged two. Both were false: there
have been **zero** attempted-but-failed hours.

The bug was a cross-process inference. Repete1 is four processes; the collector
runs from the **scheduler**, while `cycle_complete` is written by `live.py`. So an
hour in which live.py finished a cycle and the scheduler was down read as "the bot
was alive, therefore the collector failed."

That is **§25's finding in mirror image**. §25 established that the collectors
kept running precisely *because* they live in the other process, "which is why
'the collector looks fine' was never evidence the bot was." Same process boundary,
crossed in the opposite direction, three sections later, by the same hand.

The corrected discriminator needs no inference and no second source, because both
states are already recorded in the collector's own file: `sample()` writes a row
per symbol with `ok: false` and a reason when a symbol errors. So

* rows present, none usable → the sweep **ran** and failed → fix in code
* no rows at all → the sweep was **never invoked** → fix with uptime

Against real data: 0 and 15. Which is correct, and which points at the host rather
than at a collector bug that does not exist.

### What is deliberately still not known

`never_ran` does **not** distinguish host sleep from an operator restart. Nothing
recorded here can, and the note in the output says so rather than implying a
precision the data does not have. `pmset` would have answered it on this Mac and
nowhere else — the macOS-only divergence `run_repete1.sh`'s header exists to
avoid.

Also deliberately unnamed: `forward_rate_required` returns
`converges_at_observed_rate`, not `converges`. The forward rate is not observable;
the observed cumulative rate stands in for it. §8 (+10.15% in-sample, −7.29% out)
is this repo's standing evidence for what a confidently-named estimate costs, so
the assumption is carried in the field name where a reader cannot miss it.

### Attribution of the 15 lost hours

Honest accounting, since §27 ended by naming the pattern: 7 hours were overnight
sleep, and **8 were mine** — the §26 restarts and the §27 test that stopped
production. The startup catch-up removes most of the second category. Only an
always-on host removes the first.

**63 trials, zero adopted, zero closed trades, zero enabled strategies, zero
crypto gate passes ever.**

The pattern from §27 held for a fourth section, with one change worth noting: this
time inspection produced a *false positive* rather than a missed defect, and what
caught it was running the classifier against real data before believing it. The
lesson is the same one and it now has four data points: **the measurement has to
be made before the claim, not after.**

### §28b — the stop script, found while using it

Restarting to pick up §28's code, `stop_repete1.sh` reported "2 process(es) still
up" where a hand count said 1. Chasing the discrepancy rather than assuming a race
turned up two defects.

**The verification loop checked a different set than it stopped.** The stop loop
signalled four patterns including `uvicorn web.app`; the loop that then verifies
they went down listed only three. So a web server that ignored TERM was never
counted, and the script printed "repete1 stopped" while port 8787 was still held —
after which the next `run_repete1.sh` starts, uvicorn fails to bind, and the bot
runs with a dashboard that silently does not work. It is the operator's only
window into a bot that runs while they sleep. The single-instance guard in
`run_repete1.sh` had the same omission and now matches uvicorn too.

Fixed with one `_PATTERNS` list read by both loops — the rule this repo already
applies to `fills.simulate_fill` and `venue.venue_for()`, applied to the list of
what counts as the bot.

**And consolidating the two lists introduced a worse bug than the one it fixed.**
The first draft was:

    patterns | while IFS= read -r pattern; do ... FOUND=$((FOUND + 1))

A pipeline puts the loop in a **subshell**, so `FOUND` increments a copy and the
parent still sees 0. In the real path that means the script sends TERM to
everything, hits `[ "$FOUND" -eq 0 ]`, prints "no repete1 processes were running"
and exits 0 — skipping the verification entirely, while telling the operator
nothing was there. Same family as §26's `set -eu` defect: correct-looking shell
whose control flow does something else.

Iterating with `IFS` set to newline keeps the loop in the current shell. Newline
rather than spaces because `uvicorn web.app` contains one, and normal word
splitting would quietly turn it into two patterns that match nothing.

**This time I verified the test detects the bug before believing it.** A copy of
the script with the subshell form reintroduced, run against a live process:

    BROKEN:  lists 5 processes, then "no repete1 processes were running"
    FIXED:   "--dry-run: 5 process(es) would be stopped"

The first attempt at that check was itself wrong — run from the scratchpad, `ROOT`
resolved to the scratchpad's parent and matched nothing, so the harness reported
"NOT CAUGHT" for a test that is fine. Re-run from inside the repo it caught it
cleanly. Recording that because the failed harness looked exactly like a failed
test, and stopping there would have thrown away a working check.

Startup catch-up verified in production on the restart: `catch-up
collect-orderbook: started at :47, past its :05 slot` → ran → and the data file
stayed at 177 lines, because hour 01 already held a sample. The idempotence guard
working on the real path, not a stub.

1,144 tests pass; five processes up; dashboard HTTP 200.

**63 trials, zero adopted, zero closed trades, zero enabled strategies.**

---

## §29 — a news layer, wired into the decision path

**No gate, no trial, no profit. K stays at 63.** This adds an INPUT. It is not
evidence that the input helps, and it cannot by itself cause a trade.

### Why, and the objection that was overruled

Asked whether the bot trades and whether it reads news, both answers were no, and
both were verified rather than recalled: the ledger has never held a fill, order
or position event; all 24 `decision` records are `hold` / `executed: false` /
`llm_review: null`; and `news_ctx` / `market_context_block()` were unconditionally
empty since the fork.

I argued against wiring news in now — with zero enabled strategies it colours a
decision path that produces no entries, and §8 is the standing evidence against
adding ungated inputs. The owner chose it anyway after seeing that. Recorded once,
implemented in full.

The case FOR it is real and worth stating: every one of the 63 trials was a
different transform of the SAME price bars. This is the first genuinely different
information axis, and unlike §22 it is not blocked on hardware.

### What made it small

The equities plumbing survived the fork; only the SOURCE was cut.
`market_context_block()` was already called from `context_for_llm`, and `main.py`
still carried `news_ctx`, `is_nominated`, `news_note` and the
`detail_tag="news-nominated"` ledger path. Every one of them was written and
tested for the empty case, because "" was the branch the equities bot took
whenever context was stale. **So §29 changed no readers.**

### The latent bug it activated

`news_entries` was initialised and incremented, and its comment has read
"(hard cap)" since the fork — **while nothing ever compared it to anything.**
There was no cap. It could not fire only because nothing was ever nominated, and
wiring a source in is precisely what would have made it live. Now checked BEFORE
`_process_signal`, since a counter that only observes after the order is placed
is not a cap.

### Why untrusted text on the live path is tolerable

`llm.review_signal(signal, ...)` judges a signal a deterministic strategy ALREADY
produced, returning only approve/downsize/veto with scale clamped to [0,1] —
"the LLM can only reduce, never enlarge" — and the hard rails run after it,
unoverridable. **An injected headline cannot manufacture a trade.** The worst case
is the judge being neutralised, which is the `llm.enabled: false` state the bot
already supports and ledgers.

That bound is now pinned by a test, because the whole design leans on it. On top
of it: `sanitise()` strips control/bidi characters and blanks instruction-shaped
phrasings, and `_SYSTEM` tells the judge that context blocks are data, never
instructions.

### Four defects found by RUNNING it, not reading it

  1. `matches_symbol` returned True for "The deal is near completion" → NEAR/USD
     and "Follow this link for details" → LINK/USD. Word boundaries do not
     separate a ticker from the English word it happens to be, and three of the
     21 markets collide that way. Fixed by matching the ticker CASE-SENSITIVELY
     (headline convention supplies the caps) with case-insensitive aliases.
  2. The collector fetched 111 headlines and degraded with "Could not resolve
     authentication method" — `scheduler.py` runs jobs as subprocesses inheriting
     its environment, and `run_repete1.sh` loads `.env` only inside its preflight
     heredoc. The key was on disk and absent from every scheduled job that does
     not load it itself.
  3. The market summary was truncated mid-word at 180 chars — the PER-HEADLINE
     cap — in **two** call sites. Fixing one left it looking fixed.
  4. "21/21 symbols have context" was true and meaningless: the market-wide
     summary makes every block non-empty. 5 of 21 had headlines of their own.

### And one test that proved nothing

`test_the_block_drops_whole_items_rather_than_half_a_headline` used a fixture of
all "X", so a headline cut mid-word still ended in "X" — it passed against both
the correct and the buggy implementation. Caught only by running the old slicing
code against it and watching it stay green. The fixture now ends each title with
a sentinel, and the old implementation duly fails it.

### An over-reach the existing suite caught

My first preflight rule FAILED on `news.enabled: true` with `llm.enabled: false`.
Two existing tests refused it, correctly: `test_turning_the_judge_off_is_allowed`
pins the documented escape hatch — "set llm.enabled: false to trade on rules
alone; that is a decision, not a silent hole". An orthogonal feature was vetoing
a supported choice. Preflight refuses what is unsafe or quietly wrong about
trading; wasted background work is neither, so the warning moved to the collector
where the waste happens. Nominations-without-news stays a preflight failure,
because that one is a false belief about entry selection.

### What is deliberately still off

`news.nominations.enabled: false`. Context COLOURS a signal that a gated strategy
produced; a nomination scans a symbol no backtest ever covered. Different risk,
separate switch, and only the first was asked for.

### The consequence to keep in view

With zero enabled strategies, `review_signal` is never called, so **news reaches
the judge zero times.** This is correct, complete, and observably inert until a
strategy is enabled — and §29 does not enable one, because re-instating meanrev
after its pre-declared kill criterion fired is a materially bigger decision than
adding an input.

1,191 tests pass (+47). Five degradation paths verified by execution: fresh,
stale, corrupt, missing, unreachable feed.

**63 trials, zero adopted, zero closed trades, zero enabled strategies, zero
crypto gate passes ever.**

---

## §30 — newsletters, and the crowding-out bug that wore two hats

**No gate, no trial, no profit. K stays at 63.** This widens an input and repairs
two defects in §29.

Asked whether the bot reads newsletters, the answer was no — §29 added four crypto
news *desks*, and there is no email ingestion anywhere in the tree. Most crypto
newsletters publish public RSS, so adding them needed **no credential**, which
keeps the invariant that this repo holds none.

Probing candidates with §29's own `fetch`/`parse_rss` mattered more than the
feature.

### Defect 1: nothing filtered an item's own age

`published` was collected on every item from §29 and **never read**. The staleness
rule guarded the CACHE — when we last fetched — not the items inside it.

Two of six working candidate feeds serve months-old content as current:

| feed | items | newest | note |
|---|---|---|---|
| `blockworks` | 50 | **204 days** | — |
| `dlnews` | 40 | **84 days** | headline *"DL News is closing"*; the outlet shut down |

**A dead feed does not return an error.** It returns a perfectly valid document,
forever. News desks roll fast enough to hide this — the oldest live item was two
days old — so a weekly newsletter was precisely the input that exposed it. This
is §29's own argument one level down: *"Old headlines read as current to a model
and nothing in the text reveals their age."*

Fixed: `parse_date()` (RFC-822 and ISO-8601, both present in real feeds),
`fresh_items()` dropping anything past `max_item_age_hours: 48`, and an
unparseable stamp treated as too old. Verified against the live dead feeds:
blockworks 50 → 0 fresh, dlnews 40 → 0.

Also added: each feed's newest-item age in `--coverage`, flagged `QUIET >7d`. "The
fetch succeeded" was never evidence the source is alive, and nothing else would
have caught a publication that quietly closed.

### Defect 2: the summary only ever saw the first two feeds

`distill` capped at `items[:60]`, sliced in **feed order**. Measured on the live
four-feed cache:

```
coindesk       24 of 24 reached the summary
cointelegraph  30 of 30
decrypt         6 of 38
theblock        0 of 19      <- entirely absent
```

The market summary the judge reads was built from two sources. Adding four
newsletters would have pushed Decrypt out too while the newsletters contributed
nothing — a feature that appears to work and changes nothing. Per-symbol matching
was unaffected (`for_symbol` reads the full list), so this degraded the summary
only.

### And the fix for it re-created it

Sorting by recency looked correct and was **measured wrong**: pure recency hands
the whole budget to whoever publishes most often, so four desks filing hourly
crowded out the weekly letter and `pomp` went to 0. The inputs §30 exists to add
were the ones being squeezed out — Defect 2 again, wearing a different hat.

`balanced_by_source()` gives every live source a slot before any source takes a
second, then spends the rest by recency. Cadence is not relevance: a weekly macro
letter is not one-fortieth as important as a wire desk because it files less.

```
before §30 (feed order)     3 of 8 sources reached the summary
recency only                7 of 8
round-robin                 8 of 8
```

Both tests were checked against the OLD behaviour before being believed, and both
fail it.

### Newsletters are labelled as opinion

A desk reports; a newsletter is one writer's directional thesis. Shown
identically, a confident bull case reads with a wire report's weight. Items now
carry `kind`, and the judge sees `[pomp opinion]` — the same reasoning as §29's
"external, UNVERIFIED" header, one level finer.

### The feed list moved to config

Which publications to trust is the owner's taste, not a literal in a script. Eight
entries in `config.yaml`, with the rejected candidates recorded beside them
(blockworks and dlnews stale, glassnode 403, messari 404, milkroad no parseable
RSS) so nobody re-adds them. The four newsletters — Bankless, The Defiant, Pomp,
Crypto is Macro Now — are the agent's picks for angle spread, since the owner
named none, and are a one-line swap.

1,226 tests pass (+35). The bot survived the suite; five processes up.

**63 trials, zero adopted, zero closed trades, zero enabled strategies.** With
nothing enabled the judge is never called, so none of this reaches a decision.

---

## §31 — the comment that routed an operator toward halting the bot

**No gate, no trial, no profit. K stays at 63.** A one-line correction, recorded
because of how it was found and what it would have cost.

The owner asked whether the bot can trade on PaperVenue or whether they should
create an Alpaca account. The answers are yes and emphatically no — and the
question was the finding.

`config.yaml` read:

```yaml
  starting_equity: 100000        # Alpaca paper account starting capital
```

There is no Alpaca account. **PaperVenue holds that money**, seeding its opening
deposit from that very key (`venue/paper.py`), with the dashboard reading the
same key for P/L — one number, single-sourced, nowhere for two to disagree. Only
the attribution was wrong, left over from the fork.

But an operator reading that line would reasonably go and create the account, and
doing so **stops the bot**. Verified by execution rather than by reading the docs:

```
$ ALPACA_API_KEY=x .venv/bin/python -c "...preflight.run(cfg)"
FAIL: exchange credentials present in the environment: ['ALPACA_API_KEY'].
      Repete1 must hold NONE — it reads public data and simulates its own fills
```

`docs/secrets_rotation.md` already carried the right instruction — *"DO NOT CREATE
ONE"* — and even noted that an operator following its own earlier version "would
have created the exact condition that halts the bot." The config comment was the
remaining path to the same mistake, and config is where someone actually looks.

This is §23b's class at its most expensive. Not a wasted hour: a stopped bot,
reached by doing exactly what the file said.

### The sweep, and what was deliberately left alone

`config.yaml` names Alpaca four more times — "ccxt timeframe, NOT Alpaca's
`1Day`", "the equities check compared Alpaca vs yfinance" — and every one is
history or contrast that must stay. The SPY/QQQ/DIA/IWM line is §24's record of
why symbol rotation exists. `starting_equity` was the only line describing a
CURRENT value in terms of a vendor this bot does not use.

### And the guard test failed on its own subject

The first version forbade order-capable vendor names anywhere in the
`starting_equity` comment. It failed immediately — on the new comment, which
explains the §31 fix and therefore has to name `ALPACA_/KRAKEN_/COINBASE_/
BINANCE_` to say what preflight refuses.

Its own docstring had already warned about this, citing
`test_alerts_are_attributable.py` deleting its own over-broad check after the
identical collision. **Writing the warning and then shipping the thing it warns
about is the §27 pattern**, and this is its fourth appearance.

Scoped to the SUMMARY half of the comment — everything above the bare `#`
separator — because that is where attribution lives and what a skimming reader
takes as the answer. History lives below the separator and stays checkable.

Three further checks pin the rest: the comment must name PaperVenue (removing the
wrong answer is half the fix; the reader still needs the right one), neither
`paper.py` nor `dashboard.py` may hardcode 100000, and preflight must still refuse
an order-capable credential.

1,230 tests pass (+4). Venue state unchanged and verified: equity 100000.0, cash
100000.0, no positions.

**63 trials, zero adopted, zero closed trades, zero enabled strategies.**
PaperVenue was always the venue. Paper is not what is stopping this bot from
trading; the absence of an edge is.

---

## §32 — xsmom enabled, deliberately, despite failing its gate

**No gate, no trial, no profit — this is not a 64th trial and does not touch K.**
A pre-registered exception, not a new measurement.

### The request, and the correction that came first

Asked to "give it paper money to start trading and learning," the premise needed
fixing before the request could be answered: **PaperVenue already held $100,000,
all cash, zero positions.** Capital was never the blocker. The blocker was that
§20's verdict is unambiguous — *"Every strategy in this repo has now been
measured on a universe chosen by a rule. None of them works on it"* — so there
was nothing un-rejected left to trade with.

Put plainly to the owner along with what "learning" actually requires (the
Thompson allocator and lesson-ranking system learn from CLOSED TRADES, and there
have been zero, ever), the choice was: revive a rejected strategy anyway, wait
for genuinely new evidence (§22's re-gate, or the §29/30 news layer once it has
had time to accumulate), or pursue an unexplored angle as a proper new trial.
**The owner chose to revive one, informed.** That is their call to make, and this
section implements it without softening what it is.

### What was actually enabled, and why xsmom

`strategies.xsmom.enabled: true`. Of the six, it came closest to clearing the
bar and still failed it:

```
2026-07-15 [old 12]  -11.55%  PF 0.476            FAILED
§20 [21 mkts]         +1.63%  PF 1.087, 1.5x PF 0.927   FAILED (stress arm)
```

PF 0.927 under the mandatory 1.5x fee-stress arm is **below 1.0** — the stressed
simulation loses money gross of framing. This is not "a small strategy that might
still be fine"; it is a measured loser, closest of six.

### What it is for

Exercising a pipeline that has never run end to end against a real signal: paper
fills, the LLM judge (now with news/knowledge context attached, for the first
time since §29 — `llm.review_signal` was never previously called with nothing
enabled), the allocator, the journal, the dashboard. **It is expected to lose
money on average.** A paper loss here is not new evidence; the evidence was
already in before this was switched on. A paper WIN is equally not evidence —
§8's false strategy theorem is the standing reason to distrust a good-looking
result from a strategy that failed pre-registered testing.

### Verified by execution before committing

Read-only, against the real venue's data client — no write reached the running
process or the ledger:

```
xs_ctx = strategies.prepare_cross_sections(cfg, all_bars)
strategies.generate('xsmom', sym, bars, cfg, False, cross_section=xs_ctx.get('xsmom'))
```

Ranked all 21 markets correctly by 231-bar momentum and produced a live `buy` for
**NEAR/USD** (rank 1/21, top 25% of universe) against the other 20 holding. That
signal will reach the judge, the rails, and PaperVenue for real at the next bar
close, 2026-08-02T00:01:30 UTC — not forced early, to avoid a second `live.py`
instance racing the running one against the same event-sourced store.

### Pre-registered review, and its known limitation

**2026-11-01 or 20 closed trades, whichever comes first.** At that point xsmom
reverts to `enabled: false` absent a decision to renew it. §20 measured ~25
trades over a ~529-bar (~1.4yr) window for this arm, so 20 may take a while —
noted now rather than quietly extended later.

The question at that review is NOT "did it make money" — §20 already answered
that — it is whether the pipeline worked. **This has the same limitation §12's
meanrev review had: the review is a date, and nothing in this repo fires on
one.** `tests/test_docs_numbers_match_config.py` guards the checkpoint's text
from being silently dropped, but does not and cannot enforce that anyone acts on
it. Recorded as a limitation rather than quietly built around.

### What was updated to stay honest

`CLAUDE.md`'s Phase 8 row and the "zero enabled strategies" claims in the §28/29
paragraphs were stale the moment this landed; corrected in the same commit.
`docs/operational_controls.md`'s "no demonstrated edge" item now names xsmom as
a labeled exception rather than letting "zero enabled strategies" quietly go
false. Guard tests in `test_docs_numbers_match_config.py` pin the "FAILED" /
"not an adopted strategy" / review-date language in `config.yaml` itself — the
first version of one of them failed against its OWN new comment, because a
hand-wrapped phrase crossed a line break; fixed by normalizing the prose before
matching rather than reshaping the comment to fit a fragile check.

1,233 tests pass (+3). Bot restarted on the new config, confirmed live:
`ok — paper, 21 markets, enabled: ['xsmom']`.

**63 trials, zero adopted, zero closed trades. One measured loser now running on
purpose, on a clock, for a reason unrelated to whether it wins.**

---

## §33 — the dashboard was never actually published, and three stale claims found while checking

Asked why no trades were visible on the dashboard after §32's first paper fill,
the investigation found the trade WAS rendering correctly locally — and that the
public dashboard has likely never been viewable by anyone, for two independent
reasons, plus two unrelated stale-doc claims sitting in the same paragraph.

### Finding 1: `CLAUDE.md` documented a URL for a repo that does not exist

`https://connorshibley.github.io/repete1-dashboard/`. Confirmed:

```
$ gh api repos/connorshibley/repete1-dashboard  (implicit via git ls-remote)
fatal: repository 'https://github.com/connorshibley/repete1-dashboard.git/' not found
```

### Finding 2: the REAL repo has never had GitHub Pages enabled

`.site/` (the nested checkout `scripts/publish_dashboard.sh` pushes) points at
`github.com/connorshibley/repete1` — confirmed correct per the "repete1 naming
trap" memory: that repo IS the dashboard despite a misleading description. It has
been receiving every push correctly (`.site` `main` in sync with `origin/main`,
190+ "site update" commits) and its content is current — `NEAR/USD` from §32's
first fill is in the exact file (`.site/index.html`) sitting at the pushed HEAD.

But:

```
$ gh api repos/connorshibley/repete1/pages
{"message":"Not Found", ...}
```

**GitHub Pages was never switched on.** Months of correctly-generated, correctly-
pushed dashboard updates have had nowhere to be served. `scripts/publish_dashboard.sh`
never surfaced this because its whole design is "clean no-op on any failure" —
correct for not breaking a trading cycle, but it means a repo-settings gap looks
identical to a working pipeline from inside the bot.

**Not enabled by this section.** Turning on Pages makes the repo's content
externally reachable at a public URL — a "publish/modify public content" action —
so it's left for the owner to confirm rather than done silently.

### Two unrelated stale claims, found adjacent while fixing the URL

`CLAUDE.md`'s architecture table said regime detection runs "from SPY bars" and
that news "refreshes hourly 9:25-15:25 ET ... via com.repete1.newsbrain." Neither
is true and neither was asked about — found only because they sat in the same
paragraph being corrected:

* `com.repete1.newsbrain` is a launchd job that has never existed here — §23
  established Repete1 has NO launchd jobs; scheduling is in-process
  (`scripts/scheduler.py`). The real job is `collect-news`, hourly, 24/7 (there
  are no market hours), via `claude-sonnet-5` (`llm.model`), not a hardcoded
  haiku model on equities hours.
* "SPY bars" is leftover naming, not a live dependency. Checked at the actual
  fetch site, not the prose: `main.py:1110/1142` reads
  `venue.reference_symbol` (`BTC/USD`) and `main.py:231-232` says so explicitly
  — *"SPY does not exist on a crypto venue. BTC is this market's benchmark."*
  `review.py`'s function was renamed `reference_benchmark_pct` at §23; "SPY"
  survives only as descriptive text in docstrings/comments across
  backtest.py/dashboard.py/journal.py/risk.py/scorecard.py, none of which fetch
  real equities data.

### The crypto-only question, answered from the fetch sites rather than the docs

Asked directly whether this agent is crypto-only: yes, and it always has been.
The full, exhaustive symbol universe — everything this bot can ever hold — is
21 `*/USD` crypto pairs. Alpaca, the one broker in this codebase's history
capable of touching equities, is structurally deleted:
`tests/test_repo_isolation.py::test_no_alpaca_code_anywhere` and
`::test_the_broker_module_is_gone` fail the build if it returns. Every news feed
(§29/30, eight sources) is crypto-specific by construction.

1,233 tests pass, no regressions — this section is documentation-only pending
the Pages decision. **63 trials, zero adopted.** One position open (NEAR/USD,
§32), zero closed trades.

### §33 addendum — Pages enabled, verified live

Owner confirmed. Before changing visibility, re-verified independently (fresh
clone, not trusting the earlier audit's memory of it): the repo's entire
history holds exactly two files ever tracked — `dashboard_data.json`,
`index.html` — and a full-history grep for credential-shaped strings
(`sk-ant-api`, `api_key=`, `password=`, PEM headers) returned nothing.

`gh repo edit connorshibley/repete1 --visibility public` → confirmed
`{"visibility":"PUBLIC"}`. `gh api -X POST .../pages` (source: main, path: /)
→ `{"status":"building", "html_url":"https://connorshibley.github.io/repete1/"}`.

Polled rather than assumed: HTTP 404, 404, then 200 on the third attempt (~30s
build time), body confirmed containing `NEAR/USD` — §32's live position,
publicly visible for the first time since this bot began running.

**The dashboard is now actually what its months of commits always intended it
to be: reachable.** https://connorshibley.github.io/repete1/

---

## §34 — the kill-switch flatten now retries and re-verifies, ported from a real incident on the sibling bot

**No gate, no trial, no profit.** A confirmed safety gap, closed — not a strategy
decision.

Asked "what's next," a survey of the owner's other trading bot (crypto-agnostic,
run via a research subagent) turned up a fix already adopted there for a real,
named failure mode: **"the worst state in the system."** `flatten_all()` was
called once when the daily-loss kill switch engaged; an exception just logged
`kill_switch_flatten_failed` and returned. Nothing retried. Nothing re-checked
whether the position was actually gone. "The call didn't raise" and "the
position is actually closed" were treated as the same fact when they are not.

Checked against repete1's own `src/main.py` before assuming the gap applied
here too: **it did, identically.** Same single try/except, same unverified
success, and — because `check_halt()` gates the sell path through
`pre_trade_checks` the same as the buy path — once HALT engages, a partially
flattened position cannot be closed through ANY automated path. The only
recovery was a human reading a log line.

This is no longer hypothetical for repete1 specifically: §32 put a real paper
position on the book (NEAR/USD, via xsmom, a strategy chosen BECAUSE it is a
known loser). A drawdown large enough to trip the daily-loss kill switch is not
a remote scenario for the one strategy running.

### The fix

`flatten_until_confirmed(venue, ledger, max_attempts=5, delay_s=3)` — calls
`flatten_all()`, then re-reads `venue.positions()` regardless of whether the call
raised, and only declares success when that list is actually empty. Retries up
to the bound; exhausting it logs a NEW terminal event,
`kill_switch_flatten_abandoned`, naming the still-open position, added to
`docs/incident_response.md` as Sev 1. The name is borrowed deliberately from the
sibling bot's own vocabulary for the identical failure class, so the same
incident reads the same way across both of the owner's projects — described
generically in the source rather than by path or URL, since
`tests/test_repo_isolation.py` correctly refuses ANY reference into that live
checkout, comments included, and caught the first draft of this comment doing
exactly that.

### What the tests found, twice, before this shipped

1. The EXISTING kill-switch test's fixture never actually simulated a position
   staying open — it asserted `kill_switch_flatten_failed` fired on an exception
   while `positions()` was already `{}` by construction. Under the new code that
   fixture correctly reports `kill_switch_flatten_confirmed`: the position really
   was empty, and the old code would have logged a false alarm. The test was
   updated to assert the more correct behaviour, and two NEW tests were added
   using a fixture that genuinely keeps a position open, which the original
   never exercised at all.
2. A live Python gotcha in the new code itself: `run_cycle` called
   `flatten_until_confirmed(venue, ledger)` relying on the function's *default*
   argument values. Defaults bind ONCE at module load; a test monkeypatching
   `main.FLATTEN_MAX_ATTEMPTS` to 3 afterward had no effect on a call using the
   baked-in default of 5 — caught because the test asserted exactly 3 flatten
   calls and observed 5. Fixed by passing the globals explicitly at the call
   site, where they're looked up fresh on every call.

Two downstream regressions caught by the full suite and fixed, not silenced:
`docs/runbooks.md` still grepped for the retired `kill_switch_flatten_failed`
event (updated to explain `confirmed` vs `abandoned` as different facts
requiring different operator responses), and the source comment crediting the
sibling bot originally named its checkout path directly, which
`test_no_source_file_references_the_equities_checkout` correctly refused.

### Found and deliberately NOT built this round

The same survey found a second, real, currently-latent gap: the drawdown
circuit breaker (`max_drawdown_pct: 10.0`, armed) never releases once tripped,
because `update_high_water()`'s peak by design never ratchets down — confirmed
in `src/risk.py`, matching a measured incident on the sibling bot (245,213 buy
signals, 29 trades, 99.43% blocked by the identical one-way latch). Not fixed
here: the backtester keeps its own in-memory running peak and calls the same
`drawdown_pct` arithmetic for parity, so a correct fix has to touch both paths
identically or it becomes divergence — this deserves its own focused pass
rather than being bolted on. Recorded so it is not lost.

1,235 tests pass. Bot restarted, running the new code; the open NEAR/USD
position (§32) survived the restart via event-sourced replay, unaffected.

**63 trials, zero adopted, zero closed trades.**

## §35 — a decay monitor, ported as a mechanism from the sibling bot, translated to repete1's own ledger

**No gate, no trial, no profit.** Infrastructure, not a strategy decision. Does
not touch the trial counter above.

xsmom (§32) carries a pre-registered review: 2026-11-01 or 20 closed trades,
whichever comes first. Today it has zero. The daily-loss kill switch (§7-era)
answers "is this losing money fast enough to trip a hard limit" — nothing in
repete1 answers the different question of whether a strategy's entry signal has
quietly stopped carrying information without ever losing fast enough to trip
anything. Asked what's next for repete1 and pointed at the sibling bot for
ideas, this gap is exactly what the sibling's own operator used, today, to
decide to stop actively developing that bot — waiting for its own version of
this mechanism to reach n=20 closed trades. That is a strong enough signal of
real usefulness to build the equivalent here before repete1's own first trade
closes, not after.

### The algorithm, translated

Null hypothesis: entering at random times, with holding periods resampled WITH
REPLACEMENT from the strategy's own realized closed-trade holding periods (so
exposure duration is comparable, not fixed), would have done as well. For each
of 2000 synthetic track records of N trades (N = the strategy's current closed-
trade count): draw a random historical bar from the full symbol universe the
strategy watches (weighted by each symbol's bar count), enter at the bar
AFTER it — never the bar itself, no look-ahead — at that bar's open, exit at
the close of `entry + holding` bars. Cost on both legs comes from
`fills.simulate_fill`, the identical function the live path and the
backtester use, so the null pays the same fees and impact a real trade would.
Record each synthetic record's mean return-per-trade; rank the strategy's real
mean return-per-trade as a percentile within that 2000-point distribution.

Verdict: fewer than 20 closed trades is always `INSUFFICIENT_DATA`, checked
BEFORE any simulation runs or the seed is touched — a verdict nobody should
trust does not get to spend the reproducibility budget on looking like one
that ran. Below the 5th percentile is `WORSE_THAN_RANDOM` (alerts). 5th-95th is
`INDISTINGUISHABLE_FROM_RANDOM`. 95th and above is `BEATS_RANDOM`. Seed is
fixed; a re-run reproduces the same verdict exactly.

### What it is structurally incapable of

`src/decay_stats.py` — the module that does the actual comparison — imports
nothing that can write to the ledger, touch risk state, or reach the network,
and calls no function that could halt trading. This is AST-walked by
`tests/test_decay_monitor_is_read_only.py`, not merely asserted in a
docstring — the same discipline `tests/test_viewmodel_is_pure.py` already
applies to `src/viewmodel.py`. The orchestration script
(`scripts/decay_monitor.py`) legitimately imports `ledger`/`venue`/`alerting`;
the AST guard is on the pure statistics module specifically, because that is
the one place a "just write the verdict back" shortcut would be tempting and
would defeat the entire point of a monitor whose only job is to read and
report.

### The known, deliberate limitation

Synthetic null trades carry no stop-loss or take-profit, so they absorb the
FULL loss a real managed trade would have cut short. This biases the null
distribution's returns DOWNWARD — the monitor is LENIENT, more likely to call
a decayed strategy "indistinguishable from random" than to false-alarm on a
healthy one. This is printed alongside every verdict
(`decay_stats.Verdict.note`) rather than left as something a reader has to
already know.

### A bug this section's own tests caught, before it shipped

The orchestration script's `main()` originally called `run(cfg, closed,
enabled)`, relying on `run`'s *default* `status_path` argument — the exact §34
class of bug, reproduced in this section's own first draft. A test that
monkeypatched the module's `STATUS_PATH` global to redirect the cache into a
tmp_path expected the write to land there; it did not, because the default was
bound once when `run` was defined, before the monkeypatch existed. Fixed the
same way §34 was: pass `status_path=STATUS_PATH` explicitly at the call site,
so it is read fresh on every call.

### First run against the real ledger

xsmom, the only enabled strategy: 0 closed trades (192 decisions, 0 outcomes)
→ `INSUFFICIENT_DATA (0/20 trades)`, exactly as expected, with **zero network
calls** — `check_strategy` never constructs a market-data client below the
trade threshold, so this ran safely offline against production state. The
cache (`state/decay_monitor_status.json`) was written with that one row, and
the dashboard's new "Decay check" card rendered it correctly on the next local
`dashboard.py` run.

### Where it lives

`src/decay_stats.py` (pure), `scripts/decay_monitor.py` (orchestration,
`--once`), a "Decay check" dashboard card (`_decay_cards`, `src/dashboard.py`)
reading the cache file rather than recomputing anything live, and a daily
`scripts/scheduler.py` job at 04:25 UTC — clear of `collect-funding` (4:00),
`collect-orderbook` (:05), `collect-news` (:20), `cycle-catchup` (:35), and
every `watchdog` slot. Daily, not more frequent: a decay verdict shifts over
dozens of trades, not minutes, and anything faster would only spend the
venue's shared rate-limit budget for no signal.

### Found and deliberately not pursued in the same round

The random-universe design decision (full configured universe vs. only
symbols actually traded) and the below-threshold dashboard visibility
question were both put to the owner rather than assumed, since either default
would have been defensible: full universe won because xsmom is cross-sectional
and watches all 21 markets regardless of which ones it has traded so far;
always-visible won because an operator not watching a 24/7 bot live benefits
from seeing "0/20 trades" progress rather than a panel that only appears once
a verdict already exists.

1,264 tests pass (+29). Bot untouched — this section adds a script and a
scheduled job, nothing on the live decision path.

**63 trials, zero adopted, zero closed trades.** This section does not change
that count; it is a monitor, not a candidate.

## §36 — the drawdown breaker was a one-way latch, and it had been distorting every backtest

**No gate, no trial, no profit — but this one moves numbers.** A confirmed bug
in a risk rail, fixed. It is not a candidate and adopts nothing. It does,
however, change what the simulator measures, which is a different and larger
claim than §34's, and the bulk of this entry is about that.

Flagged in §34 as "found and deliberately NOT built", deferred once more at the
start of this session because a correct fix has to touch `src/risk.py` and
`src/backtest.py` identically or it becomes divergence. Built now.

### The latch, reproduced before anything was changed

`update_high_water()` ratcheted the equity peak UP only — correct in isolation,
and the reason a drawdown rail fires at all. The failure is what happens after
it fires. Run against the real, unmodified rail:

```
equity peaks $100,000 -> falls to $89,000 (11% > the 10% cap) -> entries blocked
exits run (correctly — they are exempt) until the book is FLAT
equity is now pure cash and CANNOT move, because entries are the only way to
hold anything that could appreciate
-> 10,000 further cycles: still blocked. 1,500 daily cycles: still blocked.
```

There is no automated path back. Only a human deleting `state/.equity_highwater
.json`. The §31 comment stating the peak keeps tracking on sells "otherwise the
breaker could never clear itself" described an intent the arithmetic never had:
running the ratchet on a blocked entry can only hold the peak or push it UP.
That comment has been corrected in place, and the test carrying the same false
claim in its docstring now states what it actually proves.

### The fix, and why parity got STRONGER rather than merely preserved

One new pure function, `risk.ratchet_peak(peak, peak_ts, equity, now_ts,
half_life_days)`. The peak still ratchets UP instantly; it now loses authority
DOWNWARD slowly, halving its distance above current equity every half-life.

Before, live did `max()` in `update_high_water` and the sim did `max()` in two
places in `backtest.py` — three implementations that happened to agree. Now all
three call this one function. Only the STORAGE still differs (a file vs a
variable), which is irreducible. The parity test was upgraded from a string
grep for `sim_peak = max(...)` to an AST check that both sim loops call
`risk.ratchet_peak` — the old test pinned an implementation, so it fired on
this fix rather than on a divergence, which is the wrong thing for a guard to
be sensitive to.

Two fail-safe properties, both tested: an unparseable timestamp and a
naive-beside-aware timestamp pair both decay NOTHING. A broken clock must never
be a route to clearing the breaker.

### What the measurement actually showed — the part that matters

The expectation was "this might move a gate number." It moved all of them,
because **the latch had been crippling the simulator too, silently, on every
gate ever run here.** Same frozen snapshot (`078438ba28ca`), same OOS window,
only the half-life changed. `dd-blocks` counts entries the drawdown rail
refused:

| strategy | latched: maxDD / trades / dd-blocks / ret | fixed (365d): maxDD / trades / dd-blocks / ret |
|---|---|---|
| donchian | 12.56% / 9 / 136 / −1.73% | 25.20% / 36 / 9 / **+65.93%** |
| ma_crossover | 12.00% / 17 / 223 / −12.00% | 22.20% / 33 / 195 / −22.20% |
| meanrev | 11.34% / 52 / 14 / −9.90% | 13.05% / 57 / 0 / −11.90% |
| tsmom | 13.12% / 19 / **1,692** / −1.87% | 18.71% / 66 / 976 / −6.04% |
| xsmom | 15.09% / 25 / 103 / +1.63% | 15.97% / 27 / 100 / +1.95% |
| xsrev | 12.55% / 49 / 272 / −0.37% | 20.09% / 74 / 210 / −8.96% |

`tsmom` recorded 19 trades against **1,692 drawdown-blocked entries** — that
backtest was very nearly a measurement of a frozen bot. This is the same
signature as the sibling bot's own incident (99.43% of signals blocked by the
identical latch), and it was here the whole time, in the instrument every
verdict in this file was produced by.

Note also that the flattering direction is NOT uniform: unlatching made
`ma_crossover`, `meanrev`, `tsmom` and `xsrev` look WORSE, several materially.
A change that only ever improved results would be the thing to distrust.

### donchian, and refusing to draw the obvious conclusion

`donchian` goes from −1.73% (9 trades) to +65.93% (36 trades). It has been
recorded FAIL in this file at least four separate times (lines 349, 474, 644,
909) — **every one of those measurements was taken on the latched instrument,
after the rail had already frozen it.** Those specific numbers are therefore
void as evidence, in both directions.

That is the entire claim being made. It is NOT a claim that donchian has an
edge, and this number must never later be cited as if it were:

* it is a re-measurement on the OOS window this programme has already examined
  many times over 63 trials, not a fresh holdout;
* it has not been through the mandatory 1.5x cost-stress arm, a negative
  control, or `significance.compare` with the cumulative Bonferroni K;
* it carries a 25.20% realized drawdown against a stated 10% tolerance;
* it is exactly the shape of number a later session would rediscover,
  rationalise and adopt, which is why it is written down here as inadmissible
  rather than left to be found.

A real answer needs a pre-registered re-gate, and that would be a NEW trial
incrementing K. Not done in this section, deliberately.

### xsmom: the verdict stands, the cited figures do not

§32 enabled xsmom while stating plainly it failed, citing "1.5x-fee-stress PF
0.927 < 1.0". Re-run through the real `bt.gate_both_arms` both ways:

```
LATCHED: base +1.63% PF 1.087 | 1.5x -1.60% PF 0.927 -> FAIL
FIXED  : base +1.95% PF 1.094 | 1.5x +1.24% PF 1.059 -> FAIL
```

Still **FAIL**, so §32's decision and its honest "known non-edge" label stand
and nothing needs reverting. But the specific reason §32 recorded is now stale:
the stress arm is no longer negative, and no longer below PF 1.0. It fails on
different clauses (PF < 1.3; cost multiple 1.79 < 2.0). Recorded here rather
than edited into §32 — that section is an append-only record of what was known
when the decision was made.

### The half-life is an owner decision, and was taken as one

A sweep over 0/30/90/180/365 days was run and put to the owner with the
numbers, because this is a risk-tolerance call and not a technical one: a short
half-life unlatches fast but permits realized drawdowns of 29–34%, and a long
one keeps the brake biting through a real decline. **365 days, chosen by the
owner**, on the argument that the brake should stay fully active through any
realistic drawdown episode and release only once the bot has been stuck for an
implausibly long time.

Stated explicitly because it is the trap this repo has the most machinery
against: 365d also produced the lowest realized drawdown in 4 of 6 strategies
and the best donchian return, and **neither fact is the reason it was chosen.**
The sweep ran on an already-mined OOS window; picking the value that paid best
would be precisely the mining the Bonferroni discipline exists to stop.

Measured behaviour of the shipped setting: an 11% drawdown on a flat book
clears on **day 57**, versus never. A test pins that as a WINDOW (14–365 days),
not a floor — clearing too fast makes the brake decorative, and that is a real
failure direction too.

### What is NOT resolved

Every gate verdict recorded in this file before today was measured on the
latched instrument. Most were FAILs and unlatching made several look worse, so
there is no reason to think the programme's central conclusion — no edge found
— is wrong. But "which past sections deserve a re-gate, and at what cost to K"
is a real question this section deliberately does not answer alone.

### One more thing, and it is a correction to my own diagnosis

While checking whether the live bot was safe to restart, `pgrep -fl
"scheduler.py"` showed TWO schedulers, one of them orphaned (PPID 1) and older
than the supervised one. Read as a duplicate-scheduler bug — every job firing
twice — which is a failure this repo has genuinely had before (see §26 in
`scripts/run_repete1.sh`).

It was wrong. The second scheduler's cwd is `bots/repete2`: a different bot.
Every bot on this host has a `scripts/scheduler.py`, so no command-line pattern
distinguishes them — which is stated, at length, in the header of
`scripts/stop_repete1.sh`, describing the 2026-07-29 incident where exactly this
misread led to killing the FX bot's scheduler repeatedly. Acting on the first
reading would have reproduced that incident precisely.

The guard did not fail; the diagnosis did. `stop_repete1.sh --dry-run` selected
5 processes, all `bots/repete1`, repete2 untouched — the cwd discriminator works
as designed. Recorded because the near-miss is the useful part: the trap was
already written down, in the file I was about to run, and I still walked into
it. Reading `pgrep` output as identifying a process is the habit to distrust.

1,275 tests pass (+11). Bot stopped and restarted on the new code (`risk.py` is
on the live decision path, so a running process would have kept the old rail in
memory): preflight ok, 21 markets, xsmom enabled, 5 processes, dashboard HTTP
200, scheduler up with 18 jobs including §35's `decay-monitor`. The open
NEAR/USD position survived. Live equity is above the recorded peak, so the
drawdown is 0% and the changed rail is not currently binding on anything.

**63 trials, zero adopted, zero closed trades.** Unchanged: fixing the
measuring instrument is not a trial, and nothing here was adopted.

## §37 — PRE-REGISTRATION: re-gate donchian on the repaired instrument

**This entry contains no gate script and no results.** It is committed before
`scripts/regate_donchian.py` exists, which is the only thing that makes the
prediction below worth anything. CLAIM TYPE: EDGE. **+1 trial → K = 64.**

### Why donchian and nothing else

§36 established that every gate verdict in this file was measured on a
simulator whose drawdown rail latched. §36 deliberately left "which sections
deserve a re-gate" open. The answer is donchian alone, and the reasoning is
that a re-gate is only warranted where the latch plausibly changed the ANSWER
rather than merely the numbers:

* `donchian` — recorded FAIL four times (lines 349, 474, 644, 909), and on the
  repaired instrument it was blocked 136 times after just 9 trades. Its FAILs
  are the ones most likely to be artefacts. **Re-gate.**
* `ma_crossover`, `meanrev`, `tsmom`, `xsrev` — all recorded FAIL, and
  unlatching made every one of them look WORSE, not better. A re-gate would be
  spending trials to re-confirm a rejection. **No re-gate.**
* `xsmom` — already re-run through `bt.gate_both_arms` in §36: still FAIL, so
  §32's label stands. **No further trial.**

### The one arm, and why there is no grid

**One arm: donchian at its SHIPPED parameters** (`entry_channel_bars: 20`,
`exit_channel_bars: 10`, `trend_sma_period: 200`), at 1.0x and 1.5x cost. The
two cost levels are the two halves of one trial, not two trials.

**No parameter search, deliberately.** A grid here would be searching an OOS
window this programme has examined across 63 prior trials for a strategy I have
already seen one flattering number from. That is the definition of mining. If
the shipped configuration cannot clear the gate, the honest conclusion is that
donchian does not clear the gate.

### The disclosure that weakens this

**I have already seen a number from this window: +65.93% / 36 trades**, surfaced
while repairing the instrument in §36. That was unavoidable — it is how the bug
was found — but it means this is NOT a clean pre-registration, and a PASS here
must be treated as weaker evidence than a PASS arrived at blind. Written down
because the alternative is a future reader assuming it was clean.

What that number has NOT been through, and what this section applies: the 1.5x
cost-stress arm, profit factor ≥ 1.3, cost multiple ≥ 2.0, the buy-and-hold
comparison, a negative control, and Bonferroni-corrected significance at K=64.

### Negative control

§35's random-entry null, reused: `decay_stats.null_distribution` builds
synthetic track records with holding periods resampled from donchian's own
realized trades, entering at the bar AFTER a random bar. If donchian's mean
return per trade does not sit clearly above that null, the "breakout timing
carries information" premise collapses regardless of what the headline return
says. Controls never increment K and can never be adopted.

### Stated prediction, before the script exists

**I predict donchian FAILS.** Most likely failing clauses, in order: (1) the
buy-and-hold comparison — crypto's OOS window is a bull regime and +65.93% may
simply be less than holding; (2) the 1.5x cost multiple ≥ 2.0 clause, which is
what killed xsmom; (3) profit factor ≥ 1.3.

The prediction that would most surprise me is a clean PASS on both arms. If
that happens, the correct response is still NOT to enable it — it would be one
re-measurement on a mined window, and the next step would be forward paper
evidence, not adoption.

**63 trials, zero adopted, zero closed trades.** K becomes 64 when the gate
below actually runs.

## §37 RESULT — donchian REJECTED, and the gate had a hole

**K = 64. Not adopted. donchian stays `enabled: false`.**

### The prediction was wrong, and wrong in an instructive way

§37 predicted FAIL, most likely on the buy-and-hold clause. Both halves of that
were wrong. donchian **PASSED every deterministic clause**, at both cost levels:

| arm | ret | PF | maxDD | n | cost mult | deploy% |
|---|---|---|---|---|---|---|
| latched (pre-§36) | −1.73% | 0.725 | 12.56% | 9 | −3.74 | 1.95 |
| repaired 1.0x | **+65.93%** | 3.379 | 25.20% | 36 | 34.26 | 9.81 |
| repaired 1.5x | **+64.60%** | 3.290 | 25.15% | 35 | 23.57 | 9.80 |

The B&H clause was not close: buy-and-hold returned **−4.64%** over this window
(maxDD 67.93%). The OOS period is a crypto BEAR regime, not the bull run the
prediction assumed. So the clause I expected to kill it was the easiest one to
clear — a reminder that a prediction about *which* clause fails is a guess about
the market, not about the strategy.

The §35 random-entry control also passed, at the **99.5th percentile**.

### And it is still a REJECT, because of one trade

| check | result |
|---|---|
| win rate | 36.1% (13/36) |
| mean return / trade | **+24.14%** |
| **median** return / trade | **−8.11%** |
| best single trade | ZEC/USD, +939.3%, $78,141 |
| that trade as a share of net P&L | **118.5%** |
| drop the best 1 trade | **−$12,213**, PF 0.56 |
| drop the best 3 / 5 | −$18,430 / −$21,458 |
| symbols profitable | 6 of 15 |
| significance at Bonferroni K=64 | **NOT significant** — 99.92% CI [−$836, +$9,510] includes zero |

The decisive test: **remove ZEC/USD from the universe and re-run the identical
gate.** +65.93% PASS becomes **−10.62% FAIL** at PF 0.542. One symbol out of 21.

The ZEC data is real and was checked rather than assumed — monthly closes 35.87
→ 40.56 → 120.80 → 411.83, a genuine 20x run, not a corrupted bar. donchian
caught one enormous real move. That is a lottery ticket, not an edge, and 35 of
its 36 trades collectively lose money.

### The hole this exposed, and the guard that closes it

`enablement_gate` checks return, profit factor, trade count, buy-and-hold and
cost multiple. **None of them notices that one trade is the entire result.**
donchian cleared all of them.

Worse, the §35 random-entry control did not catch it either: it compares MEAN
return per trade, and the same +939% outlier that fooled the gate fooled the
mean. The median trade lost 8.11%. **A control built on a mean inherits the
mean's blindness to concentration** — worth knowing about the instrument built
two sections ago, and found only by using it in anger.

Shipped: `backtest.concentration_clause()` — no single trade may exceed 50% of
the net result. Deliberately a separate function rather than a key on
`Result.summary()`, because that dict is compared byte-for-byte against
`tests/golden/backtest_baseline.json` and its own docstring warns that a new
key is indistinguishable at a glance from a moved number.

The 50% bar was chosen AFTER seeing donchian at 118.5%, and that is stated in
the code rather than hidden: any threshold below 1.185 would have caught this
case, so pretending the number was independent would be the tuning this repo
exists to refuse.

`tests/test_concentration_clause.py` walks the AST of every script in
`scripts/` and fails any that calls `gate_both_arms`/`enablement_gate` without
also calling `concentration_clause`. It immediately caught **10 pre-§37 gate
scripts**. They are grandfathered in an explicit frozen set — every verdict they
recorded was a FAIL, and this clause can only turn a PASS into a FAIL, so
retrofitting them changes no conclusion in this file. A second test asserts the
list **only ever shrinks**, and fails if an entry goes stale: an allowlist that
can grow is not a guard, it is a habit.

### What is now true about the other sections

§36 left open which sections deserved a re-gate. Answered: **donchian was the
only candidate, it has been re-gated, and it is rejected.** The other four
FAILs (`ma_crossover`, `meanrev`, `tsmom`, `xsrev`) all looked WORSE on the
repaired instrument, and `xsmom` was already re-run in §36 and still fails. No
further re-gates are warranted, and the programme's central finding is
unchanged.

1,283 tests pass (+8). Bot untouched: this section adds a gate script, a gate
clause and tests. Nothing on the live decision path changed, and no strategy
was enabled.

**64 trials, zero adopted, zero closed trades.**

## §38 — on-chain valuation bands: researched, replicated, and PARKED without spending a trial

**MEASUREMENT + SOURCE REVIEW (2026-08-12). K stays 64. Nothing enabled,
nothing registered, and the one candidate this research produced is parked
with its blocker named rather than gated into a predetermined verdict.**

The owner asked for deep research on profitable crypto strategies with
backtested proof, applied to this bot. The research pass surveyed the
literature under one constraint the record already imposes: §4–§37 closed
every momentum, trend, reversal, filter and execution family the published
factor zoo actually locates in daily spot bars, and the replication
literature's own estimate is that 27–53% of published anomalies are false
discoveries. The one mechanism 64 trials never touched, that is free to
replicate and survivorship-immune by construction, is BTC-level on-chain
valuation: Grobys, Näsman & Sandretto, "Using on-chain data to predict
Bitcoin cycles," RIBAF 89 (2026) 103486 — NUPL and MVRV-Z band timing,
long-or-flat, which happens to be exactly the shape this venue permits.

Full reading, not the abstract: knowledge/source-review-onchain-mvrv.md.
The deciding fact is in the paper's own Table A1 — **each strategy makes
THREE trades in 11.5 years**, and inside our snapshot window that is ~2, one
of them still open. `enablement_gate` requires ≥15 OOS trades. An EDGE
registration would therefore have been a FAIL determined before the run — K
spent on theater. The §11 lesson (inert arms reading as confirmations)
generalizes: a trial whose verdict cannot vary is not a trial. Parked
instead, with the §12-style condition recorded in
knowledge/backtest_candidates.md: an owner-licensed, SEPARATELY
pre-registered cycle-level methodology, or decades of data.

### What was built so the idea stays testable

- `scripts/build_onchain_snapshot.py` + `data/onchain_20260812.json.gz` —
  5,869 days of BTC CapMrktCurUSD + CapMVRVCur (CoinMetrics community, free,
  no key), 2010-07-18..2026-08-11, zero calendar gaps, sha256 in
  ONCHAIN_MANIFEST.json, `--verify` wired. RV and NUPL are algebraic
  identities on the stored pair (RV = MV/MVRV, NUPL = 1 − 1/MVRV); MVRV-Z's
  σ(MV) convention is deliberately NOT baked into the artifact — it belongs
  to whatever analysis pre-registers it. The manifest carries a
  `conservative_lag_rule`: a decision at bar D's close may read on-chain
  values dated ≤ D−1, because CoinMetrics publishes day D hours after this
  bot's 00:01:30 UTC decision moment.
- The era-aware sanity check exists because the first build REFUSED the real
  2010 data: MVRV 146 at genesis is genuine (almost no coins had ever
  moved), and a flat modern-era bound called it garbage. Found by execution.
- `data/funding_live.jsonl`'s silent stall (2026-08-04, another casualty of
  the 175-hour scheduler outage fixed this morning) was healed by
  backfilling Aug 5–11 from Binance history via the collector's own logic —
  funding is backfillable, order books are not. H(§12)'s forward dataset is
  intact: 21/21 symbols, no gaps since 2026-07-23.

### The measurement, disclosed §37-style

`scripts/measure_onchain_regime.py` replayed the paper's six variants
verbatim (no other thresholds computed) on the frozen snapshots: expanding-σ
Z from 2010, D−1 lag, fills at next open, 26 bps per side. Every entry and
exit matches Table A1 within the documented 2-day lag+fill offset, so the
replication is faithful and the finding transfers across data sources
(bitcoinmagazinepro → CoinMetrics community).

BTC/USD 2019-01-01..2026-07-29, costed buy-and-hold **+1,631.78%**:

| variant | trades | open? | return | vs B&H | null pctl* |
|---|---|---|---|---|---|
| NUPL 1 (exit .67) | 2 | yes | +1,873.10% | +241.3pp | 86.3% |
| NUPL 2 (exit .70) | 2 | yes | +2,386.21% | +754.4pp | 93.8% |
| NUPL 3 (exit .73) | 2 | yes | +2,954.30% | +1,322.5pp | 97.0% |
| MVRV-Z 1 (exit 5) | 2 | yes | +2,575.87% | +944.1pp | 95.1% |
| MVRV-Z 2 (exit 6) | 2 | yes | +3,187.29% | +1,555.5pp | 99.0% |
| MVRV-Z 3 (exit 7) | 2 | yes | +4,423.14% | +2,791.4pp | 99.5% |

*2,000 random-entry paths holding the SAME block lengths (the §17
time-in-market matching), seeded, in state/onchain_measurement_38.json.

### Why this is not evidence of an adoptable edge, in this repo's own terms

1. **n = 2, one open.** The entire result is one completed cycle call (exit
   within weeks of the 2021 top) plus one entry (June 2022) marked at the
   last bar. Under §37's concentration lens this is 100% of P&L in one-two
   trades BY DESIGN — cycle timing IS concentration.
2. The first "entry" is forced: the window opens with BTC already in the buy
   zone. The paper's Trade 2 gets the same treatment, but it means our
   window contributes roughly 1.5 independent decisions, not 2.
3. Exit thresholds are partly post-hoc and the authors say so; the 2022–25
   cycle already broke them (no variant exited; all six collapse into the
   same open trade — visible in the table's identical second trades).
4. Sharpe t-stats of 15–31 in the paper come from treating 4,143
   autocorrelated daily returns as the sample while the decision count is 3.
   This repo's evidence standard counts decisions.

**DISCLOSURE, binding on every future section: these numbers have been
seen.** Any later pre-registration touching on-chain bands must cite §38 and
state that the outcome was known first, the same way §37 disclosed
donchian's +65.93%.

1,313 tests pass (+30: 15 snapshot offline, 10 measurement offline, and the
§38-adjacent isolation/backup fixes). Two of the new tests are structural:
nothing in src/ may reference on-chain data, and the measurement script may
never call `gate_both_arms`/`enablement_gate` — if it ever does, it has
become a trial and owes a pre-registration.

**64 trials, zero adopted, zero closed trades.**

### §38 addendum — the current cycle, isolated

The aggregate table above pools every trade a variant ever made. That is the
wrong number to look at if the question is "how is this doing right now" —
a live decision only ever sees ONE trade, and pooling a closed 2019 cycle
with the currently open one hides exactly the thing that matters: whether
the OPEN position is itself real evidence or a lucky ride.

`trade_breakdown()` splits every variant into its individual trades and
tags the still-open one `current_cycle`. Re-run 2026-08-12, same frozen
snapshot, no new numbers touched anything already disclosed:

| variant | entry (closed) | closed return | ann. log | **current cycle entry** | **days held** | **unrealized** | **ann. log** |
|---|---|---|---|---|---|---|---|
| NUPL 1 | 2019-01-02→2020-12-28 | +582.65% | +96.6%/yr | 2022-06-15 | 1,505 | +189.03% | +25.8%/yr |
| NUPL 2 | 2019-01-02→2021-01-04 | +760.18% | +107.2%/yr | 2022-06-15 | 1,505 | +189.03% | +25.8%/yr |
| NUPL 3 | 2019-01-02→2021-01-09 | +956.73% | +116.7%/yr | 2022-06-15 | 1,505 | +189.03% | +25.8%/yr |
| MVRV-Z 1 | 2019-01-02→2021-01-04 | +760.18% | +107.2%/yr | 2022-06-20 | 1,500 | +211.08% | +27.6%/yr |
| MVRV-Z 2 | 2019-01-02→2021-01-09 | +956.73% | +116.7%/yr | 2022-06-20 | 1,500 | +211.08% | +27.6%/yr |
| MVRV-Z 3 | 2019-01-02→2021-02-21 | +1,354.00% | +125.2%/yr | 2022-06-20 | 1,500 | +211.08% | +27.6%/yr |

The current cycle is one position, entered June 2022, never having reached
ANY variant's exit band across 4+ years and 1,500 days held — exactly the
2022–25 cycle-break already noted in §38 proper. Its unrealized annualized
return (~26–28%/yr) is roughly a quarter of the closed 2019–21 cycle's
(~97–125%/yr): the SAME rule, same asset, produced a materially weaker
result on the very next cycle, which is the single-cycle-fragility concern
stated in §38 made concrete rather than abstract. It is one more entry
against blocker 4 (effective n = 3 cycles, one already broken), not new
evidence for the candidate — the DISCLOSURE rule from §38 proper applies
here too.

14 offline tests added for `trade_breakdown()` (1,317 total). No K spent,
nothing enabled, live path untouched.

### §38 addendum — the current-cycle numbers, on the dashboard

Display-only, following on directly from the trade-breakdown addendum
above: the six current-cycle unrealized returns are now cards on the live
dashboard (§35's own "dashboard card" precedent), one per variant, reading
`state/onchain_measurement_38.json` — the exact frozen cache the addendum
wrote, never recomputed on render.

Not scheduled to refresh. `measure_onchain_regime.py` reads two hand-built
snapshots that are not in scheduler.py's JOBS; a scheduled rerun would
recompute byte-identical numbers every time and misleadingly imply a live
feed. The card group's own title discloses this: "On-chain bands (§38 —
frozen snapshot, not live, as of 2026-07-29)".

The only guard this touched was `test_nothing_on_the_live_path_imports_
onchain_data`, which banned the substring "onchain" across all of `src/` —
broader than its own docstring's stated intent (the decision-path files by
name). Narrowed to exactly those files; a companion test now pins that
dashboard.py's reference is intentional, so a future re-broadening fails
loudly on the dashboard's own legitimate use instead of silently reverting
the feature. Sanity-checked by execution: a scratch "onchain" string added
to src/risk.py still fails the narrowed test immediately.

11 new tests (dashboard cards: missing/malformed file, 6-card ordering and
values, sign-based tone, one row missing its current-cycle trade empties
the whole panel rather than 5-of-6; isolation guard: narrowing + pin).
1,328 total. Live path untouched, K unchanged.

## §39 — E1: the pager was broken for 3.5 hours and nothing said so

**INFRA (2026-08-13). K stays 64. First phase of the enterprise programme
(audit 2026-08-12: ~5/10; ops scored 5 with this exact class of failure as
the evidence).**

The 2026-08-12 webhook outage: 17 consecutive `HTTPError` warnings from
16:30 to 19:50 local, one per watchdog tick, every page in that window
dropped after a single attempt. Undiagnosable afterwards — the old log line
recorded only the exception TYPE, and 429 (rate limit), 500 (their outage)
and 404 (dead topic) all read identically while each has a different fix.
Root cause therefore unknown and unknowable; the endpoint was healthy again
by 01:05 UTC when probed (200, message delivered).

The deeper defect: the channel that reports problems was the thing failing,
and no other surface knew. A broken pager is the one alarm that cannot page.

### Shipped

- `send()` retries transient failures (429/5xx/connection errors) on a
  short bounded schedule (0/1/4s), breaks immediately on other 4xx, and
  logs the HTTP STATUS CODE — never the URL, which is a credential.
- Every webhook outcome lands in `state/pager_health.json`;
  `health.status()` raises a problem at ≥3 consecutive failures, so the
  dashboard — the channel that keeps working — says "pager is broken."
- **The sibling bot's PR-#76 lesson, finally ported**: `delivery_allowed()`
  refuses real delivery under pytest unless a test explicitly declares
  `REPETE_ALERTS_TEST_DELIVERY=1` (transport-mocked tests do), and
  `REPETE_ALERTS_OFF=1` is the operator drill switch. repete1's suite could
  previously pop real banners — or with env leakage, page a real phone.
- Watchdog `backup_problems()`: newest local archive older than 48h is a
  CRITICAL. The 2026-08-06→12 six-day backup gap (the scheduler was dead
  and the backup died silently with it) can never recur unannounced.

### Verified by execution

- Real alert through the new path: delivered, `channel: webhook`,
  `pager_health` recording the success (consecutive_failures 0).
- First completed decision cycle since Aug 5: `heartbeat_cycle`
  2026-08-13T00:03:00Z; the cycle-heartbeat CRITICAL cleared on the next
  watchdog tick. The 175-hour outage is closed end-to-end.
- Fresh backup: the restored scheduler's own 01:00 UTC slot fired on
  schedule (first time since Aug 6), mirror sha256-verified, restore drill
  PASS. `watchdog.check()` against real state shows only the known
  order-book coverage problem (§28's laptop constraint, E2's target).

16 tests added (11 alerting: guard/retry/status/self-health; 5 watchdog:
backup age). Live path untouched, no strategy enabled.

## §40 — E2: everything the Bizon cutover needs except the owner's hands

**INFRA (2026-08-13). K stays 64.** §28 proved §22's 90%-coverage trigger is
structurally unreachable on a sleeping laptop (44% measured; a forward rate
below the target never converges to it). The always-on host was chosen by
the owner: the Bizon workstation at the partner's site, reachable over the
AnyDesk tunnel per the infrastructure notes.

Shipped so the owner's manual steps are the ONLY remaining gate:
- `deploy/repete1-bare.service` — user-level systemd unit exec'ing
  `scripts/run_repete1.sh` directly: the SAME launch path the laptop uses,
  supervisor loop and §26 guard included, rather than the docker unit whose
  container was deliberately never made real.
- `deploy/BIZON.md` — the run-once checklist: access, venv, secrets typed
  on the box (never through chat), systemd, four verification commands, and
  THE HANDOFF: laptop launchd unloaded, laptop checkout becomes dev-only,
  Bizon starts with fresh state/ (copying an append-only stream between
  hosts is how a track record forks; the 20-trade decay clock restarting is
  the honest cost, to be recorded here at cutover).
- Host-handoff guard: the scheduler stamps `state/.host_marker` at startup;
  a boot against state last written by a DIFFERENT host logs, pages, and
  names both hosts. A warning, not a refusal — restoring onto replacement
  hardware is legitimate. `preflight.run()` deliberately does NOT grow this
  as a failure, and a test pins that.

Verified by execution: the real entrypoint (`scripts/scheduler.py`, same
cwd, same interpreter) writes the marker; the live restart also surfaced a
diagnosis near-miss worth recording — a second scheduler PID looked like a
§26 violation and was repete2's (cwd check, the §36 lesson, saved it again).

10 tests added (6 written for the marker; 4 generated by
test_docs_reference_real_code.py because BIZON.md's cited paths are
now checked for existence — the doc-citation guard picking up a new
doc automatically is that guard working). 1,354 total. Live decision
path untouched.

## §41 — E3: security scanning that sees history, not just today

**INFRA (2026-08-13). K stays 64.** The audit scored security 6/9: no
secrets scanner, no Dependabot, pip-audit failing invisibly behind
`continue-on-error`.

Shipped: gitleaks as its own CI job with `fetch-depth: 0` — proven to
matter by execution on a scratch repo (committed-then-deleted key: MISSED
at depth 1, CAUGHT at full depth), and the sibling repo's documented trap
avoided on the second attempt only because it was written down: the AWS
documentation key `AKIA...EXAMPLE` is allowlisted by gitleaks and proves
nothing; the working canary used a non-example shape. Baseline scan of the
REAL history: 91 commits, zero findings — the repo's hygiene claim is now
measured, not asserted. Dependabot (pip + actions, weekly, grouped).
pip-audit failures now emit a run-summary warning annotation instead of a
line in a log nobody opens. Branch protection documented as structurally
unavailable (403 on this plan) rather than pretended-chosen, in
docs/operational_controls.md with what substitutes for it.

No new Python tests (CI-config change); the doc-citation guards picked up
the new operational_controls section and pass. Live path untouched.

## §42 — E4: bounded logs, a timeout somebody actually chose

**INFRA (2026-08-13). K stays 64.** Two audit deductions closed.

**Log rotation** — `scripts/rotate_logs.sh`, daily at 02:55 UTC (the one
unclaimed minute), copytruncate and NOT rename: main.py and watchdog.py
both hold descriptors on `logs/agent.log`, and a rename orphans whichever
process didn't do it — its every subsequent line lands in a file nobody
reads. The sibling bot measured this with four writers; here it's two, and
the test that matters proves the property directly: a descriptor opened
BEFORE rotation still writes into the visible file AFTER, same inode.
Size-gated at 5MB with archives pruned to 12 per log — an unbounded
archive directory is the same disease one folder over.

**Explicit venue timeout** — `venue.timeout_ms: 20000` wired through
`CcxtData._build`. Until now the client ran on whatever ccxt's per-exchange
default happens to be, unread and unreviewed; the sibling bot measured 246s
of one 15-minute window burned on three dead sockets under exactly that
arrangement. 20s is generous for Kraken's slowest documented endpoints and
small against the 60s risk tick.

Verified by execution: rotation no-ops on the real logs (all under
threshold — correct, the alarm-not-nag design), rotates a 100KB-threshold
copy correctly (3 files archived, gzip content byte-complete, inode
preserved); the constructed kraken client carries timeout=20000.

8 tests added (6 rotation, executed not read, per §27; 2 timeout).
Live decision path: the timeout is the first E-programme change that
touches code the live loop runs — it can only make a hung request fail
faster, and the §11-era retry/backoff above it is unchanged.

### Correction — the §38-addendum test arithmetic (found by the E-audit)

The trade-breakdown addendum above says "14 offline tests added ...
(1,317 total)". The 14 is right; the 1,317 is not the sum of anything: the
prior entry's 1,313 plus 14 is 1,327, and the SUITE at that commit
(`ca21dbb`) collected 1,328 — the addendum under-stated its own base by
one section's worth of drift and then the NEXT entry computed forward from
the wrong number and landed, coincidentally, on the correct 1,328. The
final totals were verified against live pytest runs and stand; the
intermediate label was wrong. Appended rather than edited, per this log's
own rule: editing history to make an audit finding disappear would be the
§24 sin. (E5, 2026-08-13.)

## §43 — E5: the docs stop lying, and the repo gets a front door

**INFRA (2026-08-13). K stays 64.** The audit scored docs 3/10, and the
worst finding was not a missing document but a lying one: the dashboard's
Evidence panel — regenerated every 15 minutes onto the public page —
carried a hardcoded §5-era paragraph ("48 registered trials... meanrev
clears every clause") and a parser that surfaced whichever verdict row sat
LAST IN THE FILE, which for meanrev was the §5 PASS that §7 explicitly
REVERTED. The page contradicted config.yaml, CLAUDE.md, and the log it
claimed to summarize, and no test referenced any of it.

Shipped:
- **knowledge/gate_verdicts.json** — the canonical per-strategy summary
  (latest section, verdict, numbers, enabled flag), maintained in the same
  commit as any new verdict. The dashboard renders THIS.
  tests/test_gate_verdicts.py pins it against config.yaml's enabled flags,
  the log's own final tally line, the cited sections' existence, and the
  renderer's source — including a deliberate tripwire: the day a strategy
  legitimately passes, test_no_verdict_says_pass must be updated in the
  same commit, so a PASS can never appear by accident.
- **README.md** — the missing front door: what the bot is, the record
  stated plainly (64 trials, zero adopted, and why that record is the
  product), a mermaid cycle diagram colored fail-open vs fail-closed (the
  repo's first correct diagram — the only prior one showed the deleted
  Alpaca broker), status, and a file map. Its record numbers are guarded
  by test.
- **GLOSSARY.md** — 25 terms, including the "coverage" collision (data
  collection vs test coverage) that misleads a new reader.
- **GUIDE.md / HEARTBEAT.md** — archive/stale banners naming exactly what
  is wrong in each (Alpaca+X walkthrough; weekday cadence on a 24/7 bot)
  instead of silently onboarding readers into a bot that no longer exists.
- The §38-addendum arithmetic error found by the audit (a "1,317 total"
  that summed from nothing) is corrected by APPENDED note above, per this
  log's own append-only rule.

Verified by execution: the real rendered page now reads "64 registered
trials; 0 adopted", shows 4× FAIL (§20) / REJECT (§18) / REJECT (§37), and
contains zero occurrences of the stale paragraph.

17 tests added (9 verdict guards incl. README; 8 auto-generated
doc-citation checks on the new docs' paths). 1,379 total.

## §44 — E6: coverage measured for the first time — 65%, floor at 60

**INFRA (2026-08-13). K stays 64.** The audit's tests dimension lost its
points to one fact: 1,328 tests and ZERO coverage measurement anywhere —
the word "coverage" appears throughout this repo meaning order-book
collection, and nothing ever quantified what fraction of the code the
suite exercises.

Measured: **65% of 10,029 statements** across src/ + scripts/. CI now
enforces a 60% floor — deliberately just UNDER measured truth so it can
only ratchet upward, never an invented target. The line-level truth also
sharpened the earlier audit's import-level finding ("no untested
modules"): imports reach every module, lines don't — `src/review.py`, the
operator's own report tool, measured **34%**.

Closed the worst of it: tests/test_review_report.py drives the report
against fixture ledgers and asserts the PRINTED NUMBERS match the
fixture's arithmetic (win rate, PF incl. the no-losses inf case, realized
P&L, exit-reason counts, per-strategy split, stale-alert windowing, and
main() end-to-end offline). The report is what a human reads to decide
whether to trust the bot; a wrong number there is an operator decision
made on bad data.

pytest-cov added to requirements-dev; the venv's moved-path pip shebang
(`.venv/bin/pip` pointing at a Desktop path that no longer exists) noted
here as a footnote — `python -m pip` works and is what everything scripted
uses.

6 tests added, 1,385 total. Live path untouched.

## §45 — E7: the learning loop proven before its first real trade, and trades that remember their pain

**INFRA (2026-08-13). K stays 64.** The owner asked for "a learning loop of
what you've learned in each trade." The honest finding: it already existed
— lessons.jsonl → generated learnings.md → weekly learn job → judge
calibration — and had never once run end-to-end, because zero trades have
ever closed. Its first execution would have been in production, unwatched:
the §27 shell-scripts lesson one layer up.

Shipped:
- **The chain, proven offline**: closed trade → evaluator (stubbed LLM)
  cites a lesson → evidence lands in the store → learnings.md regenerated
  with its GENERATED marker → the dashboard's lesson book renders it. One
  test, whole chain (test_learning_loop_e2e.py).
- **MAE/MFE** — the audit found zero references anywhere. postexit.mae_mfe
  is pure and fail-open (absent stays absent, the fees lesson applied
  forward: a trade whose bars couldn't be fetched must not read as "never
  moved against us"). Recorded at close on the live path
  (ledger.close_trade, journal entry) AND on both simulators' trades — the
  SAME function, which is what parity means. Golden verified byte-identical
  (summary() never carried per-trade fields; §37's own comment is why).
- **Exit attribution** was already real (exit_reason vocabulary on every
  outcome; review.py counts it) — verified rather than rebuilt.
- Dashboard MAE/MFE columns deferred until a closed trade exists to render
  — the data now flows; an empty column is decoration.

Why this matters for the decay-monitor era: when xsmom's 20-trade sample
arrives, every trade will carry its excursion history and exit cause — the
difference between "it lost 2%" and "it was up 9%, gave it all back, and
the exit rule watched" is the difference between a P&L and a lesson.

7 tests added, 1,392 total. Live decision path: close-path additions are
additive record fields; entries untouched.

## §46 — E8: the 324-line closure becomes a function with a name for its inputs

**INFRA (2026-08-13). K stays 64.** The audit's worst structural finding:
`_run_cycle` at 806 lines with `_process_signal` — 324 lines — nested
inside it, reading 13 outer variables by closure capture. Every one of
those captures was invisible at the call site.

The extraction, done the §36-instrument way — measured, not guessed:
- AST analysis first: 13 free variables (the audit's list plus `venue`,
  which it missed), ZERO nonlocal rebinds, and every assignment textually
  precedes both call sites — so a single `_CycleEnv` built after the last
  assignment sees exactly what the closure saw.
- Token-position rewriting (not text replacement), excluding kwarg names
  and attribute accesses — the first pass without the kwarg exclusion
  produced `env.positions=env.positions` and was reverted on the spot.
- The one gap tokenize cannot see on 3.11: NAMES INSIDE F-STRINGS. The
  drift-guard test caught the first (`cfg` in a rejection message) —
  the suite doing precisely its job — and an AST FormattedValue sweep
  found the only other one. Post-fix sweep: zero bare references.
- `_would_be_brackets` (10 lines) deliberately stays a closure — the
  defect was never "a closure exists," it was a closure the size of a
  module.

Proof: 1,392 tests pass unchanged (tests are the spec; none were edited),
golden backtest byte-identical, and the live bot restarted onto the
extracted code — clean import, risk tick running, next decision 00:01 UTC.
tests/test_code_structure.py pins the win: `_process_signal` must stay
module-level, `_run_cycle` ratchets at ≤520 lines (now ~490, was 806), and
no nested function may exceed 50 lines.

Assessed and deferred, with reasons: further carving `_run_cycle` into
stage functions (it is now a linear pipeline with phase comments and no
oversized closures — more churn on the live path buys style, not safety),
and the same treatment for `simulate_ensemble` (405L, four small
closures, all depth-1) and `dashboard.render` (356L, display-only). The
ratchet test holds the line either way.

3 tests added, 1,395 total.

## §47 — E9: the intake sweep — one weak candidate parked, one family closed twice

**RESEARCH INTAKE (2026-08-13). K stays 64.** Exchange netflow (BTC/ETH,
daily) parked as C4: data verified free (CoinMetrics community flow
series), fully gateable (daily signals — no C1-style trade-count problem),
and honestly the least-evidenced candidate on file — the solid literature
is intraday, the daily claims are practitioner survivorship. Prior: low;
a registration would predict FAIL. Calendar/day-of-week effects: intake
CLOSED without parking — current literature reads the old anomalies as
post-2015 artifacts, and the one live finding (weekend momentum
differential) lands inside the momentum family §14/§20 already closed.
C2's pre-registration text was frozen in backtest_candidates.md while the
forward sample is too young to tempt the design.

## §48 — E10: the programme re-scored on its own rubric

**INFRA CLOSE-OUT (2026-08-13). K stays 64.** The 2026-08-12 audit scored
~5/10. After E1–E9: ops 5→8.5, tests 7→8.5, security 6→8, docs 3→8.5,
structure 5→7.5, research 9 (unchanged), live evidence 1 (unchanged and
calendar-bound — no programme moves it, only closed trades). Overall
**~5 → ~8**, table with per-row evidence in README.md, each row citing
its §-entry.

What "fully enterprise ready" still honestly requires, with owners:
- **The Bizon cutover** (deploy/BIZON.md, owner's hands) — the last ops
  deduction AND §22's cost-model re-grounding both terminate there.
- **Closed trades** (calendar) — live evidence, the decay sample, C2's
  diagnostic, and the learning loop's first real lesson all wait on the
  same clock.
- The E-programme's one deliberate debt: GUIDE/HEARTBEAT are bannered,
  not rewritten; dashboard.py/backtest.py remain large files behind
  ratchet tests.

Eight sections (§39–§46) shipped in one day, every one verified by
execution, every one green in CI. The bot that was silently dead for 175
hours a week ago now pages when its pager breaks, backs itself up loudly,
measures its own coverage, documents itself truthfully, and carries the
same research discipline it always had — which remains the only thing
here that can ever make it profitable.

### §48 addendum — the fix was host-dependent, and the fix-watcher watched the wrong thing

Found ~2h after §48 was written: CI on main had been RED since §43 while
every local suite run was green. Two failures of mine, both instances of
lessons this record already carries:

1. **§39's backup alarm measured the laptop.** `backup_problems()` defaults
   to the cwd-relative `backups/`, which exists here (real archives) and
   not on a CI runner (gitignored) — so four unrelated watchdog tests
   failed IN CI ONLY. "CI measures the laptop," inverted: the laptop
   satisfied a condition CI couldn't. Fix: `check()` threads an explicit
   `backups_dir`; the four tests provide a satisfied fixture; production
   omits it and gets the real alarm. Proven by running the FULL suite with
   `backups/` moved aside — the CI-faithful condition — 1,395 green.
2. **The CI watcher itself reported on the wrong object.** Each phase's
   `gh run watch $(gh run list --limit 1 ...)` grabbed the newest run id
   BEFORE the just-pushed commit's run registered — so it watched the
   previous (green) run and exited 0. Four phases shipped over a red main
   while their watchers said green. An instrument that can't fail visibly
   is not evidence — §24's sentence, now paid for personally. Watches are
   keyed to the pushed SHA from here on.

## §49 — INFRA: the forming-bar guard was an equities fossil, and it starved the whole cross-section

**Claim class: INFRA (defect fix). K unchanged at 64.**

Found while answering "why hasn't repete1 traded in a while": the 2026-08-14
13:41 UTC catch-up cycle logged `HOLD (xsmom) — cross-section unavailable or
too small` for every symbol — n=0 against the ≥4 minimum, so the one enabled
strategy could neither enter nor rank-exit its own two open positions (NEAR,
ZEC). The venue was fine: a live probe returned exactly 253 daily bars for
every symbol tested.

**Root cause — `datacheck.drop_forming_bar` still carried the equities
ET/16:00 session rule on a venue whose daily bars close at 00:00 UTC.** Both
sides of the rule were wrong here, in opposite directions:

1. **At the scheduled 00:01 UTC cycle** (20:01 ET — "after the close" in ET
   terms), the guard KEPT the newly-opened bar: a one-minute-old stub fed to
   strategies as the newest daily close. Every live cycle since the crypto
   fork traded on an input no backtest measured. (Benign for xsmom, whose
   skip_bars=21 ignores the newest month — which is why this never surfaced —
   but wrong for any strategy that reads the newest close, i.e. most of them.)
2. **At daytime catch-up cycles** (host asleep at 00:01, cycle fires on
   wake), the guard correctly dropped the forming bar — out of an
   exactly-lookback fetch, leaving 252 < 253 bars, which excluded EVERY
   symbol from xsmom's cross-section at once. A starved ranking wears the
   same clothes as a quiet market: `HOLD`, every day, no error anywhere.

**Fix, both sides:** `drop_forming_bar` now uses UTC-calendar semantics — a
bar dated today-in-UTC is forming at every hour of the day, no "post-close"
window exists — and `_run_cycle` fetches `lookback + 1` bars when trimming so
the drop can never leave the most demanding strategy short. This moves live
TOWARD the backtest model (signals on the close of the last COMPLETED bar),
i.e. it closes a divergence rather than opening one.

**Verified by execution:** full-universe live-shaped run post-fix: 21/21
symbols ≥253 completed bars after the trim, xsmom cross-section **n=21**
(was 0), NEAR/USD rank 2/21 and ZEC/USD rank 1/21 — both top-half, both
correctly held by the exit rule rather than by starvation.
`tests/test_forming_bar.py` rewritten to pin UTC semantics, including the
exact 20:01-ET input the old rule got wrong and a fetch-plus-one starvation
regression. Suite: 1,394 passed.

**Also closed in this pass — the pager URLErrors (2026-08-13 20:00 →
2026-08-14 09:50 UTC):** not a dead webhook. The host resolves and reaches
the ntfy origin fine (DNS 4 records, origin 200), `state/pager_health.json`
shows recovery at 14:02:48 UTC with failures reset to 0, and every URLError
burst coincides with a sleep/wake window in which heartbeats were tens of
thousands of seconds stale — the network simply wasn't up when the watchdog
fired. Failure class: transient host-side unreachability, the same
sleeping-laptop disease §28 measured for order books, cured by the Bizon
cutover and not by code. The §39 self-health instrumentation measured the
entire episode correctly — this is what "an instrument that can express its
own failure" buys.

## §50 — GOVERNANCE: the EXPERIMENT claim class — paper-enabled forward tests with pre-registered kill criteria

**Claim class: GOVERNANCE (like §32's enablement decision). K unchanged.**

**Owner decisions, 2026-08-14, all three explicit:** (1) the success bar for
this bot is **beating buy-and-hold BTC risk-adjusted** — the benchmark that
has quietly beaten everything the 64 trials tested; (2) because repete1 is
paper-only, promising-but-unproven strategies **may be ENABLED in paper as
labeled forward experiments** — the owner accepts that the track record
becomes a mix of experiments rather than one clean line; (3) at most **four**
experiments run concurrently — dilution has a cap.

**What an EXPERIMENT is.** A strategy enabled without an EDGE pass, carrying
ALL of:

1. **A hypothesis** — what would have to be true of the market for this to
   make money, written in its gate-log section.
2. **Pre-registered kill criteria** — committed BEFORE enablement, in the
   gate log and echoed in the strategy's config block. A kill criterion that
   fires is executed, not renegotiated (§18 meanrev precedent).
3. **A machine-readable label** — `experiment: "§NN"` in the strategy's
   config block, pointing at the section that registered it.
4. **A monthly review** — first ~2026-09-14 — appended to this log: the
   experiment's measured alpha vs BTC buy-and-hold over its own window, and
   a live/kill/continue verdict against its own pre-registered criteria.

**What an EXPERIMENT is not.** It is not adopted, not "passed", not evidence
of edge until its forward record says so under the same statistical
discipline as everything else here. Enabling one moves no money anywhere —
that is precisely why this class can exist at all, and it stops existing the
day this bot touches a live credential (it never will; preflight enforces
that).

**Why this is not a loosening of the gate.** The gate answers "does the
backtest survive honest costs and controls?" — a question about the PAST.
Forward paper trading answers the only question the gate cannot: does it
work on data that did not exist when the rule was written? Every trade an
experiment takes is out-of-sample by construction. The discipline moved,
it did not soften: pre-registration now binds the kill rule instead of only
the backtest design.

**Enforcement, not convention:** `tests/test_experiment_governance.py`
fails the build if any enabled strategy lacks its justification — a PASS
verdict in `knowledge/gate_verdicts.json`, xsmom's §32 known-non-edge
labeling, or an `experiment: "§NN"` key whose section exists in this log,
declares kill criteria, and is echoed in the config block. The dashboard
renders each enabled strategy's justification on the operator's window
(`_strategy_labels`), and the success bar renders as a measured number:
bot return vs BTC buy-and-hold over the identical window, with the alpha
in points (`btc_hodl_comparison` — pure, fail-open, absent stays absent).

**Success metric, fixed now:** an experiment "works" iff its alpha vs BTC
buy-and-hold over its own enablement window is positive at its review AND
its kill criteria never fired. "Made money while BTC made more" is a FAIL
of the owner's stated bar, and the dashboard is built to make that
distinction impossible to miss.

## §51 — EDGE (cycle-level methodology, owner-licensed) + EXPERIMENT registration: NUPL long-or-flat BTC

**Claim class: EDGE under a newly-registered cycle-level methodology, plus a
conditional §50 EXPERIMENT enablement. K: 64 → 65. Committed BEFORE any
replication code exists or runs — this section is the pre-registration.**

### The methodology registration (the §38-review blocker-2 condition, met)

Owner decision 2026-08-14, explicit: cycle-level statistics are accepted for
strategies whose trade count is structurally bounded by market-cycle length.
The registered method is the paper's own — **Opdyke (2007) Sharpe-difference
on the full daily return series** of rule vs buy-and-hold — with its honest
price stated up front: the daily series has thousands of points but the
strategy makes ~3 decisions per decade, so the effective sample is **n = 3
cycles** and one structural break (the ETF era changing the marginal holder)
erases the pattern undetectably. **Scope limit, binding:** this methodology
may only ever score candidates with ≤1 round trip per market cycle. Using it
to rescue a high-frequency candidate from per-trade scrutiny is the §8 move
and is refused in advance.

### The arm — exactly one, chosen on stated a-priori grounds

**Long-or-flat BTC/USD: enter when NUPL < 0; exit to flat when NUPL ≥ 0.67.**
(NUPL = 1 − 1/MVRV, computed from the frozen snapshot's raw MV and MVRV
series; Grobys, Näsman & Sandretto 2026, Table 3 row "NUPL 1".)

- **NUPL over MVRV-Z:** NUPL is an algebraic identity with zero derivation
  freedom; MVRV-Z requires a σ(MV) convention the snapshot manifest
  deliberately refused to bake in. This chooses AGAINST published
  performance (the paper's Z variants scored higher) in exchange for zero
  researcher degrees of freedom — the un-flattering direction.
- **Exit 0.67, the lowest published band:** successive BTC cycles show
  diminishing amplitude, and the 2022–25 cycle reached NO published exit
  band at all — the lowest band is the only one with a live chance in an
  attenuating regime. Robustness argument, fixed before computation.
- **No sensitivity arms** (§11's inert-arm lesson). The other five published
  variants may appear in the replication output as REPORTED diagnostics,
  adoption-invalid.

### Disclosure (§37 pattern)

§38's MEASUREMENT already computed and published (dashboard cards, since
2026-08-12) the current-cycle unrealized return of all six published
variants — including the fact that every variant sits in one open trade
entered 2022-06-19 that has never exited. So this registration is NOT blind
to the rule's present state: **state-sync initialization (below) is chosen
knowing it implies an immediate BTC entry at enablement.** What has NOT been
computed anywhere: the replication statistics this section registers
(Opdyke Sharpe-difference under our conservative lag and cost model).

### The replication test (runs only after this section is committed)

On frozen snapshot `onchain_20260812.json.gz` (sha256 9b529bda…, 5,869 days,
no gaps): era 2013-12-07 → 2026-08-11 to match the paper, full-snapshot era
as a secondary diagnostic. **Conservative lag binding:** the decision at the
close of bar D reads NUPL dated ≤ D−1 (manifest `conservative_lag_rule`).
Our cost model applied (52 bps round trip — negligible at 3 trades/decade,
applied anyway). Report: Opdyke Sharpe-difference (rule vs B&H) with t-stat,
per-cycle entry/exit dates against the paper's Table A1, max drawdown of
both legs, and the 2022–25 open-trade status.

### Prediction, stated now

The full-era replication reproduces the paper's direction — rule Sharpe
above buy-and-hold, entry/exit dates within ~2 days of Table A1 (our lag is
1 day more conservative). The Sharpe-difference t-stat lands high (the
method's known flattery of n=3). The honest maybe: whether the 0.67 exit
has fired in the 2024–26 era — if it has not, the rule is one ~4-year open
trade and the EXPERIMENT below is the only forward test that means
anything. Fifty-fifty the forward experiment ever completes a round trip
within a year of enablement.

### Conditional EXPERIMENT enablement (§50 class)

IF the replication reproduces the paper's direction AND the implementation
passes parity tests, `mvrv_cycle` is enabled in paper as **EXPERIMENT §51**:

- **Hypothesis:** BTC's on-chain cost-basis cycle (capitulation → euphoria)
  sorts multi-month holding windows well enough that long-or-flat timing
  beats buy-and-hold risk-adjusted, out of sample, after costs.
- **Sleeve:** BTC/USD only, sized by the EXISTING rails
  (`risk.max_position_pct` 10% — not the paper's 100%; this experiment
  tests the signal's timing, never the allocation).
- **State-sync initialization:** at enablement the strategy adopts the
  rule's replayed state from the full series. If that state is LONG, the
  entry executes at the live price on enablement day and is journaled as a
  state-sync entry — measured from OUR price, never back-dated.
- **Kill criteria, committed now:**
  - **K1 (performance):** sleeve alpha vs BTC buy-and-hold ≤ −25 pp at any
    monthly review, identical windows → kill.
  - **K2 (data):** on-chain series stale > 14 days → entries suspended;
    stale > 60 days → kill.
  - **K3 (implementation):** live rule-state diverging from a verbatim
    offline replay for > 3 consecutive days → kill until fixed; re-enable
    requires a new § entry.
  - **K4 (governance):** two consecutive missed monthly reviews → auto-kill.
    An unreviewed experiment is unowned.
- **Review cadence:** monthly, first 2026-09-14, appended to this log.
- **Fail-open polarity:** stale or missing on-chain data ⇒ HOLD current
  state, never crash, never synthesize a value (the fees lesson).

### §51 addendum — replication results (run 2026-08-14, after registration commit 509c154)

Snapshot verified (sha 9b529bda…, 5,869 days). Registered arm, paper era
(2013-12-07 → 2026-08-11), conservative D−1 lag, 52 bps round trip:

- **Trades: 3** — 2014-10-05→2017-05-20, 2018-11-20→2020-12-27,
  2022-06-14→**OPEN**. Same cycle structure as the paper's Table A1; exact
  dates differ (ours is the NUPL family under a 1-day-more-conservative
  lag).
- **Sharpe 0.788 (rule) vs 0.572 (B&H), ΔSR +0.217.** Ann. log return
  0.396 vs 0.395 — the rule's whole risk-adjusted edge is drawdown, not
  return: **max DD −60.4% vs −83.1%**.
- **Significance — the part that matters: NOT distinguishable from zero.**
  JK-Memmel z = 1.04; stationary block bootstrap (2,000 draws, mean block
  20d) ΔSR 95% CI **[−0.189, +0.644]**, P(ΔSR>0) = 0.854. Our-window
  secondary: ΔSR +0.150, CI [−0.265, +0.606], P = 0.761.
- Reported diagnostics (adoption-invalid): exit 0.70 → ΔSR +0.269
  (P=0.902); exit 0.73 → ΔSR +0.525, CI [+0.188, +0.906], z=2.90. The
  highest published band is the one that clears — noted and REFUSED: the
  registered arm is 0.67 and stays 0.67; switching to the best-scoring
  variant after seeing it is §8 by definition.
- Current rule state: **LONG since 2022-06-14**; latest lagged NUPL 0.1751
  — far from both bands. State-sync at enablement therefore means an
  immediate BTC entry, as the registration disclosed it might.

**Prediction scored:** direction reproduced ✓; trade structure matches ✓;
"the t-stat lands high" ✗ — the registered conservative statistic does NOT
land high (P = 0.854), and that miss is the finding: the paper's 15–31
t-stats live in its method, not in the data. Three fat cycle-bets of
information is what n=3 buys.

**Verdict: EDGE FAIL (trial 65 of K spent; direction +, significance
absent). Adoption: none.** The §51 EXPERIMENT enablement condition —
direction reproduced — IS met: `mvrv_cycle` proceeds to implementation and
paper enablement as EXPERIMENT §51 under its pre-registered kill criteria,
which is precisely the class §50 built for a candidate whose backtest
cannot prove itself at n=3 and whose only honest test is forward.

### §51 tally

**65 trials, zero adopted, zero closed trades.** Trial 65 (NUPL cycle, this
section) FAILED as an EDGE claim and proceeds only as a §50 EXPERIMENT —
which is an enablement class, not an adoption.

### §51 implementation note — golden re-capture (metadata-only)

Adding `mvrv_cycle` to the strategy REGISTRY changed the golden baseline's
ensemble `params.members` metadata. Verified before re-capturing: every
trade, pnl, and blocked count byte-identical, and mvrv_cycle's own ensemble
row is {trades 0, pnl 0.0, blocked 0} — behaviorally inert in the OHLCV
fixture (no BTC/USD reference bars ⇒ stale ⇒ hold), exactly the designed
fail-open. mvrv_cycle is GOLDEN_EXCLUDED from the single-strategy captures
with the reason written in capture_golden.py: its input is an on-chain
series, and its determinism net is the sha-pinned replication script plus
tests/test_mvrv_cycle.py. The §38 live-path isolation guard now pins
strategies/mvrv_cycle.py as the ONLY sanctioned on-chain consumer.

## §52 — F3 intake sweep: five untested families, one survivor, zero trials spent

**Claim class: INTAKE (no K). Full review:
knowledge/source-review-f3-sweep-2026-08-14.md.**

Owner-scoped sweep of families genuinely absent from the 65-trial record.
Verdicts: **pairs/stat-arb BLOCKED** (needs a short leg; this venue is
long-only — correcting the F-plan's own "most practical candidate" claim,
which was written before that check); **BTC ETF flows PARKED as C5**, the
sweep's one survivor, with a frozen pre-registration draft (momentum-twin
control mandatory — the published next-day predictability may be momentum
in a flow costume); **stablecoin supply PARKED low** (C6 — event-study
evidence only, pre-2021 era, causality disputed); **hash ribbons PARKED
low** (C7 — zero peer-reviewed validation; the §51 cycle methodology is
NOT extended to survivor-published lore); **volatility risk premium
BLOCKED twice** (selling options is a different system; no free options
history). The record's honest shape holds: most families park.

## §53 — EDGE pre-registration: C4 exchange netflow, long-or-flat BTC. K: 65 → 66

**Committed BEFORE the snapshot builder or gate code exists. The parked C4
entry (2026-08-13) predicted FAIL at parking time; this registration
executes the plan's disposition step and keeps that prediction.**

- **Hypothesis:** BTC held long when trailing-3-day aggregate exchange
  netflow (FlowInExUSD − FlowOutExUSD, CoinMetrics community) is NEGATIVE
  (net outflow = coins leaving exchanges = holding), flat otherwise, beats
  buy-and-hold risk-adjusted after costs.
- **Arms: exactly one.** Sign threshold (zero free parameters — no fitted
  percentiles). **BTC only** — ETH is excluded a priori so there is no
  after-the-fact choice between two assets.
- **Lag:** the §38 manifest's conservative rule verbatim — decision at the
  close of bar D reads flow values dated ≤ D−1.
- **Costs:** 26 bps per side, charged on each state flip (the §51
  machinery reused verbatim — this rule flips far more often than NUPL, so
  costs are a real force here, which is part of the prediction).
- **Controls:** (a) §17 random-thinning matched on time-in-market, 2000
  draws — reported; (b) momentum twin — the identical rule keyed to
  trailing-3-day BTC return, matched time-in-market; the flow rule must
  beat its twin for any pass to mean "flow information".
- **Statistic:** annualized Sharpe difference vs B&H, stationary block
  bootstrap (2,000 draws, mean block 20d), JK-Memmel reported alongside.
- **Data:** a §38-mold frozen snapshot (builder + sha manifest + gap scan)
  from CoinMetrics community; BTC returns from the same artifact's MV
  series, identical treatment to §51.
- **Prediction, stated now: FAIL.** Intraday flow effects rarely survive
  daily aggregation; wallet reshuffles read as flows; every practitioner
  chart of this was published because it looked good. Expected shape:
  ΔSR indistinguishable from zero AND the momentum twin does as well or
  better; costs bite. Registered anyway because the plan's disposition
  step is to close C4 with a verdict instead of leaving it parked forever.

### §53 addendum — result: FAIL, exactly as registered

Snapshot frozen first (data/netflow_20260814.json.gz, 5,591 days
2011-04-24 → 2026-08-13, 0 gaps, sha 30e9a084…). Registered arm on the
§51-matched era: **Sharpe 0.129 vs B&H 0.572, ΔSR −0.442, bootstrap 95% CI
[−0.983, +0.069], P(ΔSR>0) = 0.040** — significantly WORSE than
buy-and-hold. 560 state flips at 46.5% time-in-market; costs and missed
drift did what the prediction said they would. The momentum twin (ΔSR
−0.293) also loses to B&H but BEATS the flow rule — netflow carries
negative information beyond momentum at this horizon.

**Method caveat, recorded rather than hidden:** the §17 thinning control
as implemented (random states matched on time-in-market) is uninformative
for STATE rules — random states flip near-daily and drown in flip costs,
so "beats 100% of random states" means nothing here. The verdict rests on
the primary statistic and the twin control, which need no help.

**Prediction scored: correct in full** (FAIL, costs bite, twin does as
well or better). **C4 is CLOSED.** Trial 66 of K spent. Tally:

**66 trials, zero adopted, zero closed trades.**

**C2 status (F4's other item):** unchanged — the funding pre-registration
draft stays frozen; first joined-sample check ~2026-09-13, now folded into
the §50 monthly experiment review so one calendar owns both.

## §54 — ENABLEMENT: mvrv_cycle live in paper as EXPERIMENT §51

**Claim class: GOVERNANCE (§50 enablement; no K).**

The §51 conditions are met — direction reproduced in the replication,
implementation landed with parity to the replication's state machine, 15
offline tests covering enter/exit/lag/staleness, and the forward collector
running (state/onchain_live.json, 5,871 days through 2026-08-13).
`mvrv_cycle` is enabled in paper, effective the next decision cycle.

- **Experiment pool after F2–F4: exactly one.** The F3 sweep parked or
  blocked everything else (C5 ETF flows is the next candidate, gated on
  its data build and a fresh registration); §53's netflow gate FAILED as
  predicted and closed C4. One experiment, cap of four — under-filled by
  the evidence, not by the policy.
- **What happens next, stated before it happens:** the rule's replayed
  state is LONG (since 2022-06-14, latest lagged NUPL ≈ 0.175). The next
  cycle should therefore fire the §51 state-sync BTC entry — a BUY at the
  live price, sized by the normal rails (~10% cap), subject to the judge's
  veto like every entry. Then, most likely, months of "hold" — which is
  the strategy working, not stuck.
- **Kill criteria in force (§51):** K1 alpha ≤ −25pp at review; K2 data
  staleness (14d suspend / 60d kill); K3 replay divergence >3d; K4 two
  missed reviews. **First monthly review: 2026-09-14**, covering this
  experiment's alpha vs BTC, the xsmom decay sample, and C2's joined
  funding sample — one calendar, three questions.
- The dashboard renders the EXPERIMENT badge, the per-strategy
  justification line, and the vs-buy-and-hold-BTC card group (§50) — the
  owner's bar is a number on the page, not a promise in a log.

## §55 — GOVERNANCE: shadow mode — forward evidence for the five disabled strategies

**Claim class: GOVERNANCE (like §50's EXPERIMENT class). K unchanged: 66.**
Nothing adopted, nothing rejected, no strategy enabled, no trial spent.

**The gap.** Five of seven registered strategies are switched off —
`ma_crossover`, `tsmom`, `xsrev`, `donchian`, `meanrev` — and every one was
gated against history that already existed when its rule was written. §50 names
the question the gate structurally cannot answer: *does it work on data that
did not exist when the rule was written?* For the two ENABLED strategies, paper
trading answers that forward. For the other five, **nothing did.** They accrued
zero evidence while they waited, and the only instruments that could look at
them (`scripts/decay_monitor.py`, `backtest.py`) re-measure the very snapshot
they were gated on. Waiting was not neutral; it was time spent learning nothing.

**What shadow mode is.** Every cycle, each disabled strategy runs against the
same bars the live loop just fetched, through the **full decision stack — the
portfolio rails AND the LLM judge** — and **no order is placed.** Decisions are
written to a separate store. The evidence accrues forward, out-of-sample, on
days that had not happened when the gate was designed, so it cannot have leaked
into it.

**Full fidelity was an explicit owner decision (2026-08-17),** chosen over the
cheaper "strategy in isolation" reading. The cost objection raised at the time
was overstated by ~20x: the judge fires on BUY SIGNALS, not on symbols.
Measured against the frozen snapshot over 120 cycles, all five strategies
together produce **4.93 buy signals per cycle** on a flat book, and fewer in
steady state — a shadow run against real Kraken data made **3 judge calls in
cycle one and 1 in cycle two**, completing in 0.08s and 0.06s.

**What shadow mode is NOT.** Not an arm. It spends no K, moves no trial count,
and may **never** be used for a PASS, a FAIL, an enablement, or a selection
between strategies. Its permitted uses are exactly two:

1. corroboration of a verdict already recorded here, and
2. detection of a live/model divergence.

`config.yaml`'s `strategies:` block is untouched. All five stay disabled.

**Registered biases — carried in the data, not in this paragraph.** Every
scored record and every level of the summary (including each per-strategy
sub-dict, because that is the level a reader copies) carries `optimistic: True`
and `not_a_track_record: True` as FIELDS. `meta.scope_excluded` names them:
no venue latency, no partial fills, no cash contention between the five books
or with the live one, a judge reasoning about shadow's own positions, and fills
priced from a synthetic spread off a bar. Shadow's books COMPOUND, because the
§36 drawdown latch and `daily_loss_breached` read an equity curve and a fixed
book would have a latch that could never engage — which is precisely why the
labelling matters more here, not less.

**Structural guarantees, not promises.**

* **Cannot trade.** `shadow.run` takes no venue, no ledger, no broker, no
  `_CycleEnv`; the module imports none of them. Asserted by AST at the
  definition AND at the call site in `main.py`, each with a negative control
  proving the assertion can fail.
* **Cannot contaminate.** A separate store, keyed `event` where the ledger keys
  `type`, every value `shadow_`-prefixed. repete2 enumerated SIXTEEN ledger
  readers that were each correct about ignoring shadow records only by
  accident; the worst would have put invented profit on a public page. The
  dashboard canary plants a fake 999999 winner and asserts every live region is
  character-identical.
* **Cannot look ahead.** An intent is written at bar *t* with **no fill price**
  and settled at bar *t+1*; the fill bar is chosen with a strict `>` on the
  signal bar. Proven by execution: on signal day there are zero settles.
* **Cannot lose a day.** `settle()` is re-runnable; a missed cycle backfills to
  the correct *t+1* bar, not to whenever the process next woke up.
* **Cannot stop the real cycle.** Never raises; failures become records.

**Exits are recomputed, not remembered** — a strategy's exit rule is part of its
thesis (donchian, meanrev and tsmom are half exit logic), and scoring them on
brackets and a horizon alone would repeat repete2's error of measuring `carry`
with its own thesis deleted.

**The reader ships with the recorder.** repete2 shipped a shadow recorder and
had nothing that scored it for months, so a pre-registered 60-day minimum
accrued toward a read that did not exist. `shadow.summarize`, a `--report` CLI
and a dashboard panel land in the same commit, and a test fails the build if
any of them goes missing.

**First review:** with the §51 monthly review (~2026-09-14). Shadow's numbers
are context for that conversation and can decide nothing in it.

## §56 — INFRA: the bot wrote a trade that never happened

**Claim class: INFRA (defect fix). K unchanged: 66.**
Nothing adopted, nothing rejected, no strategy enabled, no trial spent. This
section corrects the record itself rather than measuring anything.

On 2026-08-19 at 02:17:41Z, `reconcile_closed_positions` wrote an `outcome`
record for trade `f758042b` — BTC/USD, exit 64328.2, **+$21.15, +0.528%,
`result: "win"`, `alpha_pct: +1.068`** — with `exit_reason:
"last_price_estimate"`. The position was still open. It is still open now.

`state/ledger.jsonl` contains **zero sell records of any kind**: no
`paper_fill` with `side: sell`, no sell decision, nothing. The venue's entire
event stream is one deposit, three buy fills and three resting orders. That
single `outcome` is the only one this project has ever written, so every
"closed trade" number the bot could produce — win rate 100%, profit factor ∞,
realized P&L +$21.15 — was 100% fabricated.

### How

Three defects, each individually survivable, which together manufactured a
profit:

1. **A second writer, scheduled.** `scripts/scheduler.py` runs `cycle-catchup`
   hourly at :35. That job is `src/watchdog.py --catchup`, which called
   `main.run_cycle()` with **no `venue=`**, so it built its own `PaperVenue` —
   in a subprocess, because every scheduler job is one.
2. **A venue that never re-reads its own log.** `PaperVenue._replay()` is
   called from exactly one place: `__init__`. Afterwards `_book` changes only
   through events *that instance* emitted. `positions()` re-marks prices
   against a live quote — so the numbers stay plausible — while being wrong
   about which symbols are held.
3. **A reconciler that treats absence as proof.** `reconcile_closed_positions`
   selects ledger-open trades whose `symbol not in positions` and calls them
   exited. `resolve_exit_price`'s last rung then answers "what is this worth
   now?" instead of "did anything sell?", and against `PaperVenue` the two
   rungs above it *structurally cannot* fire for a held position: `get_order`
   returns `paper_order_placed`, and `closed_orders` yields only `kind == FILL`
   records, which for an unsold position is just the buy.

So: the catch-up bought BTC/USD at 03:36:42 on 08-18. The long-lived `live.py`
daemon, whose book had been replayed *before* that buy, never saw it, and 22
hours later declared the position closed at the current mid. Thirty seconds
after booking the "win" the same daemon tried to **buy BTC again** and was
blocked only by position sizing.

The fingerprint is in the log: `positions_mark` events at minute :03/:18 carry
no BTC (the daemon), those at :35/:37 do (the catch-up). The entry and the
outcome even carry different `model_version` hashes — `4eed8f0f1427` versus
`a37a25c3756c` — two processes on two code states.

### What was wrong in this log, and stays wrong

The standing tally has said *"zero closed trades"* since §53. From 2026-08-19
to 2026-08-21 that was **false**: the ledger held one, and it was invented. The
tally was right about the thing that matters — no strategy has produced a real
closed trade — and wrong as a description of the file. Recorded here rather
than edited into §53, per this log's own rule; the retraction is the part a
future reader needs.

`tests/test_reconcile.py::test_fallback_to_last_price_estimate` **asserted the
defect was correct behaviour.** It has been re-specified, in the same commit as
the fix, with the incident named in its docstring. A test can pin a bug as a
feature, and this one did for as long as it existed.

### The fix, and what each part cannot do

* **`watchdog.live_loop_is_running`** — the catch-up refuses to run while the
  live loop is stamping `heartbeat_live`. Unreadable beat means *run*: a
  monitor that cannot see its input must not suppress a recovery.
* **`PaperVenue.has_foreign_writes` + `main.second_writer_detected`** — the
  cycle **aborts** on a foreign write rather than re-replaying. A foreign write
  means a second writer exists, and recovering quietly would hide the
  condition instead of fixing it.
* **`resolve_exit_price(..., allow_price_estimate=False)`** — now the default.
  No fill evidence means the trade stays OPEN and a `reconcile_error` is
  ledgered, which is what `test_broker_errors_never_crash_cycle` already
  demanded of the error path. The rung is kept, not deleted, because a real
  exchange adapter may genuinely lack order history — it has to be asked for.
* **`JsonlStore.append` takes an exclusive `flock`.** This orders appends; it
  does **not** make a stale in-memory book correct, and it is not what fixes
  this. `read_all` already tolerated torn lines, and that tolerance was
  treating the symptom.
* **`ledger.voided_trade_ids`** — a retraction is an appended record, scoped by
  `trade_id`, honoured in `closed_trades()` and `open_buys()`. One append
  therefore reaches all ~20 readers of the record, including
  `risk.live_kill_blocked`, which sits in the **live decision path**, and
  `learn.resolve_realized`, which was scoring the judge's calibration against a
  fabricated win.

`tests/test_two_venues_over_one_store.py` reproduces the incident with two
venues over one store and was **verified by negative control**: neutering the
detector fails two of its three tests.

### What is NOT resolved

* **The laptop ledger still contains the record.** Voiding it is an append the
  owner runs; nothing here writes to `state/`.
* **The Bizon's ledger is unaffected** — it started fresh at the 2026-08-20
  cutover and its two closed trades are real (both losers, realized −$15.83).
* **No re-measurement.** Every gate verdict in this log was produced offline by
  `backtest.py`, which has no reconciler and no venue, so no number above moves.
* **The dashboard published the fabricated win** for two days as "100% win
  rate, profit factor ∞". The live page has since cut over to the Bizon and now
  reads 0%; nobody was shown a corrected laptop page, and that is worth saying
  out loud rather than letting the cutover quietly absorb it.

**66 trials, zero adopted, zero strategies producing a real closed trade.**
Unchanged: fixing a defect that fabricates evidence is not a trial, and nothing
here was adopted.

### §56 addendum — the Bizon was affected too, and this section's own claim was wrong

**Appended 2026-08-21, hours after §56.** Correcting §56, not replacing it.

§56's *"What is NOT resolved"* said: *"The Bizon's ledger is unaffected — it
started fresh at the 2026-08-20 cutover and its two closed trades are real (both
losers, realized −$15.83)."*

**Both halves are false.** The Bizon's ledger was inspected directly after §56
was written:

```
paper_fill records : 5   (ALL buys)
sell fills         : 0
outcome records    : 2   ← both exit_reason "last_price_estimate"
```

The same defect, on the production host, in the twenty hours *after* the
cutover:

| Time (UTC) | What |
|---|---|
| 08-20 22:37:57 | cycle completes — NEAR qty **2,259.76** @ 1.7701 |
| 08-21 00:01:45 | `outcome` — ZEC "closed" −$15.15, `last_price_estimate` |
| 08-21 00:02:19 | `outcome` — NEAR "closed" −$0.68, `last_price_estimate` |
| 08-21 00:04:51 | cycle completes — NEAR qty **1,806.17**: a *re-buy* |
| 08-21 00:36:10 | cycle completes — NEAR qty **4,065.93** = 2,259.76 + 1,806.17 |

The `:00–:04` process phantom-closed positions its stale book could not see and
then bought them again; the `:35–:36` process, holding a complete replay, shows
the sum. So the bug did not only fabricate P&L — it **double-sized two
positions**. NEAR and ZEC are each held twice over.

**The corrected count: repete1 has never had one genuine closed trade on either
host.** Eight buys, zero sells, three fabricated outcomes across two ledgers.

All three are now voided (`f758042b` on the laptop, `1a1161c6` and `51f12e82` on
the Bizon), the originals left on disk.

### Two lessons, and the second is the uncomfortable one

**The fix was right and the surrounding claim was wrong.** §56 correctly
diagnosed a reconciler that trusts a stale snapshot, and in the same breath
asserted a "real" closed-trade count taken from the dashboard **without checking
`exit_reason` on the underlying records** — which is the identical error, one
level up. Adopting a number because a summary reported it is what the whole
programme exists to refuse. Recorded rather than quietly amended: the pattern is
more useful than the correction.

**Fixing the ledger was not enough, and the page said so.** §56 claimed the
`voided` marker in `Ledger.closed_trades()`/`open_buys()` "reaches all ~20
readers". It did not. **Six readers consume raw `outcome` records without going
through that join** — `health._open_buys_count`,
`scorecard.realized_pnl_by_month`, `review.build_report`,
`dashboard.realized_pnl_series`, `evidence.lineage` and
`evidence._closed_trades`. After voiding, the published dashboard read **"2
closed trades"** beside **"$0.00 realized P&L"**: a page disagreeing with itself,
each half looking sourced. `viewmodel.voided_trade_ids` is now the single
definition, every reader imports it, and
`tests/test_voided_outcome_reaches_every_reader.py` walks all six together with
a negative control so a seventh cannot quietly reintroduce the split.

### Deployed

`main` at 6f6a8cd is live on the Bizon; the suite runs 1,552 green there on
Python 3.12 as well as 3.11 in CI. The unit was `disabled` — running, but it
would **not have survived a reboot**, which was the entire point of leaving the
laptop. It is `enabled` now.

**66 trials, zero adopted, zero closed trades.** The tally returns to what it
said before §56, and this time it is true.

## §57 — MEASUREMENT: the cost model is roughly right, and the "10x understated" claim was mine and wrong

**Claim class: MEASUREMENT (instrument check). K unchanged: 66.**
Nothing adopted, nothing rejected, no strategy enabled, no trial spent.

An audit on 2026-08-21 asserted that every one of the 66 gate verdicts was
priced at **5 bps** of slippage while live execution measured **52.2 bps**, and
called it "an order of magnitude too low" — the second of three reasons the
record might be wrong. Phase 3 set out to re-gate everything at the honest
number. Measuring it properly says **there is almost nothing to re-gate.**

### The measurement, and why it is the right one

`fill_quality.slippage_bps` is `(fill − signal)/signal` where `signal` is the
**last closed bar's close**. It therefore contains price DRIFT from that close
to the moment of execution, plus half the real spread, plus impact.
`base_impact_bps` is the impact term alone, and a backtest already absorbs the
gap because it fills at the **next bar's open**. The two are not the same
quantity, and the drift term dominates.

`scripts/measure_spread.py` (new, read-only) measures the quantities the model
actually holds, from `data/orderbook_live.jsonl` — 483 samples, 21/21 symbols,
2026-08-20T22:22 to 2026-08-21T20:05. It walks the real ask ladder for a
$10,000 order and takes the VWAP against the mid. No model is involved; it is
the thing the model approximates.

| quantity | modelled | measured |
|---|---|---|
| half-spread | 3.00 bps | **2.24 bps** (median) |
| impact, $10k order | 5.00 bps | **6.2 bps** (median walk) |

Worst symbol 18.9 bps (FET), best 0.5 bps (BTC). **The cost model is
approximately correct**, and `synthetic_half_spread_bps: 3` is mildly
conservative, which is the safe direction.

### What the 52 bps actually was

Drift. NEAR/USD measured **165 and 167 bps** signal-to-fill on two live buys and
was the reason the median looked catastrophic. Walking NEAR's real ladder for
the same size costs **6.3 bps**. The alt moved overnight; the execution was
fine. The median of five drift-inclusive fills was never evidence about impact.

### The finding that is real, and it points the other way

`impact = base + k·sqrt(notional / top_of_book_notional)` uses **level-1 depth
only**, and level-1 depth in this universe is tiny — universe median top-of-ask
is **$368**. So the formula, evaluated at measured depth for a $10k order,
returns 36–321 bps against a walked truth of 0.5–18.9 bps.

In a **backtest** that term never fires (bar data has no book, so it collapses
to `base`) — which is why backtests are close to right by accident. **Live it
does fire**, on real quotes. So the live paper venue is plausibly
*overcharging* impact on thin books by 5–50×, which biases the live record
**pessimistic** — the opposite of every other bias this log has recorded. Not
yet a divergence claim; it needs a fill-by-fill check against the same books,
and no strategy has produced a closed trade to check against.

### What was actually wrong, and stays wrong

* `backtest.py`'s CLI ended with an **unconditional**
  `cfg["slippage"]["base_impact_bps"] = slip_resolved`, so `config.yaml` was
  discarded for that entry point while `capture_golden.py`, `gate_compare.py`
  and every direct `bt.simulate()` caller honoured it. Accidental **and**
  inverted. Now an explicit precedence: `--slippage-bps` → config
  `backtest.slippage_bps` → leave the live model alone.
* The **auto-calibration was a live hazard.** With ≥10 clean fills,
  `measured_slippage_bps` would have silently re-priced every future gate run
  with the drift-contaminated number — the exact error this section corrects,
  applied automatically and with no record. It is now opt-in behind
  `--slippage-from-ledger` and documented as usually wrong.
* `slippage.base_impact_bps` is **shared with the live venue**
  (`fills.FillModel.from_config` ← `venue/paper.py` and `backtest.py` both).
  Editing it to make gates stricter would have re-priced live paper fills
  mid-record with nothing marking which model priced which fill. The new
  `backtest.slippage_bps` key exists so the two can move independently.
* `synthetic_half_spread_bps` is documented **BACKTEST ONLY** in three places
  and prices **every live protective exit** via `paper.py:_close_at`. Open.

### Limits, stated rather than implied

The collector stores **10 ladder levels**. For CRV, UNI, ALGO and ZEC those ten
levels total **less than $10,000**, so their walked costs are LOWER BOUNDS. And
this is today's book against a 2019–2026 gate window; no venue sells historical
L2 depth for this universe at a price this project will pay. Both limits make
the read optimistic.

### Consequence for Phase 3

The planned re-gate of all 66 trials at a corrected slippage **is not
justified**: the correction is 5 → ~6 bps, inside the noise of a 1.5× fee-stress
arm the gate already mandates. No verdict moves. The golden is untouched and CI
stays green. What survives from Phase 3 is the instrument work above, and one
genuine open question — whether the live venue overcharges impact on thin books.

**66 trials, zero adopted, zero closed trades.** Measuring the instrument is not
a trial, and nothing here was adopted.

## §58 — CONTROL: the ablation ladder. The agent is inside the coin flip's range.

**Claim class: CONTROL. K unchanged: 66.**
Nothing adopted, nothing rejected, no strategy enabled, no trial spent. Null arms
are instruments, not candidates — the `regate_donchian.py` convention.

The audit of 2026-08-21 named this the cheapest decisive experiment: *does the
apparatus beat a coin flip and a passive hold, once costs are charged?* It does
not.

### Pre-registration, and one deviation to disclose

The arms, the pass mark, the judge setting and the salt list were fixed in the
owner-approved plan **before any code was written**. They did not change after
seeing a result. **But the spec was transcribed into this log AFTER the first
smoke run**, not before, which is a deviation from the protocol's own ordering.
Recording it rather than letting the timestamps imply otherwise: the content is
unchanged, the sequence was wrong, and a reader is entitled to weigh that.

| Item | Value |
|---|---|
| Arm (i) | shipped ensemble — `xsmom` + `mvrv_cycle` |
| Judge simulator | **OFF** for every arm |
| Pass mark | arm (i) beats **both** (ii) and (iv), Bonferroni-corrected bootstrap CI excluding zero |
| Salts | `abl-1` … `abl-5`, fixed in advance |
| Snapshots | bars sha `078438ba28ca…`, on-chain sha `9b529bdada85…`, verified at run start |

### The result

```
  arm                       ret%      PF   maxDD%     n     costx
  i.  full agent           -5.80    0.74    19.82    28     -3.80
  ii. random entry        -11.60       —        —    16         —   [-15.83 .. -1.75] over 5 salts
  iii.SMA cross           -22.27    0.04    22.27    34    -17.37
  iv. buy and hold         -4.64       —        —    21         —
  v.  rails only          -13.57    0.32    51.45    23    -12.69
```

**RESULT: FAIL.** Two readings, and the second is the one that matters.

1. Arm (i) **loses to buy-and-hold** (−5.80% vs −4.64%). Doing nothing beat the
   apparatus on this window.
2. Arm (i) beats the random-entry *median* (−11.60%) — and then the band settles
   it: **five salts span −15.83% to −1.75%, and −5.80% sits comfortably inside
   it.** The agent's return is not distinguishable from a coin flip that trades
   as often as it does. That is the entire point of running the null five times
   instead of once; a single random arm at −11.60% would have looked like a win.

Every bootstrap comparison is **INCONCLUSIVE** at K=66. Against random entry the
difference is +$589/trade with a 99.92% CI of [−$419, +$2,012]; against
buy-and-hold, +$14/trade with [−$8,759, +$3,888]. **n=28 closed trades cannot
resolve this question**, and no arrangement of the same data will.

### DIAGNOSTIC: the live pairing is the worst configuration tested

`SimTrade` carries no owning-strategy field, so attribution required re-running
each half alone:

```
    xsmom                   2.95    1.14    16.39    31      3.24
    mvrv_cycle              0.00    1.00     8.87     3      1.00
    ensemble                -5.80   0.74    19.82    28     -3.80
```

**The shipped ensemble is 8.75pp WORSE than `xsmom` alone**, while `mvrv_cycle`
by itself neither makes nor loses money (0.00%, n=3). Neither component loses;
the *pairing* does. The mechanism is the §54 collision shape: `mvrv_cycle` is
long-or-flat BTC and holds for long stretches, occupying a slot and cash that
`xsmom` would otherwise deploy. Both are enabled on the live host right now.

**This is a signal, not a verdict.** The ensemble-vs-xsmom difference is
−$302/trade with CI [−$1,805, +$1,428] — it includes zero, like everything else
here. It does not override §51's pre-registered kill criteria or its review
date, and nothing is disabled on the strength of it. It is recorded because a
configuration that underperforms its own best component is worth knowing before
the next monthly review, not after.

### What this ladder could not measure

**The LLM.** `backtest.py` never imports `llm` by design; the `judge_model`
simulator reproduces the judge's downsize *distribution* from a **7-day equities
calibration (n=146)**. Running it would have added identical foreign noise to
every arm. It was OFF everywhere. Whether the judge adds or destroys value
remains untested and untestable by this instrument.

### Limits, stated rather than implied

* **One OOS window**, and the 0.7 split is applied **per symbol**, so each
  market's window starts on a different calendar date. This is not one period
  and is not described as one.
* **Buy-and-hold enters the bootstrap as 21 per-symbol P&Ls**, a smaller and
  differently-shaped sample than a trade list. The comparison is correspondingly
  weaker.
* **The universe is survivorship-conditioned** (`data/UNIVERSE.json`), which
  biases every arm's return upward — including the nulls, so the *comparison* is
  less affected than the levels.
* `mvrv_cycle` normally reads the **mutable** `state/onchain_live.json`, which is
  why `capture_golden.py` excludes it. This run pinned it to the frozen
  `data/onchain_20260812.json.gz` (coverage 2010-07-18 → 2026-08-11, against
  bars ending 2026-07-29). **This is the first gate in the project that can run
  `mvrv_cycle` reproducibly.**

### What was built

`scripts/gate_ablation.py`, `scripts/ablation_arms.py` (the two null arms, kept
OUT of `strategies.REGISTRY` and out of `config.yaml` — they are instruments,
and `src/main.py` orphans a position whose strategy is not registered), and
`tests/test_ablation_arms.py`. Ten tests, including the **negative control that
gives the variance band meaning**: same salt reproduces exactly, a different
salt redraws, and a symbol's draws do not depend on how many other symbols were
evaluated first. Without that last property the arm would measure scan order
rather than chance.

### The honest conclusion

After 66 registered trials, zero adoptions, zero genuine closed trades, and now
a five-arm ablation: **there is no evidence that this apparatus adds anything to
a coin flip, and it lost to doing nothing.** The strategies are not carrying
information at a scale this sample can detect. The engineering — the rails, the
gate protocol, the divergence hunting, the append-only record that made this
finding possible — is real and is the asset. The alpha is not there.

**66 trials, zero adopted, zero closed trades.** A control spends no budget, and
nothing here was adopted.

### §58 addendum — mvrv_cycle disabled by OWNER OVERRIDE; the ladder rerun on the new configuration

**Appended 2026-08-21, same day as §58. Claim class: GOVERNANCE + CONTROL
rerun. K unchanged: 66.**

#### The decision, recorded precisely

The owner disabled `mvrv_cycle` after reading §58's diagnostic. The record must
be exact about what this is and is not:

* **No §51 kill criterion fired.** K1 (alpha ≤ −25pp at a monthly review): the
  first review is 2026-09-14 and has not happened. K2 (stale data): the series
  is fresh. K3 (replay divergence): none. K4 (missed reviews): none missed.
* **The §58 evidence is inconclusive by this log's own standard.** The
  ensemble-vs-xsmom difference is −$302/trade with CI [−$1,805, +$1,428] — it
  includes zero.
* **This is therefore an owner override on inconclusive evidence, taken
  deliberately, not a kill.** Writing it up as a kill would corrupt the
  meaning of K1–K4 for every future experiment: a criterion that can be
  "fired" retroactively by whatever evidence arrives is not a pre-registered
  criterion. The tempting move — amending §51 to add a fifth,
  ensemble-interaction criterion and then firing it — was considered and
  refused for exactly that reason.

The basis, restated: §58 found the pairing ran **8.75pp worse than xsmom
alone** while `mvrv_cycle` alone was flat (0.00%, PF 1.00, n=3). Neither
component loses; the pairing does — the §54 collision shape, a long-or-flat
BTC holder occupying a slot the cross-sectional strategy would deploy.

#### The open BTC position stays

Disablement stops **new** entries. The ownership rule keeps a disabled
strategy's exit logic running, `mvrv_cycle`'s stop is live, and its NUPL ≥ 0.67
exit may be months away. The owner chose to let the position resolve on its own
rule rather than force a discretionary close. **Flagged for the 2026-09-14
review: a disabled experiment still holds capital.** The experiment's forward
record (currently: one open trade, zero closed) remains a §51 review input.

#### The ladder, rerun on what now ships

Same snapshots (sha-verified), same five salts, same pass mark, judge off.
Arm (i) is now read from config at run time — the hardcoded pairing in the
runner went stale the moment the config changed, and a ladder that measures a
configuration that no longer ships would be §43's dashboard bug wearing a lab
coat. The original §58 pairing stays reproducible from git history.

```
  arm                       ret%      PF   maxDD%     n     costx
  i.  full agent (xsmom)    2.95    1.14    16.39    31      3.24
  ii. random entry        -13.20       —        —    17         —   [-18.73 .. -3.43] over 5 salts
  iii.SMA cross           -22.27    0.04    22.27    34    -17.37
  iv. buy and hold         -4.64       —        —    21         —
  v.  rails only          -13.57    0.32    51.45    23    -12.69
```

**RESULT: FAIL, again — and the texture matters.** What changed: arm (i) is
now positive, beats every other arm's point estimate, and sits **outside** the
five-salt null band ([−18.73, −3.43]) instead of inside it. The configuration
change did exactly what §58's diagnostic predicted. What did not change: every
bootstrap comparison is still **INCONCLUSIVE** at K=66 — vs random entry
+$923/trade with CI [−$245, +$2,094]; vs buy-and-hold +$316/trade with CI
[−$8,312, +$4,123]. **n=31 trades cannot clear a Bonferroni-corrected bar at
K=66, and no rearrangement of this sample will.** The distinction between "the
point estimate improved" and "there is evidence" is the entire discipline of
this log, and this rerun sits squarely on the wrong side of it.

The honest summary of the configuration change: it removed a measured drag. It
did not create a measured edge.

**66 trials, zero adopted, zero closed trades.** An override is not a trial; a
control spends no budget; nothing was adopted.

### §58 addendum — the external dead-man's switch is live, and was tested by stopping the heartbeat

**2026-08-22. INFRA. K unchanged: 66.** The audit's worst operational finding
was that every liveness check ran on the host that would be broken. Closed:
two healthchecks.io checks (`repete1-cycle` 1 d / 6 h grace,
`repete1-live` 5 min / 10 min grace) with an email integration to the owner,
URLs set on the Bizon via `scripts/set_heartbeat_urls.sh`.

"Configured" and "proven" are different claims — §56's lesson applied to
monitoring — so it was proven: `systemctl --user stop repete1`, eighteen
minutes of genuine silence (zero repete1 processes, verified by cwd),
`repete1-live` went DOWN on its own and the email was delivered; restart,
recovery ping, UP notice delivered. A deliberate `/fail` on the cycle check
delivered a third. Also observed in production during the test: the watchdog
logged *"catch-up: live loop is running — no action"* — the §56 second-writer
guard doing its job on the live host.

Open, found during the test: `venue.downtime_seconds()` dates from the last
venue *event*, so the startup sweep reported 20 h for an 18 min stop.
Conservative direction; not fixed here.

### §58 addendum — Milestone 0 closed (2026-08-22). INFRA. K unchanged: 66.

The audit's engineering fix list is done. What each item turned out to be:

* **Type checking found two live bugs no test had reached.** `live.py` called
  `alerting.notify(...)`, which never existed, in both alert paths — one would
  have crashed startup after unattended stops fired, the other would have
  killed the live loop on its first failed decision cycle. And `review.py`'s
  verdict branch referenced `spy`, renamed to `bench` in §23: a NameError
  waiting for the 30th closed trade. ruff and mypy are now blocking in CI;
  106 type errors to zero, thirty of them hidden behind one dataclass typed
  as `object`.
* **The restart sweep was re-litigating two days of wicks.** Its "downtime"
  clock dated from the venue's last *fill*, and the bar window was a fixed
  48 h regardless — so a restart could fire a still-resting stop on a wick
  the live 60 s poll had legitimately cleared. The gap is now the liveness
  heartbeat's age and the window is sized to it. Verified on the box: two
  restarts, no sweep, where every earlier restart logged `downtime of 73293s`.
* **`synthetic_half_spread_bps` was never backtest-only.** It prices every
  live protective exit, correctly — a stop fills at a level, and a level has
  no book. Three docs said otherwise; the docs were wrong. Pinned by a test
  that moves the knob and watches the live stop fill move.
* **A hashed lock, constrained to what production runs.** The first
  unconstrained compile drifted `ccxt` one patch ahead of the box; a lock
  that pins a different environment from production is decoration. The
  cross-version proof then found that **CI (3.11) could not install
  production's numpy 2.5.2 at all** — CI had been testing a different numpy
  from the one the bot trades on, the "CI measures the laptop" lesson one
  level up. CI, the Dockerfile and the laptop dev venv are 3.12 now. One
  Python, one lock, everywhere; `pip-audit` blocks.
* **Two items closed on evidence, no code:** the order-book coverage alert
  has zero occurrences on the Bizon (104.8% coverage — it was a laptop
  symptom), and the "backups empty" alert fired only before the first
  nightly archive. Flagged for a decision, not acted on: **Bizon backups are
  local-only.**
* **Gate 1 of the audit closed structurally**: nothing on the simulation
  path can import a model, pinned statically and at runtime.

Also caught, by running the suite on the box rather than trusting the
laptop: a test written this morning read the real `state/heartbeat_live`
and gave opposite verdicts on the two machines. Now owns its state.

**66 trials, zero adopted, zero closed trades.** Infrastructure is not a
trial.

### §58 addendum — Milestone 1: extraction map, and the hygiene it demanded

**Appended 2026-08-22. Claim class: INFRA + METHOD. K unchanged: 66.**
Nothing measured, nothing adopted; no number moved (golden byte-identical).

The owner chose to sell the methodology, not the strategies. Milestone 1 was
a read-only coupling audit of what "the methodology" is in this repo —
`docs/methodology_extraction_map.md`, committed `14672cc`. Decisions taken
on it: a **separate, public** package; a **toy** second worked example (no
bars at all), so the domain-neutral claim is tested rather than asserted.

Two findings belong in this log rather than only in the doc:

1. **Bonferroni K is hand-copied.** `knowledge/gate_verdicts.json` feeds the
   dashboard and nothing else; every gate script carries its own `TRIALS`
   literal, under three different conventions, and no test pins any of them
   to the tally line. The record is correct — this section's 66 is right —
   but it is correct because a human kept it so. The package's first job is
   to make that arithmetic.
2. **The log's own grammar is enforced by prose.** Claim class, `K: n → m`,
   "committed BEFORE", controls-spend-nothing, prediction-scored: none of it
   is machine-checked. One byte-sentinel guards append-only. A linter for
   this template is the package's second job, and its first run will be
   against this file.

Pre-move hygiene done now, all behaviour-neutral:

* `significance.bootstrap_mean_ci` is public; `edge_report` no longer reaches
  into a private name across what is about to become a package boundary.
* `gate_ablation` no longer reads `config.yaml` at import time; arm (i) is
  read inside `main()`. `pass_mark()` extracted. `gate_compare.select_winner`
  extracted so the IS-only selection rule is a function, not a line in main.
* **25 tests** for the three most portable units that had none
  (`tests/test_gate_script_helpers.py`), including that `INCONCLUSIVE` can
  never round up to a pass.
* The doc-citation check now reads **source files**, not just markdown. It
  found **eleven** files naming tests that do not exist — not the four the
  audit saw in `fills.py`. Two were covering for tests that had never been
  written (`round_price` conservatism; the page's enabled-strategy prose) —
  both now exist. Deliberate absences (`src/broker.py`) are allowlisted with
  reasons, the same convention as strikethrough in markdown.
* CI now re-hashes the gate snapshot every run (`build_crypto_snapshot.py
  --verify`); before, only symbol sets and bar counts were compared.
* Three vestigial `sys.path` inserts removed from scripts that import nothing
  from `src/`, so their zero-coupling is visible rather than accidental.

Deliberately **not** done: pruning `modelver._FINGERPRINT_FILES` of the two
modules deleted at the fork. Doing so changes `model_version` on every new
ledger record with no change to the decision surface — a spurious segment
boundary in the live track record. Left for the package, where the file
list is injected.

**66 trials, zero adopted, zero closed trades.** Infrastructure is not a
trial; a map is not a measurement.
