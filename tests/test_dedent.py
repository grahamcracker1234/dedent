import pytest
from inline_snapshot import snapshot

from dedent import dedent

from ._support import dedent_f


def test_uses_exact_common_indentation_prefix() -> None:
    assert dedent(" \tfirst\n \t\tsecond") == snapshot("""\
first
	second\
""")
    assert dedent(" first\n\tsecond") == snapshot("""\
 first
	second\
""")


def test_closing_line_constrains_indentation() -> None:
    assert dedent("\n    first\n  ") == snapshot("  first\n")
    assert dedent("\n    first\n    ") == snapshot("first\n")


def test_column_zero_closer_preserves_indentation() -> None:
    assert dedent("\n    first\n    second\n") == snapshot("""\
    first
    second
""")
    assert dedent("\n    first\n    second") == snapshot("""\
first
second\
""")


def test_ignores_compatible_whitespace_only_lines() -> None:
    assert dedent("\n  first\n \n  second\n  ") == snapshot("""\
first

second
""")


def test_preserves_crlf_when_ignoring_blank_lines() -> None:
    assert dedent("    first\r\n\r\n    second\r\n    ") == snapshot("first\r\n\r\nsecond\r\n")


def test_preserves_complete_crlf_boundary() -> None:
    assert dedent("\r\n    first\r\n    ") == snapshot("first\r\n")


@pytest.mark.parametrize("whitespace", ["\f", "\v", "\N{NO-BREAK SPACE}"])
def test_non_indentation_whitespace_is_content(whitespace: str) -> None:
    string = f"  first\n{whitespace}\n  second\n  "
    assert dedent(string) == string  # pyright: ignore[reportArgumentType]: runtime contract


@pytest.mark.parametrize(
    "string",
    [
        "\n  first\n \t\n  second\n  ",
        "\r\n  first\r\n \t\r\n  second\r\n  ",
    ],
)
def test_rejects_incompatible_whitespace_only_lines(string: str) -> None:
    with pytest.raises(IndentationError, match="line 3"):
        _ = dedent_f(string)


def test_removes_common_indent() -> None:
    assert dedent("""
            first
                second
                    third
            """) == snapshot("""\
first
    second
        third
""")


def test_min_indent_from_least_indented_line() -> None:
    assert dedent("""
           first
                second
                      third
           """) == snapshot("""\
first
     second
           third
""")


def test_tabs() -> None:
    assert dedent("\n\t\tfirst\n\t\t\tsecond\n\t\t\t\tthird\n\t\t") == snapshot("""\
first
	second
		third
""")


def test_empty() -> None:
    assert dedent("") == snapshot("")


def test_single_line() -> None:
    assert dedent("A single line of input.") == snapshot("A single line of input.")


def test_escaped_newlines_are_literal() -> None:
    assert dedent("\\n\\tfirst\\n") == snapshot("\\n\\tfirst\\n")


def test_explicit_newline_is_kept() -> None:
    assert dedent("""
            <p>Hello world!</p>\n
            """) == snapshot("""\
<p>Hello world!</p>

""")


def test_source_line_continuation() -> None:
    assert dedent("""
                first \
                second
                third
                """) == snapshot("""\
first                 second
third
""")


def test_unicode() -> None:
    assert dedent("    😊 弟気") == snapshot("😊 弟気")


def test_rejects_non_string() -> None:
    with pytest.raises(TypeError, match="expected str"):
        _ = dedent(123)  # pyright: ignore[reportArgumentType]
