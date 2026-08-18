import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, TypeVar, final
from uuid import uuid4

_T = TypeVar("_T")

_ALIGN_MARKER_PREFIX: Final = "DEDENT_ALIGN"
_NOALIGN_SPEC: Final = "noalign"
_SEP: Final = "\x00"

_ALIGN_MARKER: Final = re.compile(
    rf"{_SEP}{_ALIGN_MARKER_PREFIX}:([a-f0-9]{{32}}){_SEP}(.*?){_SEP}{_ALIGN_MARKER_PREFIX}:\1{_SEP}",
    re.DOTALL,
)
_OPENING_LINE: Final = re.compile(r"^[ \t]*(\r\n|\r|\n)")


def _align_value(value: str, preceding_text: str) -> str:
    """
    Align a multiline value to the column where it is inserted.

    If the value contains newlines, each line after the first starts directly below the first.
    Alignment is also added after a terminal newline. This keeps later text at the insertion column.

    Args:
        value: The string value to align, potentially containing newlines.
        preceding_text: The text that precedes this value, used to determine its insertion column.

    Returns:
        The value with subsequent lines aligned to the insertion column.
    """
    current_line = preceding_text[preceding_text.rfind("\n") + 1 :]
    alignment = "".join(character if character in " \t" else " " for character in current_line)
    if alignment:
        return value.replace("\n", "\n" + alignment)

    return value


def _omit_opening_newline(string: str) -> str:
    """
    Omit the newline immediately following opening triple quotes.

    Args:
        string: The dedented string.

    Returns:
        The string with one initial line ending removed, if present.
    """
    if string.startswith("\r\n"):
        return string[2:]
    if string.startswith(("\r", "\n")):
        return string[1:]
    return string


def _common_indentation(string: str) -> str | None:
    """
    Find and validate the longest common leading indentation in a string.

    This follows the indentation rules proposed by PEP 822: indentation is an
    exact prefix of spaces and tabs, space/tab-only lines are ignored, and a
    final space/tab-only line constrains the indentation like a closing
    triple-quote line. A carriage return before a newline is preserved as part
    of the line ending rather than treated as content.

    Args:
        string: The literal framework to inspect.

    Raises:
        IndentationError: If a line's leading whitespace is inconsistent with the
            common indentation prefix.

    Returns:
        The common indentation, or `None` when no line determines it.
    """
    lines = [line.removesuffix("\r") for line in string.split("\n")]
    last_index = len(lines) - 1
    indentations = [
        line[: len(line) - len(line.lstrip(" \t"))]
        for index, line in enumerate(lines)
        if line.strip(" \t") or (last_index > 0 and index == last_index)
    ]

    if not indentations:
        return None

    indentation = indentations[0]
    for candidate in indentations[1:]:
        common_length = 0
        for left, right in zip(indentation, candidate, strict=False):
            if left != right:
                break
            common_length += 1
        indentation = indentation[:common_length]
        if not indentation:
            break

    for line_number, line in enumerate(lines, start=1):
        if len(line) >= len(indentation):
            is_compatible = line.startswith(indentation)
        else:
            is_compatible = indentation.startswith(line)
        if not is_compatible:
            message = f"inconsistent indentation in dedented string at line {line_number}"
            raise IndentationError(message)

    return indentation


def _remove_indentation(literals: list[str], indentation: str) -> list[str]:
    """
    Remove indentation from literal parts without crossing their opaque holes.

    Returns:
        The dedented literal parts.
    """
    if not indentation:
        return literals

    dedented_literals: list[str] = []
    at_line_start = True
    removed = 0
    last_index = len(literals) - 1

    for literal_index, literal in enumerate(literals):
        dedented: list[str] = []
        for character in literal:
            if character == "\n":
                dedented.append(character)
                at_line_start = True
                removed = 0
            elif at_line_start and removed < len(indentation) and character in " \t":
                removed += 1
            else:
                dedented.append(character)
                at_line_start = False

        dedented_literals.append("".join(dedented))
        if literal_index < last_index:
            at_line_start = False

    return dedented_literals


def _dedent_literal_parts(literals: list[str]) -> list[str]:
    """
    Dedent literal parts while treating the holes between them as opaque content.

    Returns:
        The dedented parts, with a spaces-and-tabs-only opening line omitted.
    """
    normalized_literals = literals.copy()
    opening_line = _OPENING_LINE.match(normalized_literals[0])
    if opening_line is not None:
        line_ending = opening_line.group(1)
        normalized_literals[0] = line_ending + normalized_literals[0][opening_line.end() :]

    framework = _SEP.join(normalized_literals)
    indentation = _common_indentation(framework)
    dedented_literals = (
        normalized_literals
        if indentation is None
        else _remove_indentation(normalized_literals, indentation)
    )

    if opening_line is not None:
        dedented_literals[0] = _omit_opening_newline(dedented_literals[0])

    return dedented_literals


@final
@dataclass(frozen=True, kw_only=True)
class Aligned:
    """
    Wrapper that embeds alignment markers around a value for f-string compatibility.

    When used inside an f-string and passed to `dedent()`, the markers signal that the
    interpolated value should be indented to match its surrounding context.

    This class implements `__str__`, `__repr__`, and `__format__` so that conversion
    flags (`!s`, `!r`) and format specifications work correctly.
    """

    _value: object
    _ID: Final[str] = field(default_factory=lambda: uuid4().hex, init=False)

    def _wrap(self, text: str) -> str:
        marker = f"{_SEP}{_ALIGN_MARKER_PREFIX}:{self._ID}{_SEP}"
        return f"{marker}{text}{marker}"

    # NOTE: PEP 698: Override Decorator (3.12)
    # @overload
    def __str__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        return self._wrap(str(self._value))

    # NOTE: PEP 698: Override Decorator (3.12)
    # @overload
    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        return self._wrap(repr(self._value))

    # NOTE: PEP 698: Override Decorator (3.12)
    # @overload
    def __format__(self, format_spec: str) -> str:  # pyright: ignore[reportImplicitOverride]
        return self._wrap(format(self._value, format_spec))


def align(value: object) -> Aligned:
    """
    Mark a value for automatic indentation alignment inside `dedent()`.

    Wrap an interpolated value so that, when the surrounding f-string is passed to
    `dedent()`, subsequent lines of the value start in the same column as the first.
    t-string interpolations align automatically; an `align()`-marked value there raises
    `TypeError`.

    Example::

        from dedent import align, dedent

        items = dedent(\"\"\"
            - apples
            - bananas\"\"\")
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
        value: The value to align. Can be any object; `str()`, `repr()`, or
            `format()` will be called on it depending on usage in the f-string.

    Returns:
        An `Aligned` wrapper whose string representation contains invisible
        markers that `dedent()` uses to apply alignment.
    """
    return Aligned(_value=value)


def _extend_current_line(current_line: str, text: str) -> str:
    """
    Extend the current output line with newly rendered text.

    Returns:
        The text after the final newline, or the extended current line if there is no newline.
    """
    _, separator, suffix = text.rpartition("\n")
    return suffix if separator else current_line + text


def _fill_parts(
    literals: list[str],
    holes: list[_T],
    render: Callable[[_T, str], str],
    *,
    preceding_text: str = "",
) -> str:
    """
    Fill holes between literal parts while tracking the current output line.

    Raises:
        RuntimeError: If the literal and hole counts are inconsistent.

    Returns:
        The rendered literal and hole parts.
    """
    if len(literals) != len(holes) + 1:
        message = "literal and hole counts are inconsistent"
        raise RuntimeError(message)

    result_parts = [literals[0]]
    current_line = _extend_current_line(
        preceding_text[preceding_text.rfind("\n") + 1 :],
        literals[0],
    )

    for hole, literal in zip(holes, literals[1:], strict=True):
        rendered = render(hole, current_line)
        result_parts.extend((rendered, literal))
        current_line = _extend_current_line(current_line, rendered)
        current_line = _extend_current_line(current_line, literal)

    return "".join(result_parts)


def _split_align_markers(string: str) -> tuple[list[str], list[str]]:
    """
    Split a string into literal parts and top-level aligned values.

    Returns:
        The alternating literal parts and aligned values.
    """
    literals: list[str] = []
    values: list[str] = []
    last_end = 0

    for match in _ALIGN_MARKER.finditer(string):
        literals.append(string[last_end : match.start()])
        values.append(match.group(2))
        last_end = match.end()

    literals.append(string[last_end:])
    return literals, values


def _render_align_value(value: str, preceding_text: str) -> str:
    """
    Render one aligned value after recursively rendering its nested values.

    Returns:
        The marker-free value aligned to its preceding text.
    """
    literals, nested_values = _split_align_markers(value)
    rendered = _fill_parts(
        literals,
        nested_values,
        _render_align_value,
    )
    return _align_value(rendered, preceding_text)


def _dedent_and_fill(
    literals: list[str],
    holes: list[_T],
    render: Callable[[_T, str], str],
) -> str:
    """
    Dedent literal structure, then render its opaque holes in one linear pass.

    Raises:
        RuntimeError: If hole metadata is inconsistent with the literal framework.

    Returns:
        The dedented and rendered string.
    """
    if len(literals) != len(holes) + 1:
        message = "literal and hole counts are inconsistent"
        raise RuntimeError(message)

    dedented_literals = _dedent_literal_parts(literals)
    return _fill_parts(dedented_literals, holes, render)


def _dedent_marked_string(string: str) -> str:
    """
    Dedent static text without letting aligned values affect its indentation.

    Returns:
        The dedented string with deferred values restored and aligned.
    """
    literals, values = _split_align_markers(string)
    return _dedent_and_fill(literals, values, _render_align_value)


if sys.version_info >= (3, 14):
    from string.templatelib import Interpolation, Template, convert
    from typing import LiteralString

    def _parse_format_spec(format_spec: str) -> tuple[str, bool]:
        """
        Remove the `noalign` directive from a format specification.

        Args:
            format_spec: The format specification, potentially containing `noalign`.

        Returns:
            The remaining format specification and whether column alignment is disabled.
        """
        specs = format_spec.split(":")
        return ":".join(spec for spec in specs if spec != _NOALIGN_SPEC), _NOALIGN_SPEC in specs

    def _handle_item(
        item: Interpolation[object],
        *,
        preceding_text: str,
    ) -> str:
        """
        Convert, format, and column-align one interpolation.

        Args:
            item: The interpolation to render.
            preceding_text: The text that precedes this item, used for alignment.

        Raises:
            TypeError: If the rendered value contains `align()` markers.

        Returns:
            The processed string representation of the item.
        """
        value = convert(item.value, item.conversion)
        disable_alignment = False

        if item.format_spec:
            format_spec, disable_alignment = _parse_format_spec(item.format_spec)
            if format_spec:
                value = format(value, format_spec)

        value = str(value)
        if _ALIGN_MARKER.search(value):
            message = "align() is only supported in f-strings; t-strings align automatically"
            raise TypeError(message)
        if not disable_alignment:
            value = _align_value(value, preceding_text)

        return value

    def _dedent_template(template: Template) -> str:
        """
        Dedent template literals before rendering their interpolations.

        Returns:
            The dedented and rendered template.
        """

        def render_interpolation(item: Interpolation[object], preceding_text: str) -> str:
            return _handle_item(item, preceding_text=preceding_text)

        return _dedent_and_fill(
            list(template.strings),
            list(template.interpolations),
            render_interpolation,
        )

    def dedent(  # pyright: ignore[reportUnreachable]
        string: Template | LiteralString,
        /,
    ) -> str:
        r'''
        Dedent a template string and column-align its interpolated values.

        This function removes the longest exact indentation prefix shared by all nonblank lines,
        preserving relative indentation. A final whitespace-only line constrains the prefix like
        the closing-quotes line in PEP 822. It supports both literal strings and t-strings
        (`Template` objects) with interpolations.

        For t-strings, interpolated values use column alignment by default. Use the format spec
        directive:
        - `{value:noalign}` - Disable column alignment for this value

        `align()` is only for f-strings. A t-string interpolation whose rendered value contains
        `align()` markers raises `TypeError`.

        Args:
            string: Template or literal string to dedent.
        Raises:
            IndentationError: If a line is incompatible with the common indentation prefix.
            TypeError: If the input is not a string or Template, or if a t-string interpolation
                contains `align()` markers.

        Returns:
            The string with common leading whitespace and its opening newline removed. All other
            whitespace is preserved.

        Example::

            >>> from dedent import dedent
            >>> result = dedent(t"""
            ...     Hello, {"World"}!
            ...     """)
            >>> print(result)
            Hello, World!
        '''  # ruff: ignore[docstring-extraneous-exception]
        match string:
            case str() as formatted_string:
                return _dedent_marked_string(formatted_string)
            case Template() as template:
                return _dedent_template(template)
            case unknown if not TYPE_CHECKING:  # pyright: ignore[reportUnnecessaryComparison]
                message = f"expected str or Template, not {type(unknown).__qualname__!r}"  # pyright: ignore[reportUnreachable]
                raise TypeError(message)

else:

    def dedent(  # pyright: ignore[reportUnreachable]
        string: str,
        /,
    ) -> str:
        r'''
        Dedent a string and align marked multiline values.

        This function removes the longest exact indentation prefix shared by all nonblank lines,
        preserving relative indentation. A final whitespace-only line constrains the prefix like
        the closing-quotes line in PEP 822. Use `align()` to mark interpolated values for automatic
        indentation alignment inside f-strings.

        Args:
            string: String to dedent.
        Raises:
            IndentationError: If a line is incompatible with the common indentation prefix.
            TypeError: If the input is not a string.

        Returns:
            The string with common leading whitespace and its opening newline removed. All other
            whitespace is preserved.

        Example::

            >>> from dedent import align, dedent
            >>> items = "- a\\n- b"
            >>> result = dedent(f"""
            ...     List:
            ...         {align(items)}
            ...     """)
            >>> print(result)
            List:
                - a
                - b
        '''  # ruff: ignore[docstring-extraneous-exception]
        if not isinstance(string, str):  # pyright: ignore[reportUnnecessaryIsInstance]
            message = f"expected str, not {type(string).__qualname__!r}"
            raise TypeError(message)  # pyright: ignore[reportUnreachable]

        return _dedent_marked_string(string)
