"""A golden snapshot: "this refactor moved no number."

Compared on the SERIALISED form, because that is the artefact that gets
committed, and because `inf` is a real result (gains, no losses) that JSON
cannot carry — it is stringified, never dropped. When a change is SUPPOSED
to move numbers, re-capture on purpose and record the diff in the gate log;
never let a suite that stays green either way absorb it."""
from __future__ import annotations

import difflib
import json
import math
import os
from collections.abc import Callable, Mapping
from typing import Any


def jsonable(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return "inf" if obj > 0 else ("-inf" if obj < 0 else "nan")
    return obj


class Golden:
    def __init__(self, path: str | os.PathLike[str], producer: Callable[[], Mapping[str, Any]],
                 *, note: str) -> None:
        self.path = os.fspath(path)
        self.producer = producer
        self.note = note

    def _current(self) -> str:
        doc = {"_meta": {"what": self.note}, **jsonable(self.producer())}
        return json.dumps(doc, indent=2, sort_keys=True) + "\n"

    def write(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self._current())

    def check(self, *, max_lines: int = 60) -> list[str]:
        """[] when identical; otherwise the first `max_lines` of a unified diff."""
        with open(self.path, encoding="utf-8") as f:
            committed = f.read()
        current = self._current()
        if committed == current:
            return []
        return list(difflib.unified_diff(committed.splitlines(), current.splitlines(),
                                         "golden", "current", lineterm=""))[:max_lines]
