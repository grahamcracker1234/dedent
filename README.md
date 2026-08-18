# dedent

What [`textwrap.dedent`](https://docs.python.org/3/library/textwrap.html#textwrap.dedent) should have been.

Dedent multiline strings and keep interpolated values aligned. Supports t-strings (Python 3.14+) and f-strings (Python 3.10+).

> For documentation on how to use dedent with f-strings in Python 3.10-3.13, see [Legacy Support](#legacy-support-python-310-313).

## Table of Contents

- [Usage](#usage)
- [Dedentation Rules](#dedentation-rules)
- [Installation](#installation)
- [Alignment](#alignment)
- [Legacy Support (Python 3.10-3.13)](#legacy-support-python-310-313)
- [Why `textwrap.dedent` Falls Short](#why-textwrapdedent-falls-short)

## Usage

```python
from dedent import dedent

name = "Alice"
greeting = dedent(t"""
    Hello, {name}!
    Welcome to the party.
    """)
print(greeting)
# Hello, Alice!
# Welcome to the party.

# Nested multiline strings align to the interpolation column by default
items = dedent("""
    - apples
    - bananas""")
shopping_list = dedent(t"""
    Groceries:
        {items}
    ---
    """)
print(shopping_list)
# Groceries:
#     - apples
#     - bananas
# ---
```

## Dedentation Rules

`dedent` follows the indentation model proposed by
[PEP 822](https://peps.python.org/pep-0822/):

1. Indentation is an exact prefix of spaces and tabs; a tab never equals spaces.
2. The longest indentation prefix shared by every nonblank line is removed.
3. Lines containing only spaces and tabs do not determine that prefix, except for the final line.
   A final space/tab-only line is treated like the line containing closing triple quotes.
4. Every line must be compatible with the chosen prefix. Otherwise, `IndentationError` is raised.
5. The closing-quotes indentation can preserve intentional indentation:

```python
result = dedent("""
      Hello
      World!
    """)

assert result == "  Hello\n  World!\n"
```

Keep the closing quotes at the indentation you want removed. Their placement also controls the
final newline:

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

Space/tab-only lines are ignored when finding the common prefix, but they must still be compatible
with it when that prefix is removed:

```python
dedent("\n  hello\n \t\n  world\n  ")
# IndentationError: inconsistent indentation in dedented string at line 3
```

Here the nonblank lines and closing line establish a two-space prefix. The middle line contains
one space followed by a tab, so that exact prefix cannot be removed. Raising an error catches
mixed or malformed indentation instead of silently changing or preserving ambiguous whitespace.
A shorter space/tab-only line is valid when it matches the beginning of the prefix; it simply
becomes empty. This mirrors PEP 822.

`dedent()` omits one opening newline, as PEP 822 requires. It preserves all other whitespace.
Use the closing-quote placement when you do not want a final newline.

Unlike native d-strings, `dedent()` runs after Python parses a string. Thus, Python has already
processed escape sequences. For t-strings, `dedent()` processes literal text before it renders
interpolations.

For runtime strings that use CRLF, `dedent` preserves each `\r\n` pair and excludes the terminal
`\r` from indentation checks. Other whitespace characters, such as form feed and non-breaking
space, remain content.

## Installation

```bash
# Using uv (Recommended)
uv add dedent

# Using pip
pip install dedent
```

## Alignment

When a t-string interpolation evaluates to a multiline string, `dedent` aligns each subsequent line
to the column where the interpolation begins. Column alignment is enabled by default.

> Requires Python 3.14+ (t-strings).

Use the `noalign` format spec directive to disable alignment for an individual value:

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
        {items:noalign}
    """)

print(result)
# Aligned by default:
#     - one
#     - two
# Not aligned:
#     - one
# - two
```

## Legacy Support (Python 3.10-3.13)

On Python 3.10-3.13, t-strings are not available. Use `dedent()` on plain strings and f-strings, and wrap interpolated values with `align()` to get multiline indentation alignment.

```python
from dedent import align, dedent

# dedent works on regular strings, like textwrap.dedent
message = dedent("""
    Hello,
    World!
    """)
print(message)
# Hello,
# World!

# Use align() inside f-strings for multiline value alignment
items = dedent("""
    - apples
    - bananas""")
shopping_list = dedent(f"""
    Groceries:
        {align(items)}
    ---
    """)
print(shopping_list)
# Groceries:
#     - apples
#     - bananas
# ---
```

Because Python renders an f-string before calling `dedent()`, wrap every multiline interpolation
with `align()`. Unwrapped continuation lines at column zero correctly reduce the common indentation
prefix to zero. T-strings retain interpolation boundaries, so they do not have this limitation.

> There is no way to automatically align multiline values when using f-strings.

## Why `textwrap.dedent` Falls Short

If you're here, then you're probably already familiar with the shortcomings of `textwrap.dedent`. But regardless, let's spell it out for the sake of completeness. For example, say we want to create a nicely formatted shopping list that includes some groceries:

```python
from textwrap import dedent

groceries = dedent("""
    - apples
    - bananas
    - cherries
""")

shopping_list = dedent(f"""
    Groceries:
        {groceries}
    ---
""")

print(shopping_list)
#
#     Groceries:
#
# - apples
# - bananas
# - cherries
#
#     ---
```

Wait, that's not what we wanted. We accidentally included leading and trailing newlines from the groceries string. Now, we *could* do that manually by removing, escaping, or stripping the newlines, but it's either easy to forget, difficult to read, or unnecessarily verbose.

```python
# Removing the newlines
groceries = dedent("""    - apples
    - bananas
    - cherries""")

# Escaping the newlines
groceries = dedent("""\
    - apples
    - bananas
    - cherries\
""")

# Stripping the newlines
groceries = dedent(
    """
    - apples
    - bananas
    - cherries
""".strip("\n")
)

# But the shopping list still comes out wrong:
#     Groceries:
#         - apples
# - bananas
# - cherries
#     ---
```

Uh oh, something is still wrong; the indentation is not correct at all. The interpolation happens too early. When we use an f-string with `textwrap.dedent`, the replacement occurs before dedenting can take place. Notice how only the first line of `groceries` is properly indented relative to the surrounding text? The subsequent lines lose their indentation because f-strings interpolate immediately, injecting the `groceries` string before `dedent` can process the overall structure.

Sure, we could manually adjust the indentation with a bit of string manipulation, but that's a pain to read, write, and maintain.

```python
from textwrap import dedent

groceries = dedent(
    """
    - apples
    - bananas
    - cherries
""".strip("\n")
)

manual_groceries = ("\n" + " " * 8).join(groceries.splitlines())

shopping_list = dedent(
    f"""
    Groceries:
        {manual_groceries}
    ---
""".strip("\n")
)
```

`dedent` uses closing-quote placement to control the final newline. Put the closing quotes after
the final item when nested content must not end with a newline:

```python
from dedent import dedent

groceries = dedent("""
    - apples
    - bananas
    - cherries""")

shopping_list = dedent(t"""
    Groceries:
        {groceries}
    ---
    """)

print(shopping_list)
# Groceries:
#     - apples
#     - bananas
#     - cherries
# ---
```
