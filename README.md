# dedent

Write multiline strings naturally. Keep every interpolation aligned.

Supports both f-strings and t-strings.

```python
from dedent import dedent


def showcase():
    features = dedent("""
        ✦ clean multiline strings
        ✦ automatic column alignment
        ✦ zero dependencies""")
    install = dedent("""
        uv add dedent
        pip install dedent""")

    print(
        dedent(t"""
        ╭─ dedent ──────────────────────────
          Features: {features}
          Install:  {install}
        ╰───────────────────────────────────""")
    )


showcase()
# ╭─ dedent ──────────────────────────
#   Features: ✦ clean multiline strings
#             ✦ automatic column alignment
#             ✦ zero dependencies
#   Install:  uv add dedent
#             pip install dedent
# ╰───────────────────────────────────
```

> This example uses t-strings and requires Python 3.14+.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [t-string alignment](#t-string-alignment)
  - [f-string alignment](#f-string-alignment)
- [Why `textwrap.dedent` Falls Short](#why-textwrapdedent-falls-short)
- [Dedentation Rules](#dedentation-rules)

## Installation

```bash
# Using uv (Recommended)
uv add dedent

# Using pip
pip install dedent
```

## Usage

`dedent()` removes shared indentation and omits the newline after the opening triple quotes:

```python
from dedent import dedent

message = dedent("""
    Hello,
    World!""")

print(message)
# Hello,
# World!
```

See [Dedentation Rules](#dedentation-rules) for newline, closing-quote, and mixed-indentation behavior.

### t-string alignment

> Requires Python 3.14+.

When a t-string interpolation evaluates to a multiline string, `dedent` aligns each subsequent line to the column where the interpolation begins. Column alignment is enabled by default. Do not wrap interpolations with `align()`; that wrapper is only for f-strings and raises `TypeError` here.

Use the `dedent`-specific `noalign` format specifier to disable alignment for an individual value:

- `{value:noalign}` - Disable column alignment for this value
- `{value:06d:noalign}` - Combine with other format specs

```python
from dedent import dedent

items = dedent("""
    - one
    - two""")

result = dedent(t"""
    Aligned by default:
        {items}
    Not aligned:
        {items:noalign}""")

print(result)
# Aligned by default:
#     - one
#     - two
# Not aligned:
#     - one
# - two
```

### f-string alignment

> For f-strings on every supported Python version. Use [t-string alignment](#t-string-alignment) on Python 3.14+ t-strings; `align()` inside a t-string interpolation raises `TypeError`.

Use `align()` with f-strings because Python 3.10-3.13 do not support t-strings:

```python
from dedent import align, dedent

items = dedent("""
    - apples
    - bananas
    - cherries""")
shopping_list = dedent(f"""
    Groceries:
        {align(items)}""")
print(shopping_list)
# Groceries:
#     - apples
#     - bananas
#     - cherries
```

Python renders an f-string before calling `dedent()`. The `align()` wrapper marks each multiline value so `dedent()` can align its continuation lines.

## Why `textwrap.dedent` Falls Short

`textwrap.dedent` preserves the newline after the opening triple quotes. To keep the source readable without printing a blank first line, you must escape that newline or remove it afterward. It also cannot preserve indentation when an f-string inserts a multiline value:

```python
from textwrap import dedent

items = dedent("""\
    - apples
    - bananas
    - cherries""")
shopping_list = dedent(f"""\
    Groceries:
        {items}""")

print(shopping_list)
#     Groceries:
#         - apples
# - bananas
# - cherries
```

The escape removes the first newline. It cannot fix the indentation: Python renders the f-string first, so the continuation lines begin at column zero and prevent `textwrap.dedent` from finding shared indentation.

`dedent()` receives a t-string's literal segments and interpolations separately:

```python
from dedent import dedent

items = dedent("""
    - apples
    - bananas
    - cherries""")
shopping_list = dedent(t"""
    Groceries:
        {items}""")

print(shopping_list)
# Groceries:
#     - apples
#     - bananas
#     - cherries
```

It dedents the literal text, then renders and aligns each continuation line with the interpolation column. On Python 3.10-3.13, [`align()`](#f-string-alignment) provides the same alignment for f-strings.

## Dedentation Rules

`dedent` follows the indentation model proposed by [PEP 822](https://peps.python.org/pep-0822/):

1. Indentation is an exact prefix of spaces and tabs; a tab never equals spaces.
2. The longest indentation prefix shared by every nonblank line is removed.
3. Lines containing only spaces and tabs do not determine that prefix, except for the final line. A final space/tab-only line is treated like the line containing closing triple quotes.
4. Every line must be compatible with the chosen prefix. Otherwise, `IndentationError` is raised.
5. The closing-quotes indentation can preserve intentional indentation:

```python
result = dedent("""
      Hello
      World!
    """)

assert result == "  Hello\n  World!\n"
```

Keep the closing quotes at the indentation you want removed. Their placement also controls the final newline:

```python
with_newline = dedent("""
    Hello
    World!
    """)
without_newline = dedent("""
    Hello
    World!""")

assert with_newline == "Hello\nWorld!\n"
assert without_newline == "Hello\nWorld!"
```

A final `\n` creates an empty closing line at column zero. This line preserves content indentation:

```python
assert dedent("\n    Hello\n") == "    Hello\n"
assert dedent("\n    Hello\n    ") == "Hello\n"
```

### Why `IndentationError`?

Space/tab-only lines are ignored when finding the common prefix, but they must still be compatible with it when that prefix is removed:

```python
dedent("\n  hello\n \t\n  world\n  ")
# IndentationError: inconsistent indentation in dedented string at line 3
```

Here the nonblank lines and closing line establish a two-space prefix. The middle line contains one space followed by a tab, so that exact prefix cannot be removed. Raising an error catches mixed or malformed indentation instead of silently changing or preserving ambiguous whitespace. A shorter space/tab-only line is valid when it matches the beginning of the prefix; it simply becomes empty. This mirrors PEP 822.

### Divergences from PEP 822

PEP 822 defines new literal syntax, while `dedent()` processes runtime values. The differences are:

- PEP 822 requires the opening quotes to be followed immediately by a newline. `dedent()` also accepts spaces or tabs before that first line ending and treats the whole line as the opener. To preserve an intentional leading blank line, put it after the opener line. Values without an opening line ending are also accepted.
- Python has already processed escape sequences before `dedent()` receives a string. For t-strings, `dedent()` processes literal text before rendering interpolations.
- Runtime strings can contain CRLF line endings. `dedent()` preserves each `\r\n` pair and excludes the terminal `\r` from indentation checks.

All other whitespace, including form feed and non-breaking space, remains content. Use the closing-quote placement when you do not want a final newline.
