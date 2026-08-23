"""The regular grammar of a gate log. Nothing else lives here.

Every pattern was fitted to the source bot's real log, which has two eras:

  A (§1–§48)  `## §N — title`, class in a body line `**Type: X**` or
              `**CLAIM TYPE: EDGE**` or `**INFRA (date). K stays N**`.
  B (§49+)    `## §N — CLASS: title`, class restated as `**Claim class: X**`.

A new log written against this package uses era B and `--strict`.
"""
from __future__ import annotations

import re

SPENDING: frozenset[str] = frozenset({"EDGE", "CAPACITY", "GATE"})
NON_SPENDING: frozenset[str] = frozenset({
    "CONTROL", "INFRA", "GOVERNANCE", "METHOD", "DIAGNOSTIC", "MEASUREMENT",
    "INTAKE", "EXPERIMENT", "COMPONENT", "DATA COLLECTION"})
CLASSES: frozenset[str] = SPENDING | NON_SPENDING

#: Phrases that mean a class, normalised before the enum check.
ALIASES: dict[str, str] = {
    "RESEARCH INTAKE": "INTAKE",
    "INFRA CLOSE-OUT": "INFRA",
    "SOURCE REVIEW": "INTAKE",
    "DATA COLLECTION": "DATA COLLECTION",
}

# ---- headings ----------------------------------------------------------------
H2 = re.compile(r"^## §(?P<n>\d+)(?P<sfx>[a-z]?)(?: (?P<part>RESULTS?|STATUS))? — (?P<title>.+?)\s*$",
                re.MULTILINE)
#: Era B: the class leads the title. `EDGE pre-registration:` and
#: `EDGE (…) + EXPERIMENT registration:` both count.
H2_CLASS = re.compile(r"^(?P<cls>[A-Z][A-Z\-]*(?: \([^)]*\))?(?: \+ [A-Z][A-Z\-]*(?: \([^)]*\))?)*)(?: pre-registration| registration)?:\s")
H3_PART = re.compile(r"^### §(?P<n>\d+)(?P<sfx>[a-z]?)(?:'s)? ?(?P<part>RESULTS?|STATUS|addendum|tally|implementation note)?\b",
                     re.MULTILINE)
ANY_HEADING = re.compile(r"^#{2,3} ", re.MULTILINE)

# ---- class declarations in the body ----------------------------------------
CLAIM_CLASS = re.compile(r"\bClaim class: (?P<cls>[^*]+?)(?:\.\*\*|\*\*|\. )", re.S)
TYPE_LINE = re.compile(r"^\*\*Type: (?P<cls>[^*]+?)(?:\.\*\*|\*\*|\.)", re.MULTILINE)
CLAIM_TYPE = re.compile(r"\bCLAIM TYPE: (?P<cls>EDGE|CAPACITY)\b")
BARE_CLASS = re.compile(r"^\*\*(?P<cls>INFRA CLOSE-OUT|RESEARCH INTAKE|INFRA|MEASUREMENT|GOVERNANCE|CONTROL|METHOD)\b[^*\n]*?K (?:stays|unchanged)",
                        re.MULTILINE)
ADDENDUM_CLASS = re.compile(r"^(?:### §\d+ addendum —[^\n]*?|\*\*[^*\n]*?)\b(?P<cls>INFRA|METHOD|GOVERNANCE|CONTROL|MEASUREMENT|DIAGNOSTIC)\b[^\n]*?K unchanged",
                            re.MULTILINE)

# ---- K statements --------------------------------------------------------------
K_TRANSITION = re.compile(r"\bK: (?P<before>\d+) → (?P<after>\d+)")
#: "+3 trials → K = 58", "+3 trials. Cumulative K after this run: 51", "**+3. Cumulative K: 54**"
K_DELTA_WITH_AFTER = re.compile(r"\+(?P<d>\d+)(?: trials?)?\b[^*\n]*?(?:→ K = (?P<after>\d+)|Cumulative K(?: after this run)?:? (?P<after2>\d+))")
#: "+3 trials" on its own (the total is stated elsewhere or nowhere)
K_DELTA_BARE = re.compile(r"\+(?P<d>\d+) trials?\b")
K_DELTA_PLAIN = re.compile(r"\*\*(?P<d>\d+) trials?\.\s*Cumulative K(?: after this run)?:? (?P<after>\d+)")
K_ABSOLUTE = re.compile(r"\bCumulative K(?: after this run)?:? (?P<k>\d+)|\bK becomes (?P<k2>\d+)")
K_UNCHANGED = re.compile(r"\b(?:K (?:unchanged|stays)(?: at)?:? |Trial count unchanged at )(?P<k>\d+)")
K_UNCHANGED_BARE = re.compile(r"\bK unchanged\b(?![ :]*(?:at )?\d)|\bno K\b|\bTrial count unchanged\b(?! at)")

# ---- tallies -----------------------------------------------------------------
#: What the source repo's own consumer reads (tests/test_gate_verdicts.py).
TALLY_STRICT = re.compile(r"\*\*(?P<k>\d+) trials, (?P<adopted>zero|\d+) adopted")
TALLY_LOOSE = re.compile(r"(?<![\d.])(?P<k>\d+) (?:registered )?trials[,.] (?P<adopted>zero|\d+) adopted",
                         re.IGNORECASE)

# ---- discipline phrases ----------------------------------------------------------
COMMITTED_BEFORE = re.compile(r"\b(?:committed BEFORE|pre-registered|PRE-REGISTRATION|written before the|declared before the)\b",
                              re.IGNORECASE)
DEVIATION = re.compile(r"\b(?:transcribed into this log AFTER|deviation to disclose|[Dd]eviations?, recorded)\b")
KILL = re.compile(r"\bkill\b", re.IGNORECASE)
RESOLVED = re.compile(r"\b(?:RESULT|VERDICT|Verdict:|REJECT|ADOPTED|FAIL\b|PASS\b|HALTED)")


def normalise_classes(phrase: str) -> list[str]:
    """'GATE (re-run of §4) + EDGE claim' -> ['GATE', 'EDGE'];
    'INFRA CLOSE-OUT' -> ['INFRA']. Unknown tokens are returned verbatim so
    the linter can name them."""
    text = phrase.upper()
    for alias, canon in ALIASES.items():
        text = text.replace(alias, canon)
    text = re.sub(r"\([^)]*\)", " ", text)
    out: list[str] = []
    first_word: str | None = None
    for chunk in re.split(r"\s*\+\s*|\s*,\s*", text):
        chunk = chunk.strip()
        if chunk.startswith(("NOT ", "NO ", "NOTHING", "NEVER")):
            continue   # "MEASUREMENT, not a gate" declares MEASUREMENT, not GATE
        words = re.findall(r"[A-Z][A-Z\-]+", chunk)
        if not words:
            continue
        first_word = first_word or words[0]
        if "DATA COLLECTION" in chunk:
            out.append("DATA COLLECTION")
            continue
        out.extend(w for w in words if w in CLASSES and w not in out)
    if not out and first_word:
        out.append(first_word)    # unknown, returned so the linter can name it
    return out
