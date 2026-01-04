'''
Dedent is a library for dedenting text.

Port of the TypeScript [dedent](https://github.com/dmnd/dedent) library. Preferred over
`textwrap.dedent` because it uses `string.templatelib` and t-strings for better handling of
interpolations, for example, to align the string output of multiline interpolations.

```python
from dedent import dedent

groceries = dedent(t"""
    - apples
    - bananas
    - cherries
""")

without_align = dedent(t"""
    List without align_values (default):
        {groceries}
    Done.
""")

with_align = dedent(
    t"""
        List with align_values: true
            {groceries}
        Done.
    """,
    align_values=True,
)

print(without_align)
print("---")
print(with_align)

# Output:
# List without align_values (default):
#     - apples
# - bananas
# - cherries
# Done.
# ---
# List with align_values: true
# 	- apples
# 	- bananas
# 	- cherries
# Done.
```
'''

from ._dedent import dedent

__all__ = ["dedent"]
