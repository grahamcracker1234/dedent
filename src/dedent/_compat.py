"""Backward-compatible dedent for Python <3.14 (no t-string support)."""

from __future__ import annotations

from typing import Literal

from ._aligned import process_align_markers
from ._core import DEFAULT_STRIP, MISSING, Missing, dedent_string, strip_string


def dedent(
    string: str,
    /,
    *,
    strip: Literal["smart", "all", "none"] | Missing = MISSING,
) -> str:
    r"""
    Remove common leading whitespace from a string.

    This function removes the minimum common indentation from all lines in the string, preserving
    relative indentation. Use :func:`align` to mark interpolated values for automatic indentation
    alignment inside f-strings.

    Args:
        string: The string to dedent.
        strip: How to strip leading/trailing whitespace. `"smart"` (default) strips one leading and
            one trailing `\n`-bounded blank segment. `"all"` strips all surrounding whitespace.
            `"none"` leaves the string unchanged.
    Raises:
        TypeError: If the input is not a string.

    Returns:
        The dedented string with common leading whitespace removed.
    """
    strip = strip if not isinstance(strip, Missing) else DEFAULT_STRIP

    if not isinstance(string, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        message = f"expected str, not {type(string).__qualname__!r}"
        raise TypeError(message)  # pyright: ignore[reportUnreachable]

    formatted_string = process_align_markers(string)
    formatted_string = dedent_string(formatted_string)
    return strip_string(formatted_string, strip)
