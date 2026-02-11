"""Pytest configuration for cross-version compatibility."""

from __future__ import annotations

import sys

# test_dedent.py uses t-string syntax which causes SyntaxError on Python < 3.14.
collect_ignore_glob: list[str] = []
if sys.version_info < (3, 14):
    collect_ignore_glob.append("test_dedent.py")  # pyright: ignore[reportUnreachable]
