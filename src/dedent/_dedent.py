import re
from string.templatelib import Interpolation, Template, convert
from typing import TYPE_CHECKING, LiteralString, cast

if TYPE_CHECKING:
    from collections.abc import Sequence

_INDENTED = re.compile(r"^(\s+)")
_INDENTED_WITH_CONTENT = re.compile(r"^(\s+)\S+")


def _safe_match_first_group(pattern: re.Pattern[str], string: str) -> str | None:
    if m := pattern.match(string):
        return m.group(1)
    return None


def _render(interpolation: Interpolation) -> str:
    value = convert(cast("object", interpolation.value), interpolation.conversion)
    if interpolation.format_spec:
        return format(value, interpolation.format_spec)
    return str(value)


def _align(value: str, preceding_text: str) -> str:
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
    match item:
        case str():
            return item
        case Interpolation():
            value = _render(item)
            if align:
                value = _align(value, preceding_text)
            return value


def dedent(
    string: Template | LiteralString,
    /,
    *,
    align: bool = False,
    strip: bool = True,
) -> str:
    """
    Dedent a template string.

    Args:
        string: The template or literal string to dedent.
        align: Whether to align the values of the interpolations if their formatted output contains
               newlines, e.g., is a multiline string.
        strip: Whether to trim leading and trailing whitespace.

    Raises:
        TypeError: If the template is not a string or a template.

    Returns:
        The dedented template string.
    """
    match string:
        case str() as formatted_string:
            pass
        case Template() as template:
            formatted_string = ""
            for item in template:
                formatted_string += _handle_item(item, preceding_text=formatted_string, align=align)
        case unknown if not TYPE_CHECKING:  # pyright: ignore[reportUnnecessaryComparison]
            message = f"Unsupported template type: {type(unknown)}"  # pyright: ignore[reportUnreachable]
            raise TypeError(message)

    lines: Sequence[str] = formatted_string.splitlines()
    min_indent = None

    for line in lines:
        if indent := _safe_match_first_group(_INDENTED_WITH_CONTENT, line):
            indent_size = len(indent)
            min_indent = min(min_indent or indent_size, indent_size)

    if min_indent is not None:
        formatted_string = "\n".join(
            line[min_indent:] if line and line.startswith((" ", "\t")) else line
            for line in lines
        )  # fmt: skip

    if strip:
        formatted_string = formatted_string.strip("\n")

    return formatted_string
