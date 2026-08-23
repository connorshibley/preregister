"""A gate run against drifted data is not a re-run; it is a new experiment
wearing an old name. Pin the inputs by hash and refuse to proceed on drift.
A library raises; it does not `SystemExit`."""
from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping


class SnapshotDrift(RuntimeError):
    pass


def sha256_file(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(expected: Mapping[str, str], *, root: str | os.PathLike[str] = ".") -> None:
    """`expected` maps relative path -> sha256 hex. Every file must match."""
    for rel, want in expected.items():
        got = sha256_file(os.path.join(os.fspath(root), rel))
        if got != want:
            raise SnapshotDrift(
                f"SNAPSHOT DRIFT: {rel}\n  expected {want}\n  got      {got}\n"
                f"Refusing to run — the result would not be comparable. "
                f"Do not re-hash it; find out what changed.")
