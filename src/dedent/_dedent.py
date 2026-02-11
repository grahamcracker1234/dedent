from functools import reduce
from itertools import filterfalse, tee
from string.templatelib import Interpolation, Template, convert
from typing import TYPE_CHECKING, Literal, LiteralString, cast

from ._aligned import process_align_markers
from ._core import (
    MISSING,
    AlignSpec,
    Missing,
    Strip,
    align_value,
    dedent_string,
    strip_string,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

# Re-export for backwards compatibility with existing test imports.
__all__ = ["MISSING", "AlignSpec", "Missing", "Strip", "dedent"]


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
    specs = format_spec.split(":")

    pred = set(AlignSpec).__contains__
    dedent_specs, other_specs = _partition(specs, pred)
    *_, dedent_spec = list(dedent_specs) or [None]

    format_spec = ":".join(other_specs)

    if dedent_spec is None:
        return format_spec, None

    return format_spec, AlignSpec(dedent_spec) == AlignSpec.ALIGN


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
        value = align_value(value, preceding_text)

    return value


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
            formatted_string = process_align_markers(formatted_string)
        case Template() as template:
            formatted_string = reduce(
                lambda acc, item: acc + _handle_item(item, preceding_text=acc, align=align),
                template,
                initial="",
            )
        case unknown if not TYPE_CHECKING:  # pyright: ignore[reportUnnecessaryComparison]
            message = f"expected str or Template, not {type(unknown).__qualname__!r}"  # pyright: ignore[reportUnreachable]
            raise TypeError(message)

    formatted_string = dedent_string(formatted_string)
    return strip_string(formatted_string, strip)
