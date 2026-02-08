import re
from enum import StrEnum, auto
from functools import reduce
from itertools import filterfalse, tee
from string.templatelib import Interpolation, Template, convert
from typing import TYPE_CHECKING, Final, Literal, LiteralString, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


class Missing:
    """Placeholder for missing values."""


MISSING: Final = Missing()


class AlignSpec(StrEnum):
    """Enumeration of alignment-specific format spec directives."""

    ALIGN = auto()
    NOALIGN = auto()


type Strip = Literal["smart", "all", "none"]

_INDENTED: Final = re.compile(r"^(\s+)")
_INDENTED_WITH_CONTENT: Final = re.compile(r"^(\s+)\S+")
_SMART_STRIP: Final = re.compile(r"^[^\S\n]*\n?")


def _partition[T](it: Iterable[T], pred: Callable[[T], bool]) -> tuple[filter[T], filterfalse[T]]:
    """
    Partition an iterable into two filters based on a predicate.

    Args:
        it: The iterable to partition.
        pred: A function that returns True for items in the first partition.

    Returns:
        A tuple of (matching_filter, non_matching_filter) where matching_filter contains items for
        which predicate returns True, and non_matching_filter contains items for which predicate
        returns False.
    """
    it1, it2 = tee(it)
    return filter(pred, it1), filterfalse(pred, it2)


def _parse_format_spec(format_spec: str) -> tuple[str, bool | None]:
    """
    Parse format spec to extract alignment-specific directives.

    Extracts 'align' and 'noalign' directives from the format spec and returns the remaining format
    spec along with the alignment override.

    Args:
        format_spec: The format specification string, potentially containing alignment directives
            separated by colons.

    Returns:
        A tuple of (remaining_format_spec, align_override) where:
        - remaining_format_spec: The format spec with alignment directives removed.
        - align_override: True if 'align' was found, False if 'noalign' was found, or None if
            neither was present. If multiple alignment specs are present, the last one takes
            precedence.
    """
    if not format_spec:
        return "", None

    specs = format_spec.split(":")

    pred = set(AlignSpec).__contains__
    dedent_specs, other_specs = _partition(specs, pred)
    *_, dedent_spec = list(dedent_specs) or [None]

    format_spec = ":".join(other_specs)

    if dedent_spec is None:
        return format_spec, None

    return format_spec, AlignSpec(dedent_spec) == AlignSpec.ALIGN


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


def _align(value: str, preceding_text: str) -> str:
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


def _handle_item(
    item: str | Interpolation,
    *,
    preceding_text: str,
    align: bool,
) -> str:
    """
    Process a single template item (string or interpolation).

    For string items, returns them as-is. For interpolations, converts the value, applies format
    specifications (extracting dedent directives), and optionally aligns multiline output.

    Args:
        item: Either a string literal or an Interpolation object.
        preceding_text: The text that precedes this item, used for alignment.
        align: Whether to align multiline values by default (can be overridden by format spec
            directives).

    Returns:
        The processed string representation of the item.
    """
    if isinstance(item, str):
        return item

    value = convert(cast("object", item.value), item.conversion)
    align_override: bool | None = None

    if item.format_spec:
        format_spec, align_override = _parse_format_spec(item.format_spec)
        if format_spec:
            value = format(value, format_spec)

    value = str(value)
    should_align = align_override if align_override is not None else align
    if should_align:
        value = _align(value, preceding_text)

    return value


def _strip(string: str, strip: Strip) -> str:
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


def _dedent(string: str) -> str:
    """
    Remove common leading whitespace from a string.

    Args:
        string: The string to dedent.

    Returns:
        The dedented string.
    """
    lines: Sequence[str] = string.split("\n")
    min_indent = None

    for line in lines:
        if indent := _safe_match_first_group(_INDENTED_WITH_CONTENT, line):
            indent_size = len(indent)
            min_indent = min(min_indent or indent_size, indent_size)

    if min_indent is None:
        return string

    return "\n".join(
        line[min_indent:] if line and line.startswith((" ", "\t")) else line
        for line in lines
    )  # fmt: skip


def dedent(
    string: Template | LiteralString,
    /,
    *,
    align: bool | Missing = MISSING,
    strip: Literal["smart", "all", "none"] | Missing = MISSING,
) -> str:
    r"""
    Remove common leading whitespace from a template string.

    This function removes the minimum common indentation from all lines in the string, preserving
    relative indentation. It supports both literal strings and t-strings (Template objects) with
    interpolations.

    For t-strings, interpolated values can include format spec directives:
    - `{value:align}` - Force alignment for this value (overrides `align` parameter)
    - `{value:noalign}` - Force no alignment for this value (overrides `align` parameter)
    - `{value:align:06d}` - Combine align directive with other format specs

    Args:
        string: The template or literal string to dedent. Can be a regular string or a t-string
            (Template object) created with the `t` prefix.
        align: Whether to align multiline interpolated values by indenting subsequent lines to match
            the indentation of the current line. Defaults to False. Can be overridden per-value
            using format spec directives.
        strip: Whether to remove leading and trailing whitespace from the result. Defaults to True.

    Raises:
        TypeError: If the input is not a string or Template object.

    Returns:
        The dedented string with common leading whitespace removed. If `strip` is True, leading and
        trailing whitespace is also removed.
    """
    align = align if not isinstance(align, Missing) else False
    strip = strip if not isinstance(strip, Missing) else "smart"

    match string:
        case str() as formatted_string:
            pass
        case Template() as template:
            formatted_string = reduce(
                lambda acc, item: acc + _handle_item(item, preceding_text=acc, align=align),
                template,
                initial="",
            )
        case unknown if not TYPE_CHECKING:  # pyright: ignore[reportUnnecessaryComparison]
            message = f"expected str or Template, not {type(unknown).__qualname__!r}"  # pyright: ignore[reportUnreachable]
            raise TypeError(message)

    formatted_string = _dedent(formatted_string)
    return _strip(formatted_string, strip)
