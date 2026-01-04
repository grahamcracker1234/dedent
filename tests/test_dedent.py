import pytest

from dedent import dedent


def test_literal():
    out = dedent("""
        hello
          world
    """)
    assert out == "hello\n  world"


def test_template():
    out = dedent(t"""
        hello
          world
    """)
    assert out == "hello\n  world"


def test_bad_format():
    """
    Test type checking for disallowing format strings.

    We require either a literal string or a template.
    """
    name = "python"
    out = dedent(f"""
        hello
          {name}
    """)
    assert out == "hello\n  python"

    out = dedent(f"""
        hello
          {123}
    """)  # pyright: ignore[reportArgumentType]
    assert out == "hello\n  123"

    def wrapped(value: str) -> str:
        return dedent(f"""
            hello
              {value}
        """)  # pyright: ignore[reportArgumentType]

    out = wrapped("python")
    assert out == "hello\n  python"


def test_unsupported_type():
    """
    Test type checking for disallowing unsupported types.
    """
    with pytest.raises(TypeError):
        _ = dedent(123)  # pyright: ignore[reportArgumentType]


def test_no_strip():
    out = dedent(
        """
            hello
        """,
        strip=False,
    )
    assert out == "\nhello\n"


def test_no_align():
    groceries = dedent("""
        - apples
        - bananas
        - cherries
    """)
    out = dedent(t"""
        List without align (default):
            {groceries}
        Done.
    """)
    assert out == ("List without align (default):\n    - apples\n- bananas\n- cherries\nDone.")


def test_align():
    groceries = dedent("""
        - apples
        - bananas
        - cherries
    """)
    out = dedent(
        t"""
            List with align: true
                {groceries}
            Done.
        """,
        align=True,
    )
    assert out == ("List with align: true\n    - apples\n    - bananas\n    - cherries\nDone.")


def test_align_ignores_non_multiline_formatted_output():
    groceries = dedent("""
        - apples
    """)
    out = dedent(
        t"""
            List with align: true
                {groceries}
            Done.
        """,
        align=True,
    )
    assert out == ("List with align: true\n    - apples\nDone.")


def test_format_spec():
    total = 123
    discount = 0.123456789
    header = "Receipt"
    out = dedent(t"""
        {header:=^17}
        - Total: {total:06d}
        - Discount: {discount:.2%}
    """)
    assert out == ("=====Receipt=====\n- Total: 000123\n- Discount: 12.35%")
