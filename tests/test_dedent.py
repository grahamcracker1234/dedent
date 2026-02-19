"""
Test functionality.

Adapted from https://github.com/dmnd/dedent/blob/7b38d9/src/dedent.test.ts
"""
# ruff: noqa: PLC2701
# pyright: reportPrivateUsage=false

import sys
from collections.abc import Callable
from typing import Final, cast

import pytest
from _pytest.fixtures import SubRequest
from syrupy.assertion import SnapshotAssertion

from dedent import align as align_values
from dedent import dedent
from dedent._dedent import _ALIGN_MARKER_PREFIX, _SEP, MISSING, AlignSpec, Missing, Strip

StripOption = Strip | Missing
AlignOption = bool | Missing

STRIP_OPTIONS: Final[list[StripOption]] = [MISSING, "smart", "all", "none"]
ALIGN_OPTIONS: Final[list[AlignOption]] = [MISSING, False, True]

required_py314 = pytest.mark.skipif(sys.version_info < (3, 14), reason="requires Python 3.14+")

if sys.version_info >= (3, 14):
    from string.templatelib import Template

    _T = Template
else:
    _T = str


def t(source: str, /, **ns: object) -> _T:
    code = compile(f"t'''{source}'''", "<t-string>", "eval")
    return cast("_T", eval(code, ns))  # noqa: S307


class TestDedent:
    @staticmethod
    def test_works_without_interpolation(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""first
            second
            third
        """)

    @required_py314
    @staticmethod
    def test_works_with_interpolation(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t("""first {"line"}
            {"second"}
            third
        """))  # fmt: skip

    @staticmethod
    def test_works_with_interpolation_legacy(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(f"""first {"line"}
            {"second"}
            third
        """)

    @required_py314
    @staticmethod
    def test_works_with_suppressed_newlines(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t("""first \
            {"second"}
            third
        """))  # fmt: skip

    @staticmethod
    def test_works_with_suppressed_newlines_legacy(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(f"""first \
            {"second"}
            third
        """)

    @staticmethod
    def test_works_with_blank_first_line(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""
            Some text that I might want to indent:
                * reasons
                * fun
            That's all.
        """)

    @required_py314
    @staticmethod
    def test_works_with_multiple_blank_first_lines(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t("""

            first
            second
            third
        """))  # fmt: skip

    @staticmethod
    def test_works_with_multiple_blank_first_lines_legacy(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""

            first
            second
            third
        """)

    @required_py314
    @staticmethod
    def test_works_with_removing_same_number_of_spaces(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t("""
           first
                second
                      third
        """))  # fmt: skip

    @staticmethod
    def test_works_with_removing_same_number_of_spaces_legacy(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""
           first
                second
                      third
        """)

    @staticmethod
    def test_does_not_strip_explicit_newlines(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""
            <p>Hello world!</p>\n
        """)

    @staticmethod
    def test_does_not_strip_explicit_newlines_with_min_indent(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""
            <p>
                Hello world!
            </p>\n
        """)

    @staticmethod
    def test_works_with_spaces_for_indentation(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""
            first
                second
                    third
        """)

    @staticmethod
    def test_works_with_tabs_for_indentation(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""
			first
				second
					third
        """)

    @staticmethod
    def test_works_with_explicit_tabs_for_indentation(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("\n\t\tfirst\n\t\t\tsecond\n\t\t\t\tthird\n")

    @staticmethod
    def test_escaped_explicit_newlines_and_tabs(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("\\n\\tfirst\\n")

    @required_py314
    @staticmethod
    def test_format_spec(snapshot: SnapshotAssertion) -> None:
        header = "Receipt"
        total = 123
        discount = 0.123456789
        decimals = 2
        assert snapshot == dedent(t("""
            {header:=^21}
            - Total: {total: 9d}
            - Discount: {discount: 9.{decimals}%}
        """, header=header, total=total, discount=discount, decimals=decimals))  # fmt: skip

    @staticmethod
    def test_format_spec_legacy(snapshot: SnapshotAssertion) -> None:
        header = "Receipt"
        total = 123
        discount = 0.123456789
        decimals = 2
        assert snapshot == dedent(f"""
            {header:=^21}
            - Total: {total: 9d}
            - Discount: {discount: 9.{decimals}%}
        """)  # pyright: ignore[reportArgumentType]

    @required_py314
    @staticmethod
    def test_empty_format_spec(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t("{123:}"))

    @staticmethod
    def test_empty_format_spec_legacy(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(f"{123:}")  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("strip", STRIP_OPTIONS)
class TestStrip:
    @staticmethod
    def test_with_trailing_whitespace(snapshot: SnapshotAssertion, strip: StripOption) -> None:
        assert snapshot == dedent(
            """
            foo---
            bar---
            """.replace("-", " "),
            strip=strip,
        )

    @staticmethod
    def test_without_trailing_whitespace(snapshot: SnapshotAssertion, strip: StripOption) -> None:
        assert snapshot == dedent(
            """
            foo
            bar
            """,
            strip=strip,
        )

    @staticmethod
    def test_with_leading_whitespace(snapshot: SnapshotAssertion, strip: StripOption) -> None:
        assert snapshot == dedent(
            """


            foo
            bar
            """.replace("-", " "),
            strip=strip,
        )

    @staticmethod
    def test_with_special_whitespace(snapshot: SnapshotAssertion, strip: StripOption) -> None:
        assert snapshot == dedent(
            """---

            foo
            bar

            ---""".replace("-", " "),
            strip=strip,
        )

    @staticmethod
    def test_with_inverse_special_whitespace(
        snapshot: SnapshotAssertion, strip: StripOption
    ) -> None:
        assert snapshot == dedent(
            """
            ---
            foo
            bar
            ---
            """.replace("-", " "),
            strip=strip,
        )


class TestAlign:  # noqa: PLR0904
    @pytest.fixture(scope="class", params=ALIGN_OPTIONS)
    @staticmethod
    def align(request: SubRequest) -> AlignOption:
        return request.param  # pyright: ignore[reportAny]: bad pytest typing

    @pytest.fixture(scope="class", params=[align.value for align in AlignSpec])
    @staticmethod
    def spec(request: SubRequest) -> str:
        return request.param  # pyright: ignore[reportAny]: bad pytest typing

    @staticmethod
    def align_to_fn(align: AlignOption) -> Callable[..., object]:
        def identity(value: object) -> object:
            return value

        return align_values if isinstance(align, bool) and align else identity

    @required_py314
    @staticmethod
    def test_with_multiple_lines(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        items = dedent("""
            - apples
            - bananas
            - cherries
        """)

        assert snapshot == dedent(
            t("""
            List:
                {items}
            ---
            """, items=items),
            align=align,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    def test_with_multiple_lines_legacy(
        self, snapshot: SnapshotAssertion, align: AlignOption
    ) -> None:
        align_fn = self.align_to_fn(align)

        items = dedent("""
            - apples
            - bananas
            - cherries
        """)

        assert snapshot == dedent(
            f"""
            List:
                {align_fn(items)}
            ---
            """,  # pyright: ignore[reportArgumentType]: matrix type checking
        )

    @required_py314
    @staticmethod
    def test_with_single_line(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        assert snapshot == dedent(
            t("""
            List:
                {"- apples"}
            ---
            """),
            align=align,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    def test_with_single_line_legacy(self, snapshot: SnapshotAssertion, align: AlignOption) -> None:
        align_fn = self.align_to_fn(align)

        assert snapshot == dedent(
            f"""
            List:
                {align_fn("- apples")}
            ---
            """,  # pyright: ignore[reportArgumentType]: matrix type checking
        )

    @required_py314
    @staticmethod
    def test_no_indentation(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        items = dedent("""
            - apples
            - bananas
            - cherries
        """)
        assert snapshot == dedent(t("{items}", items=items), align=align)  # pyright: ignore[reportCallIssue]: matrix type checking

    def test_no_indentation_legacy(self, snapshot: SnapshotAssertion, align: AlignOption) -> None:
        align_fn = self.align_to_fn(align)

        items = dedent("""
            - apples
            - bananas
            - cherries
        """)
        assert snapshot == dedent(f"{align_fn(items)}")  # pyright: ignore[reportArgumentType]: matrix type checking

    @required_py314
    @staticmethod
    def test_override(snapshot: SnapshotAssertion, align: AlignOption, spec: str) -> None:
        items = dedent("""
            - apples
            - bananas
            - cherries
        """)
        assert snapshot == dedent(
            t("""
            List:
                {items:{spec}}
            ---
            """, items=items, spec=spec),
            align=align,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    @required_py314
    @staticmethod
    def test_override_with_format_spec(
        snapshot: SnapshotAssertion, align: AlignOption, spec: str
    ) -> None:
        if isinstance(align, Missing):
            return

        items = dedent("""
            - apples
            - bananas
            - cherries
        """)
        size = len(items) + 2

        assert snapshot == dedent(
            t("""
            List:
                {items:\n^{size}:{spec}}
                {items:{spec}:\n^{size}}
            ---
            """, items=items, spec=spec, size=size),
            align=align,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    @required_py314
    @staticmethod
    def test_unknown_format_spec() -> None:
        with pytest.raises(ValueError, match=r"(?i)invalid format spec"):
            _ = dedent(t("{123:algn}"))  # misspelled "align"

    @required_py314
    @staticmethod
    def test_empty_string(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        assert snapshot == dedent("", align=align)  # pyright: ignore[reportArgumentType,reportCallIssue]: matrix type checking

    def test_empty_string_legacy(self, snapshot: SnapshotAssertion, align: AlignOption) -> None:
        align_fn = self.align_to_fn(align)

        assert snapshot == dedent(f"{align_fn('')}")  # pyright: ignore[reportArgumentType]: matrix type checking

    @required_py314
    @staticmethod
    def test_two_aligned_values(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        a = "line1\nline2"
        b = "foo\nbar"
        assert snapshot == dedent(
            t("""
            A:
                {a}
            B:
                {b}
            """, a=a, b=b),
            align=align,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    def test_two_aligned_values_legacy(
        self, snapshot: SnapshotAssertion, align: AlignOption
    ) -> None:
        align_fn = self.align_to_fn(align)
        a = "line1\nline2"
        b = "foo\nbar"
        assert snapshot == dedent(f"""
            A:
                {align_fn(a)}
            B:
                {align_fn(b)}
        """)  # pyright: ignore[reportArgumentType]: matrix type checking

    @required_py314
    @staticmethod
    def test_aligned_and_plain(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        items = "- apples\n- bananas"
        plain = "hello"
        assert snapshot == dedent(
            t("""
            List:
                {items}
            Plain:
                {plain}
            """, items=items, plain=plain),
            align=align,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    def test_aligned_and_plain_legacy(
        self, snapshot: SnapshotAssertion, align: AlignOption
    ) -> None:
        align_fn = self.align_to_fn(align)
        items = "- apples\n- bananas"
        plain = "hello"
        assert snapshot == dedent(f"""
            List:
                {align_fn(items)}
            Plain:
                {plain}
        """)  # pyright: ignore[reportArgumentType]: matrix type checking

    @required_py314
    @staticmethod
    def test_str_conversion(snapshot: SnapshotAssertion) -> None:
        items = "- apples\n- bananas"
        assert snapshot == dedent(
            t("""
            List:
                {items!s}
            """, items=items),
            align=True,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    @staticmethod
    def test_str_conversion_legacy(snapshot: SnapshotAssertion) -> None:
        items = "- apples\n- bananas"
        assert snapshot == dedent(f"""
            List:
                {align_values(items)!s}
        """)  # pyright: ignore[reportArgumentType]: matrix type checking

    @required_py314
    @staticmethod
    def test_repr_conversion(snapshot: SnapshotAssertion) -> None:
        value = "hello"
        assert snapshot == dedent(
            t("""
            Value:
                {value!r}
            """, value=value),
            align=True,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    @staticmethod
    def test_repr_conversion_legacy(snapshot: SnapshotAssertion) -> None:
        value = "hello"
        assert snapshot == dedent(f"""
            Value:
                {align_values(value)!r}
        """)  # pyright: ignore[reportArgumentType]: matrix type checking

    @required_py314
    @staticmethod
    def test_numeric_format(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t("""
            Value:
                {1.23456:.2f}
        """),
            align=True,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    @staticmethod
    def test_numeric_format_legacy(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(f"""
            Value:
                {align_values(1.23456):.2f}
        """)  # pyright: ignore[reportArgumentType]: matrix type checking

    @required_py314
    @staticmethod
    def test_string_format(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(
            t("""
            Header:
                {"hi":>10}
            """),
            align=True,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip

    @staticmethod
    def test_string_format_legacy(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(f"""
            Header:
                {align_values("hi"):>10}
        """)  # pyright: ignore[reportArgumentType]: matrix type checking

    @required_py314
    @staticmethod
    def test_no_null_bytes_in_output() -> None:
        items = "- apples\n- bananas"
        result = dedent(  # pyright: ignore[reportUnknownVariableType]
            t("""
            List:
                {items}
            """, items=items),
            align=True,  # pyright: ignore[reportCallIssue]: matrix type checking
        )  # fmt: skip
        assert _SEP not in result

    @staticmethod
    def test_no_null_bytes_in_output_legacy() -> None:
        items = "- apples\n- bananas"
        result = dedent(f"""
            List:
                {align_values(items)}
        """)  # pyright: ignore[reportArgumentType,reportUnknownVariableType]: matrix type checking
        assert _SEP not in result

    @required_py314
    @staticmethod
    def test_no_markers_in_output() -> None:
        items = "- apples\n- bananas"
        result = dedent(  # pyright: ignore[reportUnknownVariableType]
            t("{items}", items=items),
            align=True,  # pyright: ignore[reportCallIssue]: matrix type checking
        )
        assert _ALIGN_MARKER_PREFIX not in result

    @staticmethod
    def test_no_markers_in_output_legacy() -> None:
        items = "- apples\n- bananas"
        result = dedent(f"{align_values(items)}")  # pyright: ignore[reportArgumentType,reportUnknownVariableType]: matrix type checking
        assert _ALIGN_MARKER_PREFIX not in result

    @staticmethod
    def test_aligned_str_contains_markers() -> None:
        hello = "hello"
        wrapper = align_values(hello)
        text = str(wrapper)
        assert _SEP in text
        assert hello in text

    @staticmethod
    def test_aligned_repr_contains_markers() -> None:
        hello = "hello"
        wrapper = align_values(hello)
        text = repr(wrapper)
        assert _SEP in text
        assert repr(hello) in text

    @staticmethod
    def test_aligned_format_contains_markers() -> None:
        value = 1.23
        wrapper = align_values(value)
        format_spec = ".1f"
        text = format(wrapper, format_spec)
        assert _SEP in text
        assert format(value, format_spec) in text


class TestTyping:
    @staticmethod
    def test_literal(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""
            first
            second
            third
        """)

    @required_py314
    @staticmethod
    def test_template(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t("""
            {"first"}
            {"second"}
            {"third"}
        """))  # fmt: skip

    @staticmethod
    def test_non_literal(snapshot: SnapshotAssertion) -> None:
        name = "python"
        assert snapshot == dedent(f"""
            hello
                {name}
        """)

        assert snapshot == dedent(f"""
            hello
                {123}
        """)  # pyright: ignore[reportArgumentType]: allow non-literal string for this test

        def wrapped(value: str) -> str:
            return dedent(f"""
                hello
                    {value}
            """)  # pyright: ignore[reportArgumentType]: allow non-literal string for this test

        assert snapshot == wrapped("python")

    @staticmethod
    def test_unsupported_type() -> None:
        """
        Test type checking for disallowing unsupported types.
        """
        with pytest.raises(TypeError):
            _ = dedent(123)  # pyright: ignore[reportArgumentType]: allow unsupported type for this test


class TestSingleLine:
    @staticmethod
    def test_works(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("A single line of input.")

    @staticmethod
    def test_works_with_quotes_on_newlines(
        snapshot: SnapshotAssertion,
    ) -> None:
        assert snapshot == dedent("""
            A single line of input.
        """)

    @staticmethod
    def test_works_with_opening_quotes_on_newline(
        snapshot: SnapshotAssertion,
    ) -> None:
        assert snapshot == dedent("""
            A single line of input.""")

    @staticmethod
    def test_works_with_closing_quotes_on_newline(
        snapshot: SnapshotAssertion,
    ) -> None:
        assert snapshot == dedent("""A single line of input.
            """)


class TestUnicodeCharacterPreservation:
    @staticmethod
    def test_preserves_emojis(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("😊")

    @staticmethod
    def test_preserves_ideographs(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("弟気")
