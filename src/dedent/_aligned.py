"""Aligned wrapper for f-string backward compatibility, compatible with Python 3.10+."""

from __future__ import annotations

import re
import uuid
from typing import Final

from ._core import align_value

_ALIGN_MARKER: Final = re.compile(
    r"\x00DEDENT_ALIGN_START:([a-f0-9]{32})\x00(.*?)\x00DEDENT_ALIGN_END:\1\x00",
    re.DOTALL,
)


class Aligned:
    """
    Wrapper that embeds alignment markers around a value for f-string compatibility.

    When used inside an f-string and passed to ``dedent()``, the markers signal that the
    interpolated value should be indented to match its surrounding context.

    This class implements ``__str__``, ``__repr__``, and ``__format__`` so that conversion
    flags (``!s``, ``!r``) and format specifications work correctly.
    """

    _START_PREFIX: Final = "\x00DEDENT_ALIGN_START:"
    _END_PREFIX: Final = "\x00DEDENT_ALIGN_END:"
    _SEP: Final = "\x00"

    _value: object
    _id: str

    def __init__(self, value: object) -> None:
        self._value = value
        self._id = uuid.uuid4().hex

    def _wrap(self, text: str) -> str:
        start = f"{self._START_PREFIX}{self._id}{self._SEP}"
        end = f"{self._END_PREFIX}{self._id}{self._SEP}"
        return f"{start}{text}{end}"

    def __str__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        return self._wrap(str(self._value))

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        return self._wrap(repr(self._value))

    def __format__(self, format_spec: str) -> str:  # pyright: ignore[reportImplicitOverride]
        return self._wrap(format(self._value, format_spec))


def align(value: object) -> Aligned:
    """
    Mark a value for automatic indentation alignment inside ``dedent()``.

    Wrap an interpolated value so that, when the surrounding f-string is passed to
    ``dedent()``, subsequent lines of the value are indented to match the current
    indentation context.

    Example::

        from dedent import align, dedent

        items = dedent(\"\"\"
            - apples
            - bananas
        \"\"\")
        shopping_list = dedent(f\"\"\"
            Groceries:
                {align(items)}
            ---
        \"\"\")
        print(shopping_list)
        # Groceries:
        #     - apples
        #     - bananas
        # ---

    Args:
        value: The value to align. Can be any object; ``str()``, ``repr()``, or
            ``format()`` will be called on it depending on usage in the f-string.

    Returns:
        An :class:`Aligned` wrapper whose string representation contains invisible
        markers that ``dedent()`` uses to apply alignment.
    """
    return Aligned(value)


def process_align_markers(string: str) -> str:
    """
    Detect alignment markers in *string*, apply indentation alignment, and remove the markers.

    This is called by ``dedent()`` when it receives a plain string (the f-string path).
    Markers are inserted by :class:`Aligned` wrappers created via :func:`align`.

    Args:
        string: The string potentially containing alignment markers.

    Returns:
        The string with markers removed and aligned values indented appropriately.
    """
    result_parts: list[str] = []
    last_end = 0

    for match in _ALIGN_MARKER.finditer(string):
        # Text before this marker
        result_parts.append(string[last_end : match.start()])
        # Preceding text is what we've built so far
        preceding_text = "".join(result_parts)
        value = match.group(2)
        aligned_value = align_value(value, preceding_text)
        result_parts.append(aligned_value)
        last_end = match.end()

    if last_end == 0:
        return string

    result_parts.append(string[last_end:])
    return "".join(result_parts)
