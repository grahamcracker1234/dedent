from typing import Final

import pytest

from dedent import dedent

GROCERIES: Final = dedent("""
    - apples
    - bananas
    - cherries
""")


def test_literal():
    output = dedent("""
        hello
            world
    """)
    assert output == "hello\n    world"


def test_template():
    output = dedent(t"""
        hello
            world
    """)
    assert output == "hello\n    world"


def test_bad_format():
    """
    Test type checking for disallowing format strings.

    We require either a literal string or a template.
    """
    name = "python"
    output = dedent(f"""
        hello
            {name}
    """)
    assert output == "hello\n    python"

    output = dedent(f"""
        hello
            {123}
    """)  # pyright: ignore[reportArgumentType]
    assert output == "hello\n    123"

    def wrapped(value: str) -> str:
        return dedent(f"""
            hello
                {value}
        """)  # pyright: ignore[reportArgumentType]

    output = wrapped("python")
    assert output == "hello\n    python"


def test_unsupported_type():
    """
    Test type checking for disallowing unsupported types.
    """
    with pytest.raises(TypeError):
        _ = dedent(123)  # pyright: ignore[reportArgumentType]


def test_format_spec():
    total = 123
    discount = 0.123456789
    header = "Receipt"
    decimals = 2
    output = dedent(t"""
        {header:=^17}
        - Total: {total:06d}
        - Discount: {discount:.{decimals}%}
    """)
    assert output == "=====Receipt=====\n- Total: 000123\n- Discount: 12.35%"


def test_no_strip():
    output = dedent(
        """
            hello
        """,
        strip=False,
    )
    assert output == "\nhello\n"

    output = dedent("\n    hello!\n", strip=False)
    assert output == "\nhello!\n"


def test_strip_default():
    input_string = """
        hello
    """

    output = dedent(input_string)
    assert output == "hello"
    assert output == dedent(input_string, strip=True), "strip=True should be the default"


def test_no_align_default():
    input_string = t"""
        List:
            {GROCERIES}
        ---
    """

    output = dedent(input_string)
    assert output == "List:\n    - apples\n- bananas\n- cherries\n---"
    assert output == dedent(input_string, align=False), "align=False should be the default"


def test_align():
    output = dedent(
        t"""
            List:
                {GROCERIES}
            ---
        """,
        align=True,
    )
    assert output == "List:\n    - apples\n    - bananas\n    - cherries\n---"


def test_align_ignores_non_multiline_formatted_outputput():
    grocery, *_ = GROCERIES.splitlines()
    assert "\n" not in grocery

    output = dedent(
        t"""
            List:
                {grocery}
            ---
        """,
        align=True,
    )
    assert output == "List:\n    - apples\n---"


def test_align_no_indent():
    result = dedent(t"{GROCERIES}", align=True)
    assert result == "- apples\n- bananas\n- cherries"


def test_align_override():
    output = dedent(
        t"""
            List:
                {GROCERIES:align}
            ---
        """,
        align=False,
    )
    assert output == "List:\n    - apples\n    - bananas\n    - cherries\n---"


def test_no_align_override():
    output = dedent(
        t"""
            List:
                {GROCERIES:noalign}
            ---
        """,
        align=True,
    )
    assert output == "List:\n    - apples\n- bananas\n- cherries\n---"


def test_align_override_with_format_spec():
    total = 123
    output = dedent(
        t"""
            Total: {total:align:06d}
            Total: {total:06d:align}
        """,
        align=False,
    )
    assert output == "Total: 000123\nTotal: 000123"

    output = dedent(
        t"""
            List:
                {GROCERIES:\n^{len(GROCERIES) + 2}:align}
                {GROCERIES:align:\n^{len(GROCERIES) + 2}}
            ---
        """,
        align=False,
    )
    assert (
        output
        == "List:\n    \n    - apples\n    - bananas\n    - cherries\n    \n    \n    - apples\n    - bananas\n    - cherries\n    \n---"  # noqa: E501
    )


def test_mixed_align_overrides():
    input_string = t"""
        List:
            {GROCERIES:align}
        Other:
            {GROCERIES:noalign}
        ---
    """

    output = dedent(input_string)
    assert (
        output
        == "List:\n    - apples\n    - bananas\n    - cherries\nOther:\n    - apples\n- bananas\n- cherries\n---"  # noqa: E501
    )


def test_unknown_format_spec():
    with pytest.raises(ValueError, match=r"(?i)invalid format spec"):
        _ = dedent(t"{GROCERIES:algn}")  # misspelled "align"
