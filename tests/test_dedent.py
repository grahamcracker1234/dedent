"""Tests for `dedent`."""

import sys
from typing import Literal, cast

import pytest
from inline_snapshot import snapshot

from dedent import align, dedent

StripMode = Literal["smart", "all", "none"]

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
    return cast("_T", eval(code, ns))  # noqa: S307


def dedent_f(string: str) -> str:
    """Call `dedent` on an interpolated f-string (not `LiteralString` on 3.14+)."""
    return dedent(string)  # pyright: ignore[reportArgumentType]


class TestDedent:
    @staticmethod
    def test_uses_exact_common_indentation_prefix() -> None:
        assert dedent(" \tfirst\n \t\tsecond", strip="none") == snapshot("""\
first
	second\
""")
        assert dedent(" first\n\tsecond", strip="none") == snapshot("""\
 first
	second\
""")

    @staticmethod
    def test_closing_line_constrains_indentation() -> None:
        assert dedent("\n    first\n  ") == snapshot("  first")
        assert dedent("\n    first\n    ") == snapshot("first")

    @staticmethod
    def test_ignores_compatible_whitespace_only_lines() -> None:
        assert dedent("\n  first\n \n  second\n  ") == snapshot("""\
first

second\
""")

    @staticmethod
    def test_rejects_incompatible_whitespace_only_lines() -> None:
        with pytest.raises(IndentationError, match="line 3"):
            _ = dedent("\n  first\n \t\n  second\n  ")

    @staticmethod
    def test_removes_common_indent() -> None:
        assert dedent("""
                first
                    second
                        third
                """) == snapshot("""\
first
    second
        third\
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
           third\
""")

    @staticmethod
    def test_tabs() -> None:
        assert dedent("\n\t\tfirst\n\t\t\tsecond\n\t\t\t\tthird\n\t\t") == snapshot("""\
first
	second
		third\
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
                """) == snapshot("<p>Hello world!</p>\n")

    @staticmethod
    def test_source_line_continuation() -> None:
        assert dedent("""
                first \
                second
                third
                """) == snapshot("""\
first                 second
third\
""")

    @staticmethod
    def test_unicode() -> None:
        assert dedent("    😊 弟気") == snapshot("😊 弟気")

    @staticmethod
    def test_rejects_non_string() -> None:
        with pytest.raises(TypeError, match="expected str"):
            _ = dedent(123)  # pyright: ignore[reportArgumentType]


class TestStrip:
    @staticmethod
    def test_default_is_smart() -> None:
        assert dedent(TYPICAL) == dedent(TYPICAL, strip="smart")

    @pytest.mark.parametrize(
        ("strip", "expected"),
        [
            (
                "smart",
                snapshot("""\
foo
bar\
"""),
            ),
            (
                "all",
                snapshot("""\
foo
bar\
"""),
            ),
            (
                "none",
                snapshot("""\

foo
bar
"""),
            ),
        ],
    )
    @staticmethod
    def test_typical(strip: StripMode, expected: str) -> None:
        assert dedent(TYPICAL, strip=strip) == expected

    @staticmethod
    def test_smart_strips_one_blank_segment() -> None:
        assert dedent("""


                foo
                bar
                """) == snapshot("""\


foo
bar\
""")

    @staticmethod
    def test_smart_keeps_trailing_spaces_on_content() -> None:
        assert dedent(
            """
                    foo---
                    bar---
                    """.replace("-", " ")
        ) == snapshot("""\
foo   \n\
bar   \
""")

    @staticmethod
    def test_all_strips_surrounding_whitespace() -> None:
        padded = """---

            foo
            bar

            ---""".replace("-", " ")
        assert dedent(padded, strip="all") == snapshot("""\
foo
bar\
""")

    @staticmethod
    def test_smart_keeps_whitespace_only_lines() -> None:
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
   \
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
second\
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
second\
""")

    @required_py314
    @staticmethod
    def test_tstring_format_spec() -> None:
        assert dedent(
            t(
                """
                {header:=^21}
                - Total: {total: 9d}
                """,
                header="Receipt",
                total=123,
            )
        ) == snapshot("""\
=======Receipt=======
- Total:       123\
""")

    @required_py314
    @staticmethod
    def test_tstring_empty_format_spec() -> None:
        assert dedent(t("{123:}")) == snapshot("123")


class TestAlign:
    @staticmethod
    def test_unaligned_multiline_value() -> None:
        # Column-0 lines from interpolation prevent a common indent prefix.
        assert dedent_f(f"\n    List:\n        {ITEMS}\n    ---\n    ") == snapshot("""\
    List:
        - apples
- bananas
- cherries
    ---\
""")

    @staticmethod
    def test_align_wrapper() -> None:
        assert dedent_f(f"""
                List:
                    {align(ITEMS)}
                ---
                """) == snapshot("""\
List:
    - apples
    - bananas
    - cherries
---\
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
    bar\
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
    def test_conversions() -> None:
        assert dedent_f(f"""
                List:
                    {align(ITEMS)!s}
                """) == snapshot("""\
List:
    - apples
    - bananas
    - cherries\
""")
        assert dedent_f(f"""
                Value:
                    {align("hello")!r}
                """) == snapshot("""\
Value:
    'hello'\
""")
        assert dedent_f(f"""
                Value:
                    {align(1.23456):.2f}
                """) == snapshot("""\
Value:
    1.23\
""")
        assert dedent_f(f"""
                Header:
                    {align("hi"):>10}
                """) == snapshot("""\
Header:
            hi\
""")

    @required_py314
    @staticmethod
    def test_align_argument() -> None:
        assert dedent(
            t(
                """
                    List:
                        {items}
                    ---
                    """,
                items=ITEMS,
            ),
            align=True,  # pyright: ignore[reportCallIssue]: test is skipped before Python 3.14
        ) == snapshot("""\
List:
    - apples
    - bananas
    - cherries
---\
""")

    @required_py314
    @staticmethod
    def test_align_format_spec() -> None:
        assert dedent(
            t(
                """
                List:
                    {items:align}
                ---
                """,
                items=ITEMS,
            )
        ) == snapshot("""\
List:
    - apples
    - bananas
    - cherries
---\
""")

    @required_py314
    @staticmethod
    def test_noalign_overrides_align_argument() -> None:
        assert dedent(
            t(
                """
                    List:
                        {items:noalign}
                    ---
                    """,
                items=ITEMS,
            ),
            align=True,  # pyright: ignore[reportCallIssue]: test is skipped before Python 3.14
        ) == snapshot("""\
List:
    - apples
- bananas
- cherries
---\
""")

    @required_py314
    @staticmethod
    def test_align_directive_with_format_spec() -> None:
        assert dedent(t("{123:06d:align}")) == snapshot("000123")
        assert dedent(t("{123:align:06d}")) == snapshot("000123")

    @required_py314
    @staticmethod
    def test_unknown_format_spec() -> None:
        with pytest.raises(ValueError, match=r"(?i)invalid format spec"):
            _ = dedent(t("{123:algn}"))

    @staticmethod
    def test_wrapper_embeds_markers() -> None:
        text = str(align("hello"))
        assert "hello" in text
        assert "\x00" in text
        assert repr("hello") in repr(align("hello"))
        assert "1.2" in format(align(1.23), ".1f")
        assert "\x00" in format(align(1.23), ".1f")
