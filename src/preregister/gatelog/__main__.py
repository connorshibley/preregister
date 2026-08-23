"""python -m preregister.gatelog LOG [--strict] [--k0 N] [--lock F [--freeze]] [--registry F] [--json]"""
from __future__ import annotations

import argparse
import json
import sys

from preregister.budget import Registry
from preregister.gatelog.lint import fails, lint
from preregister.gatelog.lock import AppendOnlyLock
from preregister.gatelog.parse import final_k, parse


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="preregister.gatelog", description=__doc__)
    ap.add_argument("log")
    ap.add_argument("--strict", action="store_true", help="warnings fail; era-A leniency off")
    ap.add_argument("--k0", type=int, default=0, help="trial count before the first section")
    ap.add_argument("--lock", help="append-only lock file to check (or write, with --freeze)")
    ap.add_argument("--freeze", action="store_true", help="write --lock from the current text and exit")
    ap.add_argument("--registry", help="a budget.Registry JSON; its K and adopted count are cross-checked")
    ap.add_argument("--json", action="store_true", help="machine-readable findings on stdout")
    a = ap.parse_args(argv)

    with open(a.log, encoding="utf-8") as fh:
        text = fh.read()

    if a.freeze:
        if not a.lock:
            ap.error("--freeze needs --lock")
        AppendOnlyLock.freeze(text).save(a.lock)
        print(f"froze {a.lock}")
        return 0

    lock = AppendOnlyLock.load(a.lock) if a.lock else None
    adopted: int | None = None
    reg_k: int | None = None
    if a.registry:
        reg = Registry.load(a.registry)
        adopted, reg_k = reg.strategies_adopted, reg.k()

    findings = lint(text, strict=a.strict, k0=a.k0, lock=lock, registry_adopted=adopted)
    fk = final_k(parse(text))
    extra: list[str] = []
    if reg_k is not None and fk != reg_k:
        extra.append(f"registry K={reg_k} but the log's last tally says {fk}")

    if a.json:
        print(json.dumps({"final_k": fk, "registry_k": reg_k,
                          "findings": [f.to_dict() for f in findings],
                          "mismatch": extra}, indent=2, sort_keys=True))
    else:
        for f in findings:
            print(f"{f.level:7} {f.rule} {f.section:5} L{f.line}: {f.message}")
        n = {lvl: sum(1 for f in findings if f.level == lvl) for lvl in ("error", "warning", "info")}
        print(f"final K = {fk}; {n['error']} errors, {n['warning']} warnings, {n['info']} info")
        for e in extra:
            print("error   " + e)
    return 1 if (fails(findings, strict=a.strict) or extra) else 0


if __name__ == "__main__":
    sys.exit(main())
