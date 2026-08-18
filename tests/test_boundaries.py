from inline_snapshot import snapshot

from dedent import dedent

TYPICAL = """
    foo
    bar
    """


def test_closing_quotes_on_own_line_preserve_trailing_newline() -> None:
    assert dedent(TYPICAL) == snapshot("foo\nbar\n")


def test_closing_quotes_after_content_omit_trailing_newline() -> None:
    assert dedent("""
            foo
            bar""") == snapshot("foo\nbar")


def test_omits_only_opening_newline() -> None:
    assert dedent("""


            foo
            bar
            """) == snapshot("""\


foo
bar
""")


def test_omits_whitespace_before_the_opening_newline() -> None:
    assert dedent(" \n hello\n ") == snapshot("hello\n")
    assert dedent("\t\n  hello\n  ") == snapshot("hello\n")


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
