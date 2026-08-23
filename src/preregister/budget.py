"""The K ledger: where the multiple-comparison budget lives.

In the source bot, K was a hand-copied integer in fifteen scripts under
three different conventions, and the only machine check was that a summary
JSON restated the log's last tally line. It was correct — because a person
kept it correct. This is that arithmetic as an object.

Rules, as the bot's log states them in prose:

  * EDGE, CAPACITY and GATE claims SPEND budget: K rises by the number of
    arms declared, and the declaration must say what it was committed
    before (a commit sha, an artefact name — something a reader can check).
  * Everything else — CONTROL, INFRA, GOVERNANCE, METHOD, DIAGNOSTIC,
    MEASUREMENT, INTAKE, EXPERIMENT — spends nothing. "Null arms are
    instruments, not candidates." "An override is not a trial."
  * Adoption is counted separately. A PASS that is not adopted is a PASS.

The JSON form is a superset of the bot's `gate_verdicts.json`: that file
loads unchanged (`schema` and `ledger` are optional), and unknown keys
round-trip untouched so the consumer's own fields survive a save.
"""
from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

SPENDING: frozenset[str] = frozenset({"EDGE", "CAPACITY", "GATE"})
NON_SPENDING: frozenset[str] = frozenset({
    "CONTROL", "INFRA", "GOVERNANCE", "METHOD", "DIAGNOSTIC", "MEASUREMENT",
    "INTAKE", "EXPERIMENT", "COMPONENT", "DATA COLLECTION"})
CLASSES: frozenset[str] = SPENDING | NON_SPENDING
SCHEMA = "preregister.registry/1"


class BudgetError(ValueError):
    pass


@dataclass(frozen=True)
class Entry:
    section: str
    cls: str
    arms: int
    k_before: int
    k_after: int
    committed_before: str | None = None
    note: str = ""


@dataclass
class Registry:
    trials_registered: int = 0
    strategies_adopted: int = 0
    ledger: list[Entry] = field(default_factory=list)
    updated: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    # ---- the KSource protocol ------------------------------------------
    def k(self) -> int:
        return self.trials_registered

    def alpha(self, nominal: float = 0.05) -> float:
        return nominal / max(1, self.trials_registered)

    # ---- accounting ------------------------------------------------------
    def spend(self, section: str, n_arms: int, *, cls: str = "EDGE",
              committed_before: str, note: str = "") -> Entry:
        cls = cls.upper()
        if cls not in SPENDING:
            raise BudgetError(f"{cls!r} does not spend budget; use control()")
        if n_arms < 1:
            raise BudgetError("a spending section declares at least one arm")
        if not committed_before.strip():
            raise BudgetError("a spending section must say what it was committed BEFORE")
        e = Entry(section, cls, n_arms, self.trials_registered,
                  self.trials_registered + n_arms, committed_before, note)
        self.trials_registered = e.k_after
        self.ledger.append(e)
        return e

    def control(self, section: str, *, cls: str = "CONTROL", note: str = "") -> Entry:
        cls = cls.upper()
        if cls in SPENDING:
            raise BudgetError(f"{cls!r} spends budget; use spend()")
        if cls not in NON_SPENDING:
            raise BudgetError(f"unknown claim class {cls!r}")
        e = Entry(section, cls, 0, self.trials_registered, self.trials_registered, None, note)
        self.ledger.append(e)
        return e

    def adopt(self, section: str, name: str) -> None:
        self.strategies_adopted += 1
        self.ledger.append(Entry(section, "ADOPT", 0, self.trials_registered,
                                 self.trials_registered, None, name))

    # ---- persistence -----------------------------------------------------
    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> Registry:
        known = {"schema", "updated", "trials_registered", "strategies_adopted", "ledger"}
        ledger = [Entry(**{k: v for k, v in row.items() if k in Entry.__dataclass_fields__})
                  for row in d.get("ledger", [])]
        reg = cls(trials_registered=int(d.get("trials_registered", 0)),
                  strategies_adopted=int(d.get("strategies_adopted", 0)),
                  ledger=ledger, updated=str(d.get("updated", "")),
                  extra={k: v for k, v in d.items() if k not in known})
        if ledger and ledger[-1].k_after != reg.trials_registered:
            raise BudgetError(
                f"ledger ends at K={ledger[-1].k_after} but trials_registered="
                f"{reg.trials_registered}")
        return reg

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"schema": SCHEMA, "updated": self.updated,
                               "trials_registered": self.trials_registered,
                               "strategies_adopted": self.strategies_adopted,
                               "ledger": [asdict(e) for e in self.ledger]}
        out.update(self.extra)
        return out

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> Registry:
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def save(self, path: str | os.PathLike[str]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
            f.write("\n")
