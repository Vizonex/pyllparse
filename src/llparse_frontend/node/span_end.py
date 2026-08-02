from ..code import Span
from ..span_field import SpanField
from ..utils import UniqueName
from ..wrap import Wrap
from .base import Node


class SpanEnd(Node):
    __slots__ = ("callback", "field")

    def __init__(self, id: UniqueName, field: SpanField, callback: Wrap[Span]):
        super().__init__(id)
        self.field = field
        self.callback = callback
