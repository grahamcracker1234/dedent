import sys
from typing import cast

import pytest

from dedent import dedent

required_py314 = pytest.mark.skipif(sys.version_info < (3, 14), reason="requires Python 3.14+")

if sys.version_info >= (3, 14):
    from string.templatelib import Template

    _T = Template
else:
    _T = str


def t(source: str, /, **ns: object) -> _T:
    code = compile(f"t'''{source}'''", "<t-string>", "eval")
    return cast("_T", eval(code, ns))  # ruff: ignore[suspicious-eval-usage]


def dedent_f(string: str) -> str:
    """Call `dedent` on an interpolated f-string (not `LiteralString` on 3.14+)."""
    return dedent(string)  # pyright: ignore[reportArgumentType]
