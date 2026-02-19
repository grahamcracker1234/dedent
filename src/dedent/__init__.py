"""
A library for dedenting text with support for interpolated values.

This module provides a :func:`dedent` function that removes common leading whitespace from
multiline strings, similar to ``textwrap.dedent`` but with automatic smart stripping and
multiline-value alignment. Works with Python 3.10+.

Key features:

- Removes minimum common indentation from all lines
- Smart-strips leading/trailing whitespace by default
- Aligns multiline interpolated values to match surrounding indentation
- On Python 3.14+: t-strings with per-value format spec directives (``{value:align}``)
- On Python 3.10-3.13: f-strings with the :func:`align` wrapper
"""

from ._dedent import align, dedent
from ._version import __version__, __version_tuple__

__all__ = ["__version__", "__version_tuple__", "align", "dedent"]
