from collections import defaultdict
from dataclasses import dataclass, field
from logging import getLogger

from .errors import Error
from .node import Node, SpanEnd, SpanStart
from .reachability import Reachability
from .span import Span

LOG = getLogger(__name__)


def _id(node: SpanStart | SpanEnd) -> Span:
    return node.span


@dataclass(slots=True)
class ISpanActiveInfo:
    active: defaultdict[Node, set[Span]] = field(
        default_factory=lambda: defaultdict(set)
    )
    spans: list[Span] = field(default_factory=list)


@dataclass(slots=True)
class ISpanAllocatorResult:
    colors: dict[Span, int] = field(default_factory=dict)
    concurrency: list[list[Span]] = field(default_factory=list)
    max: int = field(default_factory=int)


# Personally I think having this function
# outside of color(...) function is a bit cleaner
# we could always change the name of this function
# specifically in the future
def _allocate(this: "SpanAllocator", span: Span) -> int:
    if span in this._colors:
        return this._colors[span]

    overlap = this._overlap_map[span]

    used: set[int] = set()
    for sub_span in overlap:
        if sub_span in this._colors:
            used.add(this._colors.get(sub_span))

    # XXX: Is this optimizable?
    i = 0
    while i in used:
        i += 1

    this._mx = max(this._mx, i)
    this._colors[span] = i
    return i


class SpanAllocator:
    __slots__ = ("_colors", "_mx", "_overlap_map")

    def __init__(self) -> None:
        return

    def allocate(self, root: Node):
        # Less numbers needing crunching if everything
        # is more glued together.
        info = self.compute_active(Reachability().build(root))

        self.check(info)
        return self.color(info.spans, self.compute_overlap(info))

    def check(self, info: ISpanActiveInfo) -> None:
        for node, spans in info.active.items():
            for edge in node.get_all_edges():
                edge_node = edge.node
                if isinstance(edge_node, SpanStart):
                    continue

                # Typescript LLParse NOTE: Skip terminal nodes
                if not edge_node.get_all_edges():
                    continue

                if not LOG.disabled:
                    LOG.debug(f"checking edge from {node.name!r} to {edge_node.name!r}")

                for sub_span in info.active[edge_node]:
                    if sub_span not in spans:
                        raise Error(
                            f"unmatched span end for {sub_span.callback.name!r}"
                            f"at {edge_node.name!r}, coming from {node.name!r}"
                        )

                if isinstance(edge_node, SpanEnd):
                    span = edge_node.span
                    if span not in spans:
                        raise Error(f"unmatched span end for {span.callback.name!r}")

    def compute_active(self, nodes: list[Node]) -> ISpanActiveInfo:
        active_map: defaultdict[Node, set[Node]] = defaultdict(set)

        queue = set(nodes)
        spans: set[Span] = set()
        # This fixes an issue when using a for loop which unlike in typescript
        # we cannot remove items when in a for-loop in python this also ensures
        # that all spans are visited.
        while queue:
            node = queue.pop()
            active = active_map[node]
            if isinstance(node, SpanStart):
                span = _id(node)
                spans.add(span)
                active.add(span)

            for span in active:
                if isinstance(node, SpanEnd) and span == _id(node):
                    break

                for edge in node.get_all_edges():
                    edge_node = edge.node

                    if isinstance(edge_node, SpanStart) and _id(edge_node) == span:
                        raise Error(
                            f"Detected loop in span {span.callback.name!r} at {node.name!r}"
                        )

                    edgeActive = active_map[edge_node]
                    if span in edgeActive:
                        break

                    edgeActive.add(span)
                    queue.add(edge_node)

        return ISpanActiveInfo(active=active_map, spans=list(spans))

    def compute_overlap(self, info: ISpanActiveInfo) -> defaultdict[Span, set[Span]]:
        overlap: defaultdict[Span, set[Span]] = defaultdict(set)
        for spans in info.active.values():
            # Itertools might be a good option here...
            for one in spans:
                for other in spans:
                    if other != one:
                        overlap[one].add(other)
        return overlap

    def color(
        self, spans: list[Span], overlap_map: dict[Node, set[Span]]
    ) -> ISpanAllocatorResult:
        # Used _max instead of max because max() is an api called function needed in a bit...
        self._mx = -1
        self._colors: dict[Span, int] = {}

        self._overlap_map = overlap_map

        colors = {span: _allocate(self, span) for span in spans}

        # This algorythm is a little bit less complicated than typescript
        # llparse so lets let it stay the way it is...

        # TODO: Maybe concurrency should've been a defaultdict?

        concurrency: list[list[Span]] = [[] for _ in range(self._mx + 1)]
        for s in sorted(spans, key=lambda s: s.callback.name):
            concurrency[_allocate(self, s)].append(s)
        return ISpanAllocatorResult(colors, concurrency, self._mx)
