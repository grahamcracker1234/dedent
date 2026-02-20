# dedent

What [`textwrap.dedent`](https://docs.python.org/3/library/textwrap.html#textwrap.dedent) should have been.

Dedent and strip multiline strings, and keep interpolated values aligned—without manual whitespace wrangling. Supports t-strings (Python 3.14+) and f-strings (Python 3.10+).

> For documentation on how to use dedent with f-strings in Python 3.10-3.13, see [Legacy Support](#legacy-support-python-310-313).

## Table of Contents

- [Usage](#usage)
- [Installation](#installation)
- [Options](#options)
  - [`align`](#align)
  - [`strip`](#strip)
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

# Nested multiline strings align correctly with :align
items = dedent("""
    - apples
    - bananas
""")
shopping_list = dedent(t"""
    Groceries:
        {items:align}
    ---
""")
print(shopping_list)
# Groceries:
#     - apples
#     - bananas
# ---
```

## Installation

```bash
# Using uv (Recommended)
uv add dedent

# Using pip
pip install dedent
```

## Options

### `align`

When an interpolation evaluates to a multiline string, only its first line is placed where the `{...}` appears. Subsequent lines keep whatever indentation they already had (often none), so they can appear "shifted left". Alignment fixes this by indenting subsequent lines to match the first.

#### Format Spec Directives

Use format spec directives inside t-strings for per-value control:

- `{value:align}` - Align this multiline value to the current indentation
- `{value:noalign}` - Disable alignment for this value [^1]
- `{value:align:06d}` - Combine with other format specs [^2]

```python
from dedent import dedent

items = dedent("""
    - one
    - two
""")

result = dedent(t"""
    Aligned:
        {items:align}
    Not aligned:
        {items}
""")

print(result)
# Aligned:
#     - one
#     - two
# Not aligned:
#     - one
# - two
```

[^1]: Only has an effect when using the [`align=True` argument](#align-argument).

[^2]: This rarely makes sense, unless you are also using custom format specifications, but nonetheless works.

#### `align` Argument

Pass `align=True` to enable alignment globally for all t-string interpolations. Format spec directives override this.

```python
from dedent import dedent

items = dedent("""
    - one
    - two
""")

result = dedent(
    t"""
        List 1:
            {items}
        List 2:
            {items}
        ---
    """,
    align=True,
)

print(result)
# List 1:
#     - one
#     - two
# List 2:
#     - one
#     - two
# ---
```

### `strip`

The `strip` parameter controls how leading and trailing whitespace is removed after dedenting. It accepts three modes:

#### `"smart"` (default)

Strips one leading and one trailing newline-bounded blank segment. This is the default behavior and handles the common case of triple-quoted strings that start and end with a newline.

```python
from dedent import dedent

result = dedent("""
    hello!
""")

print(repr(result))
# 'hello!'
```

#### `"all"`

Strips all surrounding whitespace, equivalent to calling `.strip()` on the result.

```python
from dedent import dedent

result = dedent(
    """


        hello!


    """,
    strip="all",
)
print(repr(result))
# 'hello!'
```

#### `"none"`

Leaves whitespace exactly as-is after dedenting.

```python
from dedent import dedent

result = dedent(
    """
        hello!
    """,
    strip="none",
)

print(repr(result))
# '\nhello!\n'
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
    - bananas
""")
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

Per-value control with `align()` mirrors the format spec directives available on 3.14+:

```python
from dedent import align, dedent

items = dedent("""
    - one
    - two
""")

result = dedent(f"""
    Aligned:
        {align(items)}
    Not aligned:
        {items}
""")

print(result)
# Aligned:
#     - one
#     - two
# Not aligned:
#     - one
# - two
```

> There is no equivalent of the [`align` argument](#align-argument) in Python 3.10-3.13. There is no way to automatically align multiline values automatically when using f-strings.

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
groceries = dedent("""
    - apples
    - bananas
    - cherries
""".strip("\n"))

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

groceries = dedent("""
    - apples
    - bananas
    - cherries
""".strip("\n"))

manual_groceries = ("\n" + " " * 8).join(groceries.splitlines())

shopping_list = dedent(f"""
    Groceries:
        {manual_groceries}
    ---
""".strip("\n"))
```

`dedent` solves these problems and more:

```python
from dedent import dedent

groceries = dedent("""
    - apples
    - bananas
    - cherries
""")

shopping_list = dedent(t"""
    Groceries:
        {groceries:align}
    ---
""")

print(shopping_list)
# Groceries:
#     - apples
#     - bananas
#     - cherries
# ---
```
