from inline_snapshot import snapshot

from dedent import dedent

from ._support import dedent_f, required_py314, t


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
def test_tstring_omits_whitespace_before_the_opening_newline() -> None:
    assert dedent(t(" \n {value}\n ", value="hello")) == snapshot("hello\n")


@required_py314
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
def test_tstring_empty_format_spec() -> None:
    assert dedent(t("{123:}")) == dedent_f(f"{123:}") == snapshot("123")
