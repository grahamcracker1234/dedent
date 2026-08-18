import pytest
from inline_snapshot import snapshot

from dedent import align, dedent

from ._support import dedent_f, required_py314, t

ITEMS = "- apples\n- bananas\n- cherries"


def test_unaligned_multiline_value() -> None:
    # Column-0 lines from interpolation prevent a common indent prefix.
    assert dedent_f(f"""
    List:
        {ITEMS}
    ---
    """) == snapshot("""\
    List:
        - apples
- bananas
- cherries
    ---
    \
""")


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


def test_alignment_after_terminal_newline_preserves_interpolation_column() -> None:
    value = "item\n"
    assert dedent_f(f"""
            List:
                {align(value)}
            """) == snapshot("List:\n    item\n    \n")


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


def test_nested_wrappers() -> None:
    inner = "line1\nline2"
    outer = f"outer {align(inner)}"
    result = dedent_f(f"""
        {align(outer)}""")
    assert result == snapshot("""\
outer line1
      line2\
""")
    assert "\x00" not in result
    assert "DEDENT_ALIGN" not in result


def test_alignment_uses_interpolation_column_with_non_space_prefix() -> None:
    value = "line1\nline2"
    string = f"\N{NO-BREAK SPACE}{align(value)}"
    assert (
        dedent(string)  # pyright: ignore[reportArgumentType]: runtime contract
        == snapshot("\N{NO-BREAK SPACE}line1\n line2")
    )


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
def test_align_wrapper_rejected_in_tstring() -> None:
    message = r"align\(\) is only supported in f-strings; t-strings align automatically"
    with pytest.raises(TypeError, match=message):
        _ = dedent(t("{items}", items=align(ITEMS)))
    with pytest.raises(TypeError, match=message):
        _ = dedent(t("{items}", items=str(align(ITEMS))))
    with pytest.raises(TypeError, match=message):
        _ = dedent(t("{items:noalign}", items=align(ITEMS)))


@required_py314
def test_noalign_directive_with_format_spec() -> None:
    assert dedent(t("{123:06d:noalign}")) == snapshot("000123")
    assert dedent(t("{123:noalign:06d}")) == snapshot("000123")


@required_py314
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
def test_align_format_spec_is_not_supported() -> None:
    with pytest.raises(ValueError, match=r"(?i)invalid format spec"):
        _ = dedent(t("{123:align}"))


def test_wrapper_embeds_markers() -> None:
    text = str(align("hello"))
    assert "hello" in text
    assert "\x00" in text
    assert repr("hello") in repr(align("hello"))
    assert "1.2" in format(align(1.23), ".1f")
    assert "\x00" in format(align(1.23), ".1f")
