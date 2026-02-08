"""
A library for dedenting text with support for t-string interpolations.

This module provides a `dedent` function that removes common leading whitespace from multiline
strings, similar to `textwrap.dedent` but with enhanced support for t-strings (Template objects)
and interpolated values.

Key features:
- Removes minimum common indentation from all lines
- Supports t-strings with interpolations using `string.templatelib`
- Aligns multiline interpolated values to match surrounding indentation
- Per-value alignment control via format spec directives (`{value:align}`, `{value:noalign}`)
- Combines dedent directives with standard Python format specs
"""

from ._dedent import dedent
from ._version import __version__, __version_tuple__

__all__ = ["__version__", "__version_tuple__", "dedent"]
