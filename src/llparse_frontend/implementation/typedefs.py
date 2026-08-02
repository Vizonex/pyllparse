from collections.abc import Callable
from typing import TypeVar

from ..wrap import Wrap

T = TypeVar("T")
WrapCall = Callable[[T], Wrap[T]]
