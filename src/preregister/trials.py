"""The trials log and the walk-forward shape.

EVERY variant tried is appended — the audit trail against the False
Strategy Theorem (the more variants you try, the better the best one looks
by luck alone). A trials log with only the winners in it is a press release.
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, TypeVar

P = TypeVar("P")
R = TypeVar("R")


class TrialLog:
    """Append-only JSONL. Records carry `phase` and a UTC `logged_at`."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = os.fspath(path)

    def append(self, record: Mapping[str, Any], *, phase: str) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        row = {"phase": phase, **record,
               "logged_at": datetime.now(timezone.utc).isoformat()}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    def read(self) -> list[dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]


@dataclass(frozen=True)
class WalkForward:
    n_variants: int
    best: Any
    is_result: Any
    oos_result: Any


def walk_forward(grid: Sequence[P], fit: Callable[[P], R], validate: Callable[[P], R],
                 score: Callable[[R], Any], log: TrialLog,
                 summarise: Callable[[R], Mapping[str, Any]] | None = None
                 ) -> WalkForward:
    """Fit every variant in-sample, pick ONE winner by `score` on in-sample
    results only, validate that one out-of-sample. `validate` is called
    exactly once; the OOS number never influences selection."""
    summarise = summarise or _as_mapping
    results: list[tuple[P, R]] = []
    for params in grid:
        r = fit(params)
        results.append((params, r))
        log.append({"params": _jsonable_params(params), **summarise(r)}, phase="in_sample")
    best_params, best_r = max(results, key=lambda pr: score(pr[1]))
    oos = validate(best_params)
    log.append({"params": _jsonable_params(best_params), **summarise(oos)}, phase="oos")
    return WalkForward(len(grid), best_params, best_r, oos)


def _as_mapping(r: Any) -> Mapping[str, Any]:
    return dict(r) if isinstance(r, Mapping) else {"result": _jsonable_params(r)}


def _jsonable_params(p: Any) -> Any:
    try:
        json.dumps(p)
        return p
    except TypeError:
        return repr(p)
