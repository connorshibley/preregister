import hashlib
from pathlib import Path

import pytest

from preregister import snapshot


def test_sha256_file_matches_hashlib(tmp_path: Path) -> None:
    p = tmp_path / "blob"
    p.write_bytes(b"x" * (3 << 20) + b"tail")
    assert snapshot.sha256_file(p) == hashlib.sha256(p.read_bytes()).hexdigest()


def test_verify_refuses_drift_and_passes_when_matched(tmp_path: Path) -> None:
    (tmp_path / "a").write_bytes(b"abc")
    (tmp_path / "b").write_bytes(b"abd")
    good = {"a": snapshot.sha256_file(tmp_path / "a")}
    snapshot.verify(good, root=tmp_path)
    with pytest.raises(snapshot.SnapshotDrift, match="SNAPSHOT DRIFT: b"):
        snapshot.verify({**good, "b": good["a"]}, root=tmp_path)
