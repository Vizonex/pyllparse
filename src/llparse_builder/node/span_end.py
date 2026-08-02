import typing

from .base import Node

if typing.TYPE_CHECKING:
    from ..span import Span


class SpanEnd(Node):
    __slots__ = ("span",)

    def __init__(self, span: "Span"):
        super().__init__(f"span_end_{span.callback.name}")
        self.span = span
