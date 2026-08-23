"""The package is stdlib-only, names nothing from the bot it came from, and
importing it has no side effects.

These are the properties that make "domain-neutral" a checked claim rather
than a README sentence. The bot's version of this test (an AST scan of one
module for forbidden imports) is generalised to every module in the package.
"""
import ast
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "preregister")

#: Names from the source repo that must never appear in this package. If one
#: does, the extraction leaked a seam instead of cutting it.
FORBIDDEN_NAMES = ("repete1", "backtest", "fills", "judge_model", "allocator",
                   "venue", "ccxt", "strategies", "simulate_ensemble", "PaperVenue")
# ("ledger" is deliberately NOT here: the K budget IS a ledger, and the word
#  is the right one for it. The list is module and class names that only
#  mean something inside the bot.)


def _modules() -> list[str]:
    out = []
    for dirpath, _dirs, files in os.walk(SRC):
        if "__pycache__" in dirpath:
            continue
        out.extend(os.path.join(dirpath, f) for f in sorted(files) if f.endswith(".py"))
    return sorted(out)


MODULES = _modules()


def _imports(path: str) -> set[str]:
    tree = ast.parse(open(path, encoding="utf-8").read(), path)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


@pytest.mark.parametrize("path", MODULES, ids=lambda p: os.path.relpath(p, SRC))
def test_only_stdlib_and_itself(path: str) -> None:
    bad = {n for n in _imports(path)
           if n not in sys.stdlib_module_names and n != "preregister"}
    assert not bad, f"{os.path.relpath(path, ROOT)} imports non-stdlib: {sorted(bad)}"


@pytest.mark.parametrize("path", MODULES, ids=lambda p: os.path.relpath(p, SRC))
def test_no_source_repo_name_survives(path: str) -> None:
    body = open(path, encoding="utf-8").read()
    # Identifiers only: a docstring may SAY "extracted from the bot's
    # backtest.py"; code may not import or attribute-access it.
    tree = ast.parse(body, path)
    hits = sorted({n.id for n in ast.walk(tree) if isinstance(n, ast.Name)
                   and n.id in FORBIDDEN_NAMES}
                  | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                     and n.attr in FORBIDDEN_NAMES}
                  | {i for i in _imports(path) if i in FORBIDDEN_NAMES})
    assert not hits, f"{os.path.relpath(path, ROOT)} still names {hits}"


def test_importing_the_package_opens_no_file(tmp_path: "os.PathLike[str]") -> None:
    """Run in a subprocess with `open` poisoned AFTER the import machinery
    has what it needs, from an empty cwd with no config anywhere."""
    code = r"""
import builtins, io, sys
real_open = builtins.open
opened = []
def spy(file, *a, **k):
    opened.append(str(file))
    return real_open(file, *a, **k)
builtins.open = spy
import importlib, pkgutil, preregister
for m in pkgutil.walk_packages(preregister.__path__, 'preregister.'):
    importlib.import_module(m.name)
user = [p for p in opened if not p.endswith((".py", ".pyc")) and "site-packages" not in p
        and "/src/preregister/" not in p]
print(user)
sys.exit(1 if user else 0)
"""
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
    r = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, f"import opened files: {r.stdout} {r.stderr}"


def test_the_purity_scanner_can_actually_fail(tmp_path: "os.PathLike[str]") -> None:
    """Negative control for the two scanners above."""
    decoy = os.path.join(str(tmp_path), "decoy.py")
    with open(decoy, "w") as f:
        f.write("import numpy\nimport backtest\nx = fills.simulate\n")
    with pytest.raises(AssertionError):
        test_only_stdlib_and_itself(decoy)
    with pytest.raises(AssertionError):
        test_no_source_repo_name_survives(decoy)
