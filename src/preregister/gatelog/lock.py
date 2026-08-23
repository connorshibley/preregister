"""Append-only, made checkable.

The frozen prefix is everything above the LAST heading in the file. A new
section or addendum is appended below it and moves the boundary; re-freeze
in the same commit. Any edit above the boundary changes the hash. This
generalises the single byte-sentinel the source repo used (a superseded
figure that a test asserted was still present)."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass

from preregister.gatelog import grammar as g


@dataclass(frozen=True)
class AppendOnlyLock:
    frozen_through_line: int     # 1-based; lines BEFORE this one are frozen
    sha256: str

    @staticmethod
    def frozen_prefix(text: str) -> tuple[int, str]:
        heads = list(g.ANY_HEADING.finditer(text))
        if not heads:
            return 1, ""
        last = heads[-1].start()
        line = text.count("\n", 0, last) + 1
        return line, text[:last]

    @classmethod
    def freeze(cls, text: str) -> AppendOnlyLock:
        line, prefix = cls.frozen_prefix(text)
        return cls(line, hashlib.sha256(prefix.encode("utf-8")).hexdigest())

    def check(self, text: str) -> str | None:
        """None when the frozen prefix is intact; otherwise a message."""
        lines = text.split("\n")
        if len(lines) < self.frozen_through_line:
            return (f"log is shorter ({len(lines)} lines) than its frozen prefix "
                    f"({self.frozen_through_line - 1} lines)")
        prefix = "\n".join(lines[:self.frozen_through_line - 1])
        if self.frozen_through_line > 1:
            prefix += "\n"
        got = hashlib.sha256(prefix.encode("utf-8")).hexdigest()
        if got != self.sha256:
            return (f"frozen prefix (lines 1-{self.frozen_through_line - 1}) has changed: "
                    f"expected {self.sha256[:12]}, got {got[:12]} — history was edited")
        return None

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> AppendOnlyLock:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return cls(int(d["frozen_through_line"]), str(d["sha256"]))

    def save(self, path: str | os.PathLike[str]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, sort_keys=True)
            f.write("\n")
