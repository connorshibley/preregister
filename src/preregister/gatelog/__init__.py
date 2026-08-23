"""A linter for pre-registration logs.

`parse()` reads the structure; `lint()` judges it against the rules in
`lint.py`; `AppendOnlyLock` makes "never edited, only appended" checkable;
`final_k()` is what a consumer reads as the current trial count.
"""
from preregister.gatelog.grammar import CLASSES, NON_SPENDING, SPENDING
from preregister.gatelog.lint import RULES, Finding, fails, lint
from preregister.gatelog.lock import AppendOnlyLock
from preregister.gatelog.parse import Log, Section, final_k, parse

__all__ = ["CLASSES", "NON_SPENDING", "SPENDING", "RULES", "Finding", "fails", "lint",
           "AppendOnlyLock", "Log", "Section", "final_k", "parse"]
