from dataclasses import dataclass, field

from .code.span import Span as SpanCallback
from .node import Node, SpanEnd, SpanStart


@dataclass(slots=True)
class Span:
    callback: SpanCallback
    start_cache: dict[Node, SpanStart] = field(init=False, default_factory=dict)
    end_cache: dict[Node, SpanStart] = field(init=False, default_factory=dict)

    def start(self, otherwise: Node | None = None) -> SpanStart:
        if otherwise is not None and otherwise in self.start_cache:
            return self.start_cache[otherwise]

        res = SpanStart(self)
        if otherwise is not None:
            res.otherwise(otherwise)
            self.start_cache[otherwise] = res
        return res

    def end(self, otherwise: Node | None = None) -> SpanEnd:
        if otherwise is not None and otherwise in self.end_cache:
            return self.end_cache[otherwise]

        res = SpanEnd(self)
        if otherwise is not None:
            res.otherwise(otherwise)
            self.end_cache[otherwise] = res
        return res

    def __hash__(self) -> int:
        return hash(self.callback.name)
