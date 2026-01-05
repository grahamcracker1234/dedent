# dedent

It's like `textwrap.dedent`, but actually functional.

> Only supports Python 3.14+ due to the use of t-strings.

## Table of Contents

- [Why `textwrap.dedent` Falls Short](#why-textwrapdedent-falls-short)

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
```

```plaintext

    Groceries:

- apples
- bananas
- cherries

    ---
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
```

```plaintext
    Groceries:
        - apples
- bananas
- cherries
    ---
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

print(shopping_list)
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
```

```plaintext
Groceries:
    - apples
    - bananas
    - cherries
---
```
