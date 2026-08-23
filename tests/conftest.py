"""Shared fixtures.

Every test that writes goes through `tmp_path`. There is no `state/` here to
protect, but the habit is the point: the repo this was extracted from lost a
snapshot to a cleaned gitignored directory and a test verdict to a file that
was fresh on one host and stale on another.
"""
import os

import pytest


@pytest.fixture(autouse=True)
def _no_bytecode_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    # CPython validates a cached .pyc on (mtime, size) at one-second
    # resolution. A test that rewrites a source file and re-imports it can be
    # handed the previous file's bytecode. Tests here that do that set the
    # same flag CI sets.
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    assert os.environ["PYTHONDONTWRITEBYTECODE"] == "1"
