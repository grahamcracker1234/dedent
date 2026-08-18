"""Tests for `dedent`."""

import sys
from typing import cast

import pytest
from inline_snapshot import snapshot

from dedent import align, dedent

required_py314 = pytest.mark.skipif(sys.version_info < (3, 14), reason="requires Python 3.14+")

if sys.version_info >= (3, 14):
    from string.templatelib import Template

    _T = Template
else:
    _T = str

ITEMS = "- apples\n- bananas\n- cherries"
TYPICAL = """
    foo
    bar
    """


def t(source: str, /, **ns: object) -> _T:
    code = compile(f"t'''{source}'''", "<t-string>", "eval")
    return cast("_T", eval(code, ns))  # ruff: ignore[suspicious-eval-usage]


def dedent_f(string: str) -> str:
    """Call `dedent` on an interpolated f-string (not `LiteralString` on 3.14+)."""
    return dedent(string)  # pyright: ignore[reportArgumentType]


class TestDedent:
    @staticmethod
    def test_uses_exact_common_indentation_prefix() -> None:
        assert dedent(" \tfirst\n \t\tsecond") == snapshot("""\
first
	second\
""")
        assert dedent(" first\n\tsecond") == snapshot("""\
 first
	second\
""")

    @staticmethod
    def test_closing_line_constrains_indentation() -> None:
        assert dedent("\n    first\n  ") == snapshot("  first\n")
        assert dedent("\n    first\n    ") == snapshot("first\n")

    @staticmethod
    def test_column_zero_closer_preserves_indentation() -> None:
        assert dedent("\n    first\n    second\n") == snapshot("""\
    first
    second
""")
        assert dedent("\n    first\n    second") == snapshot("""\
first
second\
""")

    @staticmethod
    def test_ignores_compatible_whitespace_only_lines() -> None:
        assert dedent("\n  first\n \n  second\n  ") == snapshot("""\
first

second
""")

    @staticmethod
    def test_preserves_crlf_when_ignoring_blank_lines() -> None:
        assert dedent("    first\r\n\r\n    second\r\n    ") == snapshot("first\r\n\r\nsecond\r\n")

    @staticmethod
    def test_preserves_complete_crlf_boundary() -> None:
        assert dedent("\r\n    first\r\n    ") == snapshot("first\r\n")

    @pytest.mark.parametrize("whitespace", ["\f", "\v", "\N{NO-BREAK SPACE}"])
    @staticmethod
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
    @staticmethod
    def test_rejects_incompatible_whitespace_only_lines(string: str) -> None:
        with pytest.raises(IndentationError, match="line 3"):
            _ = dedent_f(string)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def test_tabs() -> None:
        assert dedent("\n\t\tfirst\n\t\t\tsecond\n\t\t\t\tthird\n\t\t") == snapshot("""\
first
	second
		third
""")

    @staticmethod
    def test_empty() -> None:
        assert dedent("") == snapshot("")

    @staticmethod
    def test_single_line() -> None:
        assert dedent("A single line of input.") == snapshot("A single line of input.")

    @staticmethod
    def test_escaped_newlines_are_literal() -> None:
        assert dedent("\\n\\tfirst\\n") == snapshot("\\n\\tfirst\\n")

    @staticmethod
    def test_explicit_newline_is_kept() -> None:
        assert dedent("""
                <p>Hello world!</p>\n
                """) == snapshot("""\
<p>Hello world!</p>

""")

    @staticmethod
    def test_source_line_continuation() -> None:
        assert dedent("""
                first \
                second
                third
                """) == snapshot("""\
first                 second
third
""")

    @staticmethod
    def test_unicode() -> None:
        assert dedent("    😊 弟気") == snapshot("😊 弟気")

    @staticmethod
    def test_rejects_non_string() -> None:
        with pytest.raises(TypeError, match="expected str"):
            _ = dedent(123)  # pyright: ignore[reportArgumentType]


class TestBoundaries:
    @staticmethod
    def test_closing_quotes_on_own_line_preserve_trailing_newline() -> None:
        assert dedent(TYPICAL) == snapshot("foo\nbar\n")

    @staticmethod
    def test_closing_quotes_after_content_omit_trailing_newline() -> None:
        assert dedent("""
                foo
                bar""") == snapshot("foo\nbar")

    @staticmethod
    def test_omits_only_opening_newline() -> None:
        assert dedent("""


                foo
                bar
                """) == snapshot("""\


foo
bar
""")

    @staticmethod
    def test_keeps_trailing_spaces_on_content() -> None:
        assert dedent(
            """
                    foo---
                    bar---
                    """.replace("-", " ")
        ) == snapshot("""\
foo   \n\
bar   \n\
""")

    @staticmethod
    def test_keeps_whitespace_only_lines() -> None:
        assert dedent(
            """
                    ---
                    foo
                    bar
                    ---
                    """.replace("-", " ")
        ) == snapshot("""\
   \n\
foo
bar
   \n\
""")


class TestInterpolation:
    @staticmethod
    def test_fstring() -> None:
        line = "line"
        assert dedent(f"""
                first {line}
                second
                """) == snapshot("""\
first line
second
""")

    @required_py314
    @staticmethod
    def test_tstring() -> None:
        assert dedent(
            t("""
                first {"line"}
                second
                """)
        ) == snapshot("""\
first line
second
""")

    @required_py314
    @staticmethod
    def test_tstring_format_spec() -> None:
        template_result = dedent(
            t(
                """
                {header:=^21}
                - Total: {total: 9d}
                """,
                header="Receipt",
                total=123,
            )
        )
        fstring_result = dedent_f(f"""
                {"Receipt":=^21}
                - Total: {123: 9d}
                """)
        assert (
            template_result
            == fstring_result
            == snapshot("""\
=======Receipt=======
- Total:       123
""")
        )

    @required_py314
    @staticmethod
    def test_tstring_empty_format_spec() -> None:
        assert dedent(t("{123:}")) == dedent_f(f"{123:}") == snapshot("123")


class TestAlign:
    @staticmethod
    def test_unaligned_multiline_value() -> None:
        # Column-0 lines from interpolation prevent a common indent prefix.
        assert dedent_f(f"\n    List:\n        {ITEMS}\n    ---\n    ") == snapshot("""\
    List:
        - apples
- bananas
- cherries
    ---
    \
""")

    @staticmethod
    def test_align_wrapper() -> None:
        items = dedent("""
            - apples
            - bananas""")
        assert dedent_f(f"""
                Groceries:
                    {align(items)}
                ---
                """) == snapshot("""\
Groceries:
    - apples
    - bananas
---
""")

    @staticmethod
    def test_two_values() -> None:
        a = "line1\nline2"
        b = "foo\nbar"
        assert dedent_f(f"""
                A:
                    {align(a)}
                B:
                    {align(b)}
                """) == snapshot("""\
A:
    line1
    line2
B:
    foo
    bar
""")

    @staticmethod
    def test_two_values_on_the_same_line() -> None:
        a = "a1\na2"
        b = "b1\nb2"
        assert dedent_f(f"""
                Row:
                    {align(a)} + {align(b)}
                """) == snapshot("""\
Row:
    a1
    a2 + b1
         b2
""")

    @staticmethod
    def test_nested_wrappers() -> None:
        inner = "line1\nline2"
        outer = f"outer {align(inner)}"
        result = dedent_f(f"  {align(outer)}")
        assert result == snapshot("""\
outer line1
      line2\
""")
        assert "\x00" not in result
        assert "DEDENT_ALIGN" not in result

    @staticmethod
    def test_alignment_uses_interpolation_column_with_non_space_prefix() -> None:
        value = "line1\nline2"
        string = f"\N{NO-BREAK SPACE}{align(value)}"
        assert (
            dedent(string)  # pyright: ignore[reportArgumentType]: runtime contract
            == snapshot("\N{NO-BREAK SPACE}line1\n line2")
        )

    @staticmethod
    def test_conversions() -> None:
        assert dedent_f(f"""
                List:
                    {align(ITEMS)!s}
                """) == snapshot("""\
List:
    - apples
    - bananas
    - cherries
""")
        assert dedent_f(f"""
                Value:
                    {align("hello")!r}
                """) == snapshot("""\
Value:
    'hello'
""")
        assert dedent_f(f"""
                Value:
                    {align(1.23456):.2f}
                """) == snapshot("""\
Value:
    1.23
""")
        assert dedent_f(f"""
                Header:
                    {align("hi"):>10}
                """) == snapshot("""\
Header:
            hi
""")

    @required_py314
    @staticmethod
    def test_tstring_aligns_by_default() -> None:
        assert dedent(
            t(
                """
                    List:
                        {items}
                    ---
                    """,
                items=ITEMS,
            )
        ) == snapshot("""\
List:
    - apples
    - bananas
    - cherries
---
""")

    @required_py314
    @staticmethod
    def test_noalign_disables_alignment() -> None:
        assert dedent(
            t(
                """
                    List:
                        {items:noalign}
                    ---
                    """,
                items=ITEMS,
            )
        ) == snapshot("""\
List:
    - apples
- bananas
- cherries
---
""")

    @required_py314
    @staticmethod
    def test_align_wrapper_is_not_applied_twice() -> None:
        assert dedent(
            t(
                """
                    List:
                        {items}
                    ---
                    """,
                items=align(ITEMS),
            )
        ) == snapshot("""\
List:
    - apples
    - bananas
    - cherries
---
""")

    @required_py314
    @staticmethod
    def test_noalign_directive_with_format_spec() -> None:
        assert dedent(t("{123:06d:noalign}")) == snapshot("000123")
        assert dedent(t("{123:noalign:06d}")) == snapshot("000123")

    @required_py314
    @staticmethod
    def test_alignment_after_multiline_formatting() -> None:
        size = len(ITEMS) + 2
        assert dedent(
            t(
                """
                List:
                    {items:\n^{size}}
                ---
                """,
                items=ITEMS,
                size=size,
            )
        ) == snapshot("""\
List:
    \n\
    - apples
    - bananas
    - cherries
    \n\
---
""")
        assert dedent(
            t(
                """
                List:
                    {items:\n^{size}:noalign}
                ---
                """,
                items=ITEMS,
                size=size,
            )
        ) == snapshot("""\
List:
    \n\
- apples
- bananas
- cherries

---
""")

    @required_py314
    @staticmethod
    def test_align_format_spec_is_not_supported() -> None:
        with pytest.raises(ValueError, match=r"(?i)invalid format spec"):
            _ = dedent(t("{123:align}"))

    @staticmethod
    def test_wrapper_embeds_markers() -> None:
        text = str(align("hello"))
        assert "hello" in text
        assert "\x00" in text
        assert repr("hello") in repr(align("hello"))
        assert "1.2" in format(align(1.23), ".1f")
        assert "\x00" in format(align(1.23), ".1f")
