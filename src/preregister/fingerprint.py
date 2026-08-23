"""A track record is only attributable if the decision surface that produced
it can be named. This stamps a short version over a declared set of files —
stamp-only, never a lock: the honest fit for an iterating system is
segmentation, not a freeze.

The file list is an argument, not a module constant: the bot's constant
kept two deleted modules for months, hashing their absence on purpose."""
from __future__ import annotations

import glob
import hashlib
import os
from collections.abc import Sequence


def fingerprint(files: Sequence[str], *, root: str | os.PathLike[str] = ".",
                globs: Sequence[str] = ()) -> dict[str, object]:
    """{"version": 12-hex, "files": {rel: 8-hex | "absent"}}. Missing files
    hash as "absent" so the version still moves when one appears or goes."""
    rootp = os.fspath(root)
    paths = list(files)
    for pattern in globs:
        paths += sorted(os.path.relpath(p, rootp) for p in glob.glob(os.path.join(rootp, pattern)))
    agg = hashlib.sha256()
    out: dict[str, str] = {}
    for rel in paths:
        try:
            with open(os.path.join(rootp, rel), "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
        except OSError:
            h = "absent"
        out[rel] = h[:8]
        agg.update(f"{rel}:{h}\n".encode())
    return {"version": agg.hexdigest()[:12], "files": out}


def current_version(files: Sequence[str], *, root: str | os.PathLike[str] = ".",
                    globs: Sequence[str] = ()) -> str | None:
    """Fail-soft: stamping is instrumentation and must never block a cycle."""
    try:
        return str(fingerprint(files, root=root, globs=globs)["version"])
    except Exception:  # noqa: BLE001
        return None
