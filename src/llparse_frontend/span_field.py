from collections.abc import Sequence
from dataclasses import dataclass

from .code import Span
from .wrap import Wrap


@dataclass(slots=True)
class SpanField:
    index: int
    callbacks: Sequence[Wrap[Span]]
