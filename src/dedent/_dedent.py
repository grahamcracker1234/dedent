import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from itertools import filterfalse, tee
from typing import TYPE_CHECKING, Final, Literal, TypeVar, final
from uuid import uuid4


class Missing:
    """Placeholder for missing values."""


MISSING: Final = Missing()

DEFAULT_STRIP: Final = "smart"
DEFAULT_ALIGN: Final = False


class AlignSpec(str, Enum):
    """Enumeration of alignment-specific format spec directives."""

    ALIGN = "align"
    NOALIGN = "noalign"


Strip = Literal["smart", "all", "none"]
_T = TypeVar("_T")

_SMART_STRIP_START: Final = re.compile(r"^[^\S\r\n]*(?:\r\n|[\r\n])?")
_SMART_STRIP_END: Final = re.compile(r"(?:\r\n|[\r\n])?[^\S\r\n]*\Z")

_ALIGN_MARKER_PREFIX: Final = "DEDENT_ALIGN"
_HOLE_MARKER_PREFIX: Final = "DEDENT_HOLE"
_SEP: Final = "\x00"

_ALIGN_MARKER: Final = re.compile(
    rf"{_SEP}{_ALIGN_MARKER_PREFIX}:([a-f0-9]{{32}}){_SEP}(.*?){_SEP}{_ALIGN_MARKER_PREFIX}:\1{_SEP}",
    re.DOTALL,
)


def _align_value(value: str, preceding_text: str) -> str:
    """
    Align a multiline value to the column where it is inserted.

    If the value contains newlines, each line after the first starts directly below the first.

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


def _strip_string(string: str, strip: Strip) -> str:
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
            string = _SMART_STRIP_START.sub("", string, count=1)
            return _SMART_STRIP_END.sub("", string, count=1)
        case "all":
            return string.strip()
        case "none":
            return string


def _dedent_string(string: str) -> str:
    """
    Remove the longest common leading indentation from a string.

    This follows the indentation rules proposed by PEP 822: indentation is an
    exact prefix of spaces and tabs, space/tab-only lines are ignored, and a
    final space/tab-only line constrains the indentation like a closing
    triple-quote line. A carriage return before a newline is preserved as part
    of the line ending rather than treated as content.

    Args:
        string: The string to dedent.

    Raises:
        IndentationError: If a line's leading whitespace is inconsistent with the
            common indentation prefix.

    Returns:
        The dedented string.
    """
    lines = [
        (line.removesuffix("\r"), "\r" if line.endswith("\r") else "")
        for line in string.split("\n")
    ]
    last_index = len(lines) - 1
    indentations = [
        line[: len(line) - len(line.lstrip(" \t"))]
        for index, (line, _) in enumerate(lines)
        if line.strip(" \t") or (last_index > 0 and index == last_index)
    ]

    if not indentations:
        return string

    indentation = indentations[0]
    for candidate in indentations[1:]:
        common_length = 0
        for left, right in zip(indentation, candidate, strict=False):
            if left != right:
                break
            common_length += 1
        indentation = indentation[:common_length]
        if not indentation:
            return string

    dedented_lines: list[str] = []
    for line_number, (line, line_ending) in enumerate(lines, start=1):
        if len(line) >= len(indentation):
            if not line.startswith(indentation):
                message = f"inconsistent indentation in dedented string at line {line_number}"
                raise IndentationError(message)
            dedented_lines.append(line[len(indentation) :] + line_ending)
        elif indentation.startswith(line):
            dedented_lines.append(line_ending)
        else:
            message = f"inconsistent indentation in dedented string at line {line_number}"
            raise IndentationError(message)

    return "\n".join(dedented_lines)


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


def _render_align_marker(value: str, preceding_text: str) -> str:
    """
    Render one aligned value, processing nested markers first.

    Returns:
        The marker-free value aligned to its preceding text.
    """
    return _align_value(process_align_markers(value), preceding_text)


def process_align_markers(string: str, *, preceding_text: str = "") -> str:
    """
    Detect alignment markers in `string`, apply indentation alignment, and remove the markers.

    This is called by `dedent()` when it receives a plain string (the f-string path).
    Markers are inserted by `Aligned` wrappers created via `align`.

    Args:
        string: The string potentially containing alignment markers.
        preceding_text: Text preceding `string`, used to align a marker at its start.

    Returns:
        The string with markers removed and aligned values indented appropriately.
    """
    literals, values = _split_align_markers(string)
    if not values:
        return string

    return _fill_parts(
        literals,
        values,
        _render_align_marker,
        preceding_text=preceding_text,
    )


def _dedent_and_fill(
    literals: list[str],
    holes: list[_T],
    render: Callable[[_T, str], str],
    strip: Strip,
) -> str:
    """
    Dedent literal structure, then render its opaque holes in one linear pass.

    Raises:
        RuntimeError: If hole metadata is inconsistent with the literal framework.

    Returns:
        The dedented, rendered, and stripped string.
    """
    if len(literals) != len(holes) + 1:
        message = "literal and hole counts are inconsistent"
        raise RuntimeError(message)

    if not holes:
        return _strip_string(_dedent_string(literals[0]), strip)

    marker_id = uuid4().hex
    framework_parts = [literals[0]]

    for index, literal in enumerate(literals[1:]):
        token = f"{_SEP}{_HOLE_MARKER_PREFIX}:{marker_id}:{index}{_SEP}"
        framework_parts.extend((token, literal))

    framework = _dedent_string("".join(framework_parts))
    hole_marker = re.compile(rf"{_SEP}{_HOLE_MARKER_PREFIX}:{marker_id}:(\d+){_SEP}")
    dedented_literals: list[str] = []
    last_end = 0

    for match in hole_marker.finditer(framework):
        if int(match.group(1)) != len(dedented_literals):
            message = "dedent hole markers are out of order"
            raise RuntimeError(message)
        dedented_literals.append(framework[last_end : match.start()])
        last_end = match.end()

    dedented_literals.append(framework[last_end:])
    return _strip_string(_fill_parts(dedented_literals, holes, render), strip)


def _dedent_marked_string(string: str, strip: Strip) -> str:
    """
    Dedent static text without letting aligned values affect its indentation.

    Returns:
        The dedented string with deferred values restored and aligned.
    """
    literals, values = _split_align_markers(string)
    return _dedent_and_fill(literals, values, _render_align_marker, strip)


if sys.version_info >= (3, 14):
    from string.templatelib import Interpolation, Template, convert
    from typing import LiteralString

    def _partition(
        it: Iterable[_T], pred: Callable[[_T], bool]
    ) -> tuple[filter[_T], filterfalse[_T]]:
        """
        Partition an iterable into two filters based on a predicate.

        Args:
            it: The iterable to partition.
            pred: A function that returns True for items in the first partition.

        Returns:
            A tuple of (matching_filter, non_matching_filter) where matching_filter contains items
            for which predicate returns True, and non_matching_filter contains items for which
            predicate returns False.
        """
        it1, it2 = tee(it)
        return filter(pred, it1), filterfalse(pred, it2)

    def _parse_format_spec(format_spec: str) -> tuple[str, bool | None]:
        """
        Parse format spec to extract alignment-specific directives.

        Extracts 'align' and 'noalign' directives from the format spec and returns the remaining
        format spec along with the alignment override.

        Args:
            format_spec: The format specification string, potentially containing alignment
                directives separated by colons.

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
        item: Interpolation[object],
        *,
        preceding_text: str,
        align: bool,
    ) -> str:
        """
        Convert and format one interpolation, then apply requested alignment.

        Args:
            item: The interpolation to render.
            preceding_text: The text that precedes this item, used for alignment.
            align: Whether to align multiline values by default (can be overridden by format spec
                directives).

        Returns:
            The processed string representation of the item.
        """
        value = convert(item.value, item.conversion)
        align_override: bool | None = None

        if item.format_spec:
            format_spec, align_override = _parse_format_spec(item.format_spec)
            if format_spec:
                value = format(value, format_spec)

        value = str(value)
        should_align = align_override if align_override is not None else align
        if _ALIGN_MARKER.search(value):
            return process_align_markers(value, preceding_text=preceding_text)
        if should_align:
            value = _align_value(value, preceding_text)

        return value

    def _dedent_template(template: Template, *, align: bool, strip: Strip) -> str:
        """
        Dedent template literals before rendering their interpolations.

        Returns:
            The dedented and rendered template.
        """
        interpolations: list[Interpolation[object]] = []
        literals = [""]

        for item in template:
            if isinstance(item, str):
                literals[-1] += item
                continue

            interpolations.append(item)
            literals.append("")

        def render_interpolation(item: Interpolation[object], preceding_text: str) -> str:
            return _handle_item(item, preceding_text=preceding_text, align=align)

        return _dedent_and_fill(literals, interpolations, render_interpolation, strip)

    def dedent(  # pyright: ignore[reportUnreachable]
        string: Template | LiteralString,
        /,
        *,
        align: bool | Missing = MISSING,
        strip: Strip | Missing = MISSING,
    ) -> str:
        r'''
        Dedent, strip, and align a template string.

        This function removes the longest exact indentation prefix shared by all nonblank lines,
        preserving relative indentation. A final whitespace-only line constrains the prefix like
        the closing-quotes line in PEP 822. It supports both literal strings and t-strings
        (`Template` objects) with interpolations.

        For t-strings, interpolated values can include format spec directives:
        - `{value:align}` - Enable alignment for this value
        - `{value:noalign}` - Disable alignment for this value
        - `{value:align:06d}` - Combine alignment directive with other format specs

        Args:
            string: Template or literal string to dedent.
            align: Whether multiline interpolated values start each line in the column where the
                interpolation begins. Defaults to False. Can be overridden per value using format
                spec directives.
            strip: Stripping mode to use.
                - "smart" (default): Strips one leading and trailing newline-bounded blank segment.
                - "all": Strips all surrounding whitespace.
                - "none": Leaves whitespace exactly as-is after dedenting.

        Raises:
            IndentationError: If a line is incompatible with the common indentation prefix.
            TypeError: If the input is not a string or Template object.

        Returns:
            The dedented string with common leading whitespace removed, stripped according to
            the `strip` mode.

        Example::

            >>> from dedent import dedent
            >>> result = dedent(t"""
            ...     Hello, {"World"}!
            ...     """)
            >>> print(result)
            Hello, World!
        '''  # ruff: ignore[docstring-extraneous-exception]
        align = align if not isinstance(align, Missing) else DEFAULT_ALIGN
        strip = strip if not isinstance(strip, Missing) else DEFAULT_STRIP

        match string:
            case str() as formatted_string:
                return _dedent_marked_string(formatted_string, strip)
            case Template() as template:
                return _dedent_template(template, align=align, strip=strip)
            case unknown if not TYPE_CHECKING:  # pyright: ignore[reportUnnecessaryComparison]
                message = f"expected str or Template, not {type(unknown).__qualname__!r}"  # pyright: ignore[reportUnreachable]
                raise TypeError(message)

else:

    def dedent(  # pyright: ignore[reportUnreachable]
        string: str,
        /,
        *,
        strip: Strip | Missing = MISSING,
    ) -> str:
        r'''
        Dedent and strip a string, with optional multiline-value alignment.

        This function removes the longest exact indentation prefix shared by all nonblank lines,
        preserving relative indentation. A final whitespace-only line constrains the prefix like
        the closing-quotes line in PEP 822. Use `align()` to mark interpolated values for automatic
        indentation alignment inside f-strings.

        Args:
            string: String to dedent.
            strip: Stripping mode to use.
                - "smart" (default): Strips one leading and trailing newline-bounded blank segment.
                - "all": Strips all surrounding whitespace.
                - "none": Leaves whitespace exactly as-is after dedenting.

        Raises:
            IndentationError: If a line is incompatible with the common indentation prefix.
            TypeError: If the input is not a string.

        Returns:
            The dedented string with common leading whitespace removed.

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
        strip = strip if not isinstance(strip, Missing) else DEFAULT_STRIP

        if not isinstance(string, str):  # pyright: ignore[reportUnnecessaryIsInstance]
            message = f"expected str, not {type(string).__qualname__!r}"
            raise TypeError(message)  # pyright: ignore[reportUnreachable]

        return _dedent_marked_string(string, strip)
