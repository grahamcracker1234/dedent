"""
A library for dedenting text with support for interpolated values.

This module provides a `dedent` function that removes common leading whitespace from
multiline strings, follows PEP 822's newline behavior, and aligns multiline values.
Works with Python 3.10+.

Key features:

- Uses PEP 822's exact common-prefix and closing-line indentation rules
- Omits the opening newline and preserves all other whitespace
- Aligns multiline interpolated values to their interpolation column
- On Python 3.14+: t-strings with per-value format spec directives (`{value:align}`)
- On Python 3.10-3.13: f-strings with the `align` wrapper
"""

from ._dedent import align, dedent
from ._version import __version__, __version_tuple__

__all__ = ["__version__", "__version_tuple__", "align", "dedent"]
