from pathlib import Path

from preregister import fingerprint as fp


def test_absent_files_hash_as_absent_and_appearance_moves_the_version(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    f1 = fp.fingerprint(["a.py", "gone.py"], root=tmp_path)
    assert f1["files"] == {"a.py": f1["files"]["a.py"], "gone.py": "absent"}  # type: ignore[index]
    (tmp_path / "gone.py").write_text("y = 1\n")
    f2 = fp.fingerprint(["a.py", "gone.py"], root=tmp_path)
    assert f2["version"] != f1["version"]


def test_globs_are_included_in_sorted_order_and_content_changes_the_version(tmp_path: Path) -> None:
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "b.py").write_text("1")
    (tmp_path / "s" / "a.py").write_text("1")
    f1 = fp.fingerprint([], root=tmp_path, globs=["s/*.py"])
    assert list(f1["files"]) == ["s/a.py", "s/b.py"]  # type: ignore[arg-type]
    (tmp_path / "s" / "a.py").write_text("2")
    assert fp.fingerprint([], root=tmp_path, globs=["s/*.py"])["version"] != f1["version"]


def test_current_version_fails_soft() -> None:
    assert fp.current_version(["x"], root="/nonexistent/\0") is None
