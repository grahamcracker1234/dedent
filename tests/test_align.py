"""Tests for the align() f-string wrapper, compatible with Python 3.10+."""

# pyright: reportArgumentType=false
# All tests pass f-strings (non-LiteralString) to dedent(), which is intentional for align().

from __future__ import annotations

from dedent import align, dedent


class TestAlignBasic:
    @staticmethod
    def test_shopping_list_example() -> None:
        items = dedent("""
            - apples
            - bananas
        """)
        shopping_list = dedent(f"""
            Groceries:
                {align(items)}
            ---
        """)
        assert shopping_list == "Groceries:\n    - apples\n    - bananas\n---"

    @staticmethod
    def test_multiline_alignment() -> None:
        items = dedent("""
            - apples
            - bananas
            - cherries
        """)
        result = dedent(f"""
            List:
                {align(items)}
            ---
        """)
        assert result == "List:\n    - apples\n    - bananas\n    - cherries\n---"

    @staticmethod
    def test_single_line_value() -> None:
        result = dedent(f"""
            List:
                {align("- apples")}
            ---
        """)
        assert result == "List:\n    - apples\n---"

    @staticmethod
    def test_no_indentation_context() -> None:
        items = "- apples\n- bananas"
        result = dedent(f"{align(items)}")
        assert result == "- apples\n- bananas"

    @staticmethod
    def test_empty_string() -> None:
        result = dedent(f"""
            Prefix:
                {align("")}
            ---
        """)
        assert result == "Prefix:\n    \n---"


class TestAlignMultiple:
    @staticmethod
    def test_two_aligned_values() -> None:
        a = "line1\nline2"
        b = "foo\nbar"
        result = dedent(f"""
            A:
                {align(a)}
            B:
                {align(b)}
        """)
        assert result == "A:\n    line1\n    line2\nB:\n    foo\n    bar"

    @staticmethod
    def test_aligned_and_plain() -> None:
        items = "- apples\n- bananas"
        plain = "hello"
        result = dedent(f"""
            List:
                {align(items)}
            Plain:
                {plain}
        """)
        assert result == "List:\n    - apples\n    - bananas\nPlain:\n    hello"


class TestAlignConversion:
    @staticmethod
    def test_str_conversion() -> None:
        items = "- apples\n- bananas"
        result = dedent(f"""
            List:
                {align(items)!s}
        """)
        assert result == "List:\n    - apples\n    - bananas"

    @staticmethod
    def test_repr_conversion() -> None:
        value = "hello"
        result = dedent(f"""
            Value:
                {align(value)!r}
        """)
        assert result == "Value:\n    'hello'"


class TestAlignFormatSpec:
    @staticmethod
    def test_numeric_format() -> None:
        result = dedent(f"""
            Value:
                {align(1.23456):.2f}
        """)
        assert result == "Value:\n    1.23"

    @staticmethod
    def test_string_format() -> None:
        result = dedent(f"""
            Header:
                {align("hi"):>10}
        """)
        assert result == "Header:\n            hi"


class TestAlignStrip:
    @staticmethod
    def test_strip_none() -> None:
        items = "- apples\n- bananas"
        result = dedent(
            f"""
            List:
                {align(items)}
            ---
            """,
            strip="none",
        )
        assert result == "\nList:\n    - apples\n    - bananas\n---\n"

    @staticmethod
    def test_strip_all() -> None:
        items = "- apples\n- bananas"
        result = dedent(
            f"""
            List:
                {align(items)}
            ---
            """,
            strip="all",
        )
        assert result == "List:\n    - apples\n    - bananas\n---"

    @staticmethod
    def test_strip_smart() -> None:
        items = "- apples\n- bananas"
        result = dedent(
            f"""
            List:
                {align(items)}
            ---
            """,
            strip="smart",
        )
        assert result == "List:\n    - apples\n    - bananas\n---"


class TestAlignMarkerLeakage:
    @staticmethod
    def test_no_null_bytes_in_output() -> None:
        items = "- apples\n- bananas"
        result = dedent(f"""
            List:
                {align(items)}
        """)
        assert "\x00" not in result

    @staticmethod
    def test_no_markers_in_output() -> None:
        items = "- apples\n- bananas"
        result = dedent(f"""
            {align(items)}
        """)
        assert "DEDENT_ALIGN" not in result


class TestAlignWithoutDedent:
    @staticmethod
    def test_aligned_str_contains_markers() -> None:
        wrapper = align("hello")
        text = str(wrapper)
        assert "\x00" in text
        assert "hello" in text

    @staticmethod
    def test_aligned_repr_contains_markers() -> None:
        wrapper = align("hello")
        text = repr(wrapper)
        assert "\x00" in text
        assert "'hello'" in text

    @staticmethod
    def test_aligned_format_contains_markers() -> None:
        wrapper = align(1.23)
        text = format(wrapper, ".1f")
        assert "\x00" in text
        assert "1.2" in text


class TestAlignEdgeCases:
    @staticmethod
    def test_value_with_trailing_newline() -> None:
        items = "- apples\n- bananas\n"
        result = dedent(f"""
            List:
                {align(items)}---
        """)
        assert result == "List:\n    - apples\n    - bananas\n    ---"

    @staticmethod
    def test_non_string_value() -> None:
        result = dedent(f"""
            Value:
                {align(42)}
        """)
        assert result == "Value:\n    42"

    @staticmethod
    def test_deeply_nested_indentation() -> None:
        inner = "a\nb\nc"
        result = dedent(f"""
            Level1:
                Level2:
                    Level3:
                        {align(inner)}
        """)
        expected = (
            "Level1:\n    Level2:\n        Level3:\n            a\n            b\n            c"
        )
        assert result == expected
