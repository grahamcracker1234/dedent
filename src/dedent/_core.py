"""Shared utilities for dedent, compatible with Python 3.10+."""

# NOTE: PEP 649: Deferred Evaluation Of Annotations (3.14+)
from __future__ import annotations

import re
from enum import Enum
from functools import reduce
from typing import Final, Literal

DEFAULT_STRIP: Final = "smart"
DEFAULT_ALIGN: Final = False


# NOTE: PEP 661: Sentinel Values (Deferred)
class Missing:
    """Placeholder for missing values."""


MISSING: Final = Missing()


# NOTE: PEP 663: Standardizing Enum behaviors (3.11+)
# class AlignSpec(StrEnum):
#     """Enumeration of alignment-specific format spec directives."""
#
#     ALIGN = auto()
#     NOALIGN = auto()
#
class AlignSpec(str, Enum):
    """Enumeration of alignment-specific format spec directives."""

    ALIGN = "align"
    NOALIGN = "noalign"


# NOTE: PEP 695: Type Parameter Syntax (3.12+)
# type Strip = Literal["smart", "all", "none"]
Strip = Literal["smart", "all", "none"]

_INDENTED: Final = re.compile(r"^(\s+)")
_INDENTED_WITH_CONTENT: Final = re.compile(r"^(\s+)\S+")
_SMART_STRIP: Final = re.compile(r"^[^\S\n]*\n?")


def _safe_match_first_group(pattern: re.Pattern[str], string: str) -> str | None:
    """
    Safely extract the first capture group from a regex match.

    Args:
        pattern: The compiled regex pattern to match against.
        string: The string to match.

    Returns:
        The first capture group if the pattern matches, None otherwise.
    """
    if m := pattern.match(string):
        return m.group(1)
    return None


def align_value(value: str, preceding_text: str) -> str:
    """
    Align multiline value to match the indentation of the current line.

    If the value contains newlines, each line after the first is indented to match the indentation
    of the current line in the preceding text.

    Args:
        value: The string value to align, potentially containing newlines.
        preceding_text: The text that precedes this value, used to determine the current line's
            indentation.

    Returns:
        The value with subsequent lines indented to match the current line's indentation, or the
        original value if no indentation is found or if the value doesn't contain newlines.
    """
    current_line = preceding_text[preceding_text.rfind("\n") + 1 :]
    if indent := _safe_match_first_group(_INDENTED, current_line):
        return value.replace("\n", "\n" + indent)

    return value


def strip_string(string: str, strip: Strip) -> str:
    """
    Strip leading and trailing whitespace from a string.

    Args:
        string: The string to strip.
        strip: The strip mode to use.

    Returns:
        The stripped string.
    """
    match strip:
        case "smart":
            string = _SMART_STRIP.sub("", string, count=1)
            # Reversing to get the rightmost match instead of leftmost
            return _SMART_STRIP.sub("", string[::-1], count=1)[::-1]
        case "all":
            return string.strip()
        case "none":
            return string


def dedent_string(string: str) -> str:
    """
    Remove common leading whitespace from a string.

    Args:
        string: The string to dedent.

    Returns:
        The dedented string.
    """
    lines = string.split("\n")
    max_indent = len(string)
    min_indent: int = reduce(
        lambda acc, line: (
            min(acc, len(indent))
            if (indent := _safe_match_first_group(_INDENTED_WITH_CONTENT, line))
            else acc
        ),
        lines,
        max_indent,
    )

    if min_indent == max_indent:
        return string

    return "\n".join(
        line[min_indent:] if len(line) >= min_indent and line[:min_indent].isspace() else line
        for line in lines
    )
