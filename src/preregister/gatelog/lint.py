"""The rules. Each is a function over the parsed log that yields Findings;
every rule has a positive and a negative-control fixture in the tests, and
a meta-test fails if a rule is registered without one.

Levels: "error" fails the run; "warning" fails only under `--strict`;
"info" never fails and is never suppressed — the point of an info finding
(a self-reported deviation, a tally in a form the consumer's regex cannot
read) is that a reader sees it.

Era A (the source log's first 48 sections) predates the grammar. Its
findings are warnings where era B's are errors; `--strict` promotes them,
which is what a NEW log is held to.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass

from preregister.gatelog import grammar as g
from preregister.gatelog.lock import AppendOnlyLock
from preregister.gatelog.parse import Log, Section, parse

ERROR, WARNING, INFO = "error", "warning", "info"


@dataclass(frozen=True, order=True)
class Finding:
    line: int
    rule: str
    level: str
    section: str
    message: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class _State:
    k: int
    strict: bool
    lock: AppendOnlyLock | None
    registry_adopted: int | None
    k_in: dict[str, int]
    k_out: dict[str, int]


Rule = Callable[[Log, _State], Iterator[Finding]]
RULES: dict[str, Rule] = {}


def _rule(name: str) -> Callable[[Rule], Rule]:
    def deco(fn: Rule) -> Rule:
        RULES[name] = fn
        return fn
    return deco


def _era_level(sec: Section, strict: bool) -> str:
    return ERROR if (sec.era == "B" or strict) else WARNING


# ---- R01 / R02: structure --------------------------------------------------------

@_rule("R01")
def unparseable_headings(log: Log, st: _State) -> Iterator[Finding]:
    """An H2 that starts `## §` but does not match either heading grammar."""
    seen = {p.line for s in log.sections for p in s.parts}
    for i, line in enumerate(_TEXT[0].split("\n"), start=1):
        if line.startswith("## §") and i not in seen:
            yield Finding(i, "R01", ERROR, "-", f"unparseable section heading: {line!r}")


@_rule("R02")
def numbering(log: Log, st: _State) -> Iterator[Finding]:
    prev = 0
    for s in log.sections:
        if s.number < prev:
            yield Finding(s.start, "R02", ERROR, s.ref, f"section numbers go backwards ({prev} -> {s.number})")
        elif s.number > prev + 1 and prev:
            yield Finding(s.start, "R02", WARNING, s.ref,
                          f"numbering gap: §{prev + 1}..§{s.number - 1} never written")
        prev = max(prev, s.number)


# ---- R03 / R04: claim class ----------------------------------------------------------

@_rule("R03")
def class_present(log: Log, st: _State) -> Iterator[Finding]:
    for s in log.sections:
        if not s.classes and not s.unknown_classes:
            yield Finding(s.start, "R03", _era_level(s, st.strict), s.ref,
                          "no claim class declared (heading or `Claim class:` line)")


@_rule("R04")
def class_in_enum(log: Log, st: _State) -> Iterator[Finding]:
    for s in log.sections:
        for u in s.unknown_classes:
            level = WARNING if s.classes else ERROR
            yield Finding(s.start, "R04", level, s.ref,
                          f"claim class {u!r} is not in the enum "
                          f"{sorted(g.CLASSES)}" + (f"; body declares {s.classes}" if s.classes else ""))


# ---- R05 / R06 / R07: K accounting ---------------------------------------------------
#
# Computed once, in section order, by `_account()`; the three rules read the
# result. K never decreases. A section's K-out is derived from its FIRST
# declaration; later declarations must agree with it (restatements are
# normal — a registration and its result both say "K: 65 -> 66").

def _account(log: Log, st: _State) -> list[Finding]:
    out: list[Finding] = []
    k = st.k
    for s in log.sections:
        st.k_in[s.ref] = k
        k_out = k
        first = True
        for d in s.k_decls:
            if first:
                first = False
                if d.kind == "transition":
                    assert d.before is not None and d.after is not None
                    if d.before != k:
                        out.append(Finding(d.line, "R05", ERROR, s.ref,
                                           f"K declared as {d.before} -> {d.after} but the running count is {k}"))
                    k_out = d.after
                elif d.kind == "delta":
                    assert d.delta is not None
                    if d.after is not None and k + d.delta != d.after:
                        level = _era_level(s, st.strict)
                        out.append(Finding(d.line, "R05", level, s.ref,
                                           f"+{d.delta} from {k} is {k + d.delta}, not {d.after} as declared"))
                        k_out = d.after      # trust the stated total; the gap is the finding
                    else:
                        k_out = k + d.delta
                elif d.kind == "absolute":
                    assert d.after is not None
                    if d.after < k:
                        out.append(Finding(d.line, "R05", ERROR, s.ref,
                                           f"K stated as {d.after} but it was already {k}; K never decreases"))
                    elif d.after != k:
                        level = INFO if s.era == "A" and not st.strict else ERROR
                        out.append(Finding(d.line, "R05", level, s.ref,
                                           f"K resynchronised to {d.after} (+{d.after - k}) without declared arms"))
                    k_out = d.after
                else:  # unchanged / unchanged_bare
                    if d.after is not None and d.after != k:
                        out.append(Finding(d.line, "R05", ERROR, s.ref,
                                           f"declares K unchanged at {d.after} but the running count is {k}"))
                    k_out = k
            else:
                stated = d.after
                if d.kind == "delta" and stated is None:
                    if d.delta != (k_out - k):
                        out.append(Finding(d.line, "R05", WARNING, s.ref,
                                           f"a later +{d.delta} does not restate this section's spend (+{k_out - k})"))
                elif stated is not None and stated not in (k, k_out):
                    out.append(Finding(d.line, "R05", ERROR, s.ref,
                                       f"restates K as {stated}; this section runs {k} -> {k_out}"))
        # R06: spending vs class
        if s.spends and k_out == k:
            out.append(Finding(s.start, "R06", _era_level(s, st.strict), s.ref,
                               f"class {s.classes} spends budget but K did not move from {k}"))
        if not s.spends and (s.classes or s.unknown_classes) and k_out != k:
            out.append(Finding(s.start, "R06", ERROR, s.ref,
                               f"class {s.classes or s.unknown_classes} spends nothing but K moved {k} -> {k_out}"))
        if not s.classes and not s.unknown_classes and k_out != k:
            out.append(Finding(s.start, "R06", _era_level(s, st.strict), s.ref,
                               f"K moved {k} -> {k_out} in a section with no claim class"))
        # R07: tallies
        for t in s.tallies:
            if t.k not in (k, k_out):
                out.append(Finding(t.line, "R07", ERROR, s.ref,
                                   f"tally says {t.k} trials; this section runs {k} -> {k_out}"))
        st.k_out[s.ref] = k_out
        k = k_out
    return out


@_rule("R05")
def k_arithmetic(log: Log, st: _State) -> Iterator[Finding]:
    yield from (f for f in _account(log, st) if f.rule == "R05")


@_rule("R06")
def spending_matches_class(log: Log, st: _State) -> Iterator[Finding]:
    yield from (f for f in _account(log, st) if f.rule == "R06")


@_rule("R07")
def tally_matches_k(log: Log, st: _State) -> Iterator[Finding]:
    yield from (f for f in _account(log, st) if f.rule == "R07")


# ---- R08 .. R14 ---------------------------------------------------------------------

@_rule("R08")
def tally_form(log: Log, st: _State) -> Iterator[Finding]:
    for s in log.sections:
        for t in s.tallies:
            if not t.strict_form:
                yield Finding(t.line, "R08", WARNING if st.strict else INFO, s.ref,
                              "tally is not in the `**N trials, zero adopted` form the consumer regex reads")


@_rule("R09")
def committed_before(log: Log, st: _State) -> Iterator[Finding]:
    for s in log.sections:
        if s.spends and not s.committed_before:
            yield Finding(s.start, "R09", _era_level(s, st.strict), s.ref,
                          "spends budget but never says it was committed BEFORE the run")


@_rule("R10")
def experiment_has_kill(log: Log, st: _State) -> Iterator[Finding]:
    for s in log.sections:
        if "EXPERIMENT" in s.classes and not s.has_kill:
            yield Finding(s.start, "R10", ERROR, s.ref,
                          "an EXPERIMENT must state kill criteria (the word 'kill' is absent)")


@_rule("R11")
def spending_section_resolved(log: Log, st: _State) -> Iterator[Finding]:
    for s in log.sections:
        if s.spends and not s.resolved:
            yield Finding(s.start, "R11", WARNING, s.ref,
                          "spends budget but has no RESULT, STATUS, addendum, tally or verdict")


@_rule("R12")
def append_only(log: Log, st: _State) -> Iterator[Finding]:
    if st.lock is None:
        yield Finding(1, "R12", WARNING, "-", "no append-only lock supplied; history is unverified")
        return
    msg = st.lock.check(_TEXT[0])
    if msg:
        yield Finding(1, "R12", ERROR, "-", msg)


@_rule("R13")
def self_reported_deviation(log: Log, st: _State) -> Iterator[Finding]:
    for s in log.sections:
        for line in s.deviation_lines:
            yield Finding(line, "R13", INFO, s.ref,
                          "self-reported protocol deviation (recorded, never suppressed)")


@_rule("R14")
def adopted_matches_registry(log: Log, st: _State) -> Iterator[Finding]:
    if st.registry_adopted is None:
        return
    for s in log.sections:
        for t in s.tallies:
            if t.adopted != st.registry_adopted:
                yield Finding(t.line, "R14", ERROR, s.ref,
                              f"tally says {t.adopted} adopted; registry says {st.registry_adopted}")


_TEXT: list[str] = [""]   # the raw text, for R12; set by lint()


def lint(text: str, *, strict: bool = False, k0: int = 0, lock: AppendOnlyLock | None = None,
         registry_adopted: int | None = None) -> list[Finding]:
    _TEXT[0] = text
    log = parse(text)
    st = _State(k0, strict, lock, registry_adopted, {}, {})
    found: list[Finding] = []
    accounted = False
    for name, rule in RULES.items():
        if name in ("R05", "R06", "R07"):
            if not accounted:
                found.extend(_account(log, st))
                accounted = True
            continue
        found.extend(rule(log, st))
    return sorted(set(found))


def fails(findings: list[Finding], *, strict: bool = False) -> bool:
    bad = {ERROR, WARNING} if strict else {ERROR}
    return any(f.level in bad for f in findings)
