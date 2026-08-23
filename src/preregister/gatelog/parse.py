"""Parse a gate log into sections, parts, class declarations, K statements
and tally lines. No judgement here — `lint.py` judges."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from preregister.gatelog import grammar as g


@dataclass(frozen=True)
class Tally:
    k: int
    adopted: int
    line: int
    strict_form: bool


@dataclass(frozen=True)
class KDeclaration:
    kind: str                 # transition | delta | absolute | unchanged | unchanged_bare
    before: int | None
    after: int | None
    delta: int | None
    line: int


@dataclass(frozen=True)
class Part:
    kind: str                 # registration | result | status | addendum | tally | note | other
    heading: str
    line: int


@dataclass
class Section:
    number: int
    suffix: str
    era: str                  # "A" | "B"
    title: str
    start: int                # 1-based line of the first heading
    end: int                  # exclusive
    heading_class: str | None = None
    classes: tuple[str, ...] = ()
    unknown_classes: tuple[str, ...] = ()
    parts: list[Part] = field(default_factory=list)
    tallies: list[Tally] = field(default_factory=list)
    k_decls: list[KDeclaration] = field(default_factory=list)
    committed_before: bool = False
    has_kill: bool = False
    resolved: bool = False
    deviation_lines: tuple[int, ...] = ()
    text: str = ""

    @property
    def ref(self) -> str:
        return f"§{self.number}{self.suffix}"

    @property
    def spends(self) -> bool:
        return any(c in g.SPENDING for c in self.classes)


@dataclass
class Log:
    preamble: str
    sections: list[Section]
    n_lines: int


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _classes_in(body: str, heading_title: str, era: str) -> tuple[str | None, list[str]]:
    """(class phrase from the heading if any, all declared class tokens)."""
    found: list[str] = []
    heading_cls: str | None = None
    m = g.H2_CLASS.match(heading_title)
    if m and era == "B":
        heading_cls = m.group("cls").strip()
    elif era == "A":
        # Era A occasionally leads the title with a class word ("MEASUREMENT, no verdict").
        first = re.match(r"([A-Z][A-Z\- ]+?)[,.:]", heading_title)
        if first and g.normalise_classes(first.group(1))[0] in g.CLASSES:
            heading_cls = first.group(1)
    phrases: list[str] = []
    for pat in (g.CLAIM_CLASS, g.TYPE_LINE, g.BARE_CLASS):
        phrases += [m.group("cls") for m in pat.finditer(body)]
    phrases += [m.group("cls") for m in g.CLAIM_TYPE.finditer(body)]
    phrases += [m.group("cls") for m in g.ADDENDUM_CLASS.finditer(body)]
    if heading_cls:
        phrases.insert(0, heading_cls)
    for p in phrases:
        for c in g.normalise_classes(p):
            if c not in found:
                found.append(c)
    if not found and era == "A" and "PRE-REGISTRATION" in heading_title.upper():
        found.append("EDGE")   # the era-A convention: a pre-registration IS an edge claim
    return heading_cls, found


def _k_decls(body: str, offset_line: int) -> list[KDeclaration]:
    out: list[KDeclaration] = []
    for m in g.K_TRANSITION.finditer(body):
        out.append(KDeclaration("transition", int(m["before"]), int(m["after"]), None,
                                offset_line + _line_of(body, m.start()) - 1))
    for m in g.K_DELTA_PLAIN.finditer(body):
        out.append(KDeclaration("delta", None, int(m["after"]), int(m["d"]),
                                offset_line + _line_of(body, m.start()) - 1))
    for m in g.K_DELTA_WITH_AFTER.finditer(body):
        after = m["after"] or m["after2"]
        out.append(KDeclaration("delta", None, int(after), int(m["d"]),
                                offset_line + _line_of(body, m.start()) - 1))
    delta_lines = {d.line for d in out}
    for m in g.K_DELTA_BARE.finditer(body):
        line = offset_line + _line_of(body, m.start()) - 1
        if line not in delta_lines:
            out.append(KDeclaration("delta", None, None, int(m["d"]), line))
            delta_lines.add(line)
    for m in g.K_ABSOLUTE.finditer(body):
        line = offset_line + _line_of(body, m.start()) - 1
        if line in delta_lines:
            continue
        out.append(KDeclaration("absolute", None, int(m["k"] or m["k2"]), None, line))
    for m in g.K_UNCHANGED.finditer(body):
        out.append(KDeclaration("unchanged", None, int(m["k"]), 0,
                                offset_line + _line_of(body, m.start()) - 1))
    for m in g.K_UNCHANGED_BARE.finditer(body):
        out.append(KDeclaration("unchanged_bare", None, None, 0,
                                offset_line + _line_of(body, m.start()) - 1))
    return sorted(out, key=lambda d: d.line)


def _tallies(body: str, offset_line: int) -> list[Tally]:
    out: list[Tally] = []
    seen: set[int] = set()
    for m in g.TALLY_STRICT.finditer(body):
        line = offset_line + _line_of(body, m.start()) - 1
        seen.add(line)
        a = m["adopted"]
        out.append(Tally(int(m["k"]), 0 if a == "zero" else int(a), line, True))
    for m in g.TALLY_LOOSE.finditer(body):
        line = offset_line + _line_of(body, m.start()) - 1
        if line in seen:
            continue
        a = m["adopted"].lower()
        out.append(Tally(int(m["k"]), 0 if a == "zero" else int(a), line, False))
    return sorted(out, key=lambda t: t.line)


def parse(text: str) -> Log:
    lines = text.split("\n")
    heads = list(g.H2.finditer(text))
    if not heads:
        return Log(text, [], len(lines))
    preamble = text[:heads[0].start()]

    # Group consecutive H2s by (number, suffix): `## §14` + `## §14 RESULT` are one section.
    raw: list[tuple[int, str, list[tuple[int, str, str | None]]]] = []
    for m in heads:
        n, sfx = int(m["n"]), m["sfx"] or ""
        entry = (_line_of(text, m.start()), m["title"], m["part"])
        if raw and raw[-1][0] == n and raw[-1][1] == sfx:
            raw[-1][2].append(entry)
        else:
            raw.append((n, sfx, [entry]))

    era_b_from: int | None = None
    for n, _sfx, entries in raw:
        hm = g.H2_CLASS.match(entries[0][1])
        if hm and era_b_from is None and g.normalise_classes(hm["cls"])[0] in g.CLASSES:
            era_b_from = n     # the first heading that LEADS with a known class

    sections: list[Section] = []
    for idx, (n, sfx, entries) in enumerate(raw):
        start = entries[0][0]
        end = raw[idx + 1][2][0][0] if idx + 1 < len(raw) else len(lines) + 1
        body = "\n".join(lines[start - 1:end - 1])
        era = "B" if era_b_from is not None and n >= era_b_from else "A"
        title = entries[0][1]
        heading_cls, classes = _classes_in(body, title, era)
        known = tuple(c for c in classes if c in g.CLASSES)
        unknown = tuple(c for c in classes if c not in g.CLASSES)
        sec = Section(n, sfx, era, title, start, end, heading_cls, known, unknown, text=body)
        for line, _t, part in entries:
            kind = {"RESULT": "result", "RESULTS": "result", "STATUS": "status"}.get(part or "", "registration")
            sec.parts.append(Part(kind, lines[line - 1], line))
        for m in g.H3_PART.finditer(body):
            line = start + _line_of(body, m.start()) - 1
            p = (m["part"] or "").lower()
            kind = {"result": "result", "results": "result", "status": "status",
                    "addendum": "addendum", "tally": "tally",
                    "implementation note": "note"}.get(p, "other")
            sec.parts.append(Part(kind, lines[line - 1], line))
        sec.parts.sort(key=lambda p: p.line)
        sec.tallies = _tallies(body, start)
        sec.k_decls = _k_decls(body, start)
        sec.committed_before = bool(g.COMMITTED_BEFORE.search(body))
        sec.has_kill = bool(g.KILL.search(body))
        sec.resolved = (any(p.kind in ("result", "status", "addendum") for p in sec.parts)
                        or bool(sec.tallies) or bool(g.RESOLVED.search(body)))
        sec.deviation_lines = tuple(start + _line_of(body, m.start()) - 1
                                    for m in g.DEVIATION.finditer(body))
        sections.append(sec)
    return Log(preamble, sections, len(lines))


def final_k(log: Log) -> int | None:
    """The last tally's K — strict form preferred, to stay byte-compatible
    with the source repo's own consumer. None when no tally exists."""
    strict = [t for s in log.sections for t in s.tallies if t.strict_form]
    loose = [t for s in log.sections for t in s.tallies]
    pool = strict or loose
    return pool[-1].k if pool else None
