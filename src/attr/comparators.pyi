from typing import TypeVar, Optional, Callable
from . import _ComparatorType

_T = TypeVar("_T")
_FuncType = Callable[[_T, _T], bool]

def using_key(key: Callable[_T], order: Optional[bool]) -> _ComparatorType: ...
def using_functions(
    eq: _FuncType,
    lt: Optional[_FuncType],
    le: Optional[_FuncType],
    gt: Optional[_FuncType],
    ge: Optional[_FuncType],
) -> _ComparatorType: ...
