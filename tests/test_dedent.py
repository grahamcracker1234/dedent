"""
Test functionality.

Adapted from https://github.com/dmnd/dedent/blob/7b38d9/src/dedent.test.ts
"""

from typing import TYPE_CHECKING, Final

import pytest

from dedent import align, dedent
from dedent._dedent import MISSING, AlignSpec, Missing, Strip  # noqa: PLC2701

if TYPE_CHECKING:
    from _pytest.fixtures import SubRequest
    from syrupy.assertion import SnapshotAssertion

    type StripOption = Strip | Missing
    type AlignOption = bool | Missing


STRIP_OPTIONS: Final[list[StripOption]] = [MISSING, "smart", "all", "none"]
ALIGN_OPTIONS: Final[list[AlignOption]] = [MISSING, False, True]


class TestDedent:
    @staticmethod
    def test_works_without_interpolation(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""first
            second
            third
        """)

    @staticmethod
    def test_works_with_interpolation(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t"""first {"line"}
            {"second"}
            third
        """)

    @staticmethod
    def test_works_with_suppressed_newlines(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t"""first \
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

    @staticmethod
    def test_works_with_multiple_blank_first_lines(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t"""

            first
            second
            third
        """)

    @staticmethod
    def test_works_with_removing_same_number_of_spaces(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t"""
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

    @staticmethod
    def test_format_spec(snapshot: SnapshotAssertion) -> None:
        total = 123
        discount = 0.123456789
        header = "Receipt"
        decimals = 2
        assert snapshot == dedent(t"""
            {header:=^21}
            - Total: {total: 9d}
            - Discount: {discount: 9.{decimals}%}
        """)

    @staticmethod
    def test_empty_format_spec(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t"{123:}")


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


class TestAlign:
    @pytest.fixture(scope="class", params=ALIGN_OPTIONS)
    @staticmethod
    def align(request: SubRequest) -> AlignOption:
        return request.param  # pyright: ignore[reportAny]: bad pytest typing

    @pytest.fixture(scope="class", params=[align.value for align in AlignSpec])
    @staticmethod
    def spec(request: SubRequest) -> str:
        return request.param  # pyright: ignore[reportAny]: bad pytest typing

    @staticmethod
    def test_with_multiple_lines(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        items = dedent("""
            - apples
            - bananas
            - cherries
        """)

        assert snapshot == dedent(
            t"""
            List:
                {items}
            ---
            """,
            align=align,
        )

    @staticmethod
    def test_with_single_line(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        assert snapshot == dedent(
            t"""
            List:
                {"- apples"}
            ---
            """,
            align=align,
        )

    @staticmethod
    def test_no_indentation(snapshot: SnapshotAssertion, align: AlignOption) -> None:
        items = dedent("""
            - apples
            - bananas
            - cherries
        """)
        assert snapshot == dedent(t"{items}", align=align)

    @staticmethod
    def test_override(snapshot: SnapshotAssertion, align: AlignOption, spec: str) -> None:
        items = dedent("""
            - apples
            - bananas
            - cherries
        """)
        assert snapshot == dedent(
            t"""
            List:
                {items:{spec}}
            ---
            """,
            align=align,
        )

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
            t"""
            List:
                {items:\n^{size}:{spec}}
                {items:{spec}:\n^{size}}
            ---
            """,
            align=align,
        )

    @staticmethod
    def test_unknown_format_spec() -> None:
        with pytest.raises(ValueError, match=r"(?i)invalid format spec"):
            _ = dedent(t"{123:algn}")  # misspelled "align"


class TestTyping:
    @staticmethod
    def test_literal(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent("""
            first
            second
            third
        """)

    @staticmethod
    def test_template(snapshot: SnapshotAssertion) -> None:
        assert snapshot == dedent(t"""
            {"first"}
            {"second"}
            {"third"}
        """)

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


class TestAlignWithTStrings:
    """Test that align() works alongside t-string dedent on Python 3.14+."""

    @staticmethod
    def test_align_wrapper_in_fstring_with_tstring_dedent() -> None:
        items = dedent("""
            - apples
            - bananas
        """)
        result = dedent(f"""
            Groceries:
                {align(items)}
            ---
        """)  # pyright: ignore[reportArgumentType]
        assert result == "Groceries:\n    - apples\n    - bananas\n---"

    @staticmethod
    def test_tstring_align_spec_still_works(snapshot: SnapshotAssertion) -> None:
        items = dedent("""
            - apples
            - bananas
        """)
        assert snapshot == dedent(
            t"""
            List:
                {items:align}
            ---
            """,
        )

    @staticmethod
    def test_align_markers_processed_in_str_branch() -> None:
        items = dedent("""
            - one
            - two
        """)
        # Plain string (f-string) goes through str() branch even on 3.14
        result = dedent(f"""
            A:
                {align(items)}
            B:
                {align(items)}
        """)  # pyright: ignore[reportArgumentType]
        assert "\x00" not in result
        assert result == "A:\n    - one\n    - two\nB:\n    - one\n    - two"
