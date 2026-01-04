import pytest

from dedent import dedent


def test_literal():
    output = dedent("""
        hello
          world
    """)
    assert output == "hello\n  world"


def test_template():
    output = dedent(t"""
        hello
          world
    """)
    assert output == "hello\n  world"


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
    assert output == "hello\n  python"

    output = dedent(f"""
        hello
          {123}
    """)  # pyright: ignore[reportArgumentType]
    assert output == "hello\n  123"

    def wrapped(value: str) -> str:
        return dedent(f"""
            hello
              {value}
        """)  # pyright: ignore[reportArgumentType]

    output = wrapped("python")
    assert output == "hello\n  python"


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
    output = dedent(t"""
        {header:=^17}
        - Total: {total:06d}
        - Discount: {discount:.2%}
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


def test_strip_default():
    input_string = """
        hello
    """

    output = dedent(input_string)
    assert output == "hello"
    assert output == dedent(input_string, strip=True), "strip=True should be the default"


def test_no_align_default():
    groceries = dedent("""
        - apples
        - bananas
        - cherries
    """)
    input_string = t"""
        List:
            {groceries}
        ---
    """

    output = dedent(input_string)
    assert output == "List:\n    - apples\n- bananas\n- cherries\n---"

    assert output == dedent(input_string, align=False), "align=False should be the default"


def test_align():
    groceries = dedent("""
        - apples
        - bananas
        - cherries
    """)
    output = dedent(
        t"""
            List:
                {groceries}
            ---
        """,
        align=True,
    )
    assert output == "List:\n    - apples\n    - bananas\n    - cherries\n---"


def test_align_ignores_non_multiline_formatted_outputput():
    groceries = dedent("""
        - apples
    """)
    assert "\n" not in groceries

    output = dedent(
        t"""
            List:
                {groceries}
            ---
        """,
        align=True,
    )
    assert output == "List:\n    - apples\n---"


def test_align_no_indent():
    groceries = dedent("""
        - apples
        - bananas
        - cherries
    """)
    result = dedent(t"{groceries}", align=True)
    assert result == "- apples\n- bananas\n- cherries"
