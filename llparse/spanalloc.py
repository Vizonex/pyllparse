from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Union

from .errors import Error
from .pybuilder.main_code import Node, Reachability, Span, SpanEnd, SpanStart

SpanSet = set[Span]


def _id(node: Union[SpanStart, SpanEnd]):
    return node.span


@dataclass
class ISpanActiveInfo:
    active: dict[Node, SpanSet] = field(default_factory=dict)
    spans: list[Span] = field(default_factory=list)


SpanOverlap = dict[Node, SpanSet]


@dataclass
class ISpanAllocatorResult:
    colors: dict[Span, int] = field(default_factory=dict)
    concurrency: list[list[Span]] = field(default_factory=list)
    max: int = field(default_factory=int)


class SpanAllocator:
    def __init__(self) -> None:
        return

    def allocate(self, root: Node):
        nodes = Reachability.build(root)
        info = self.computeActive(nodes)

        self.check(info)
        overlap = self.computeOverlap(info)
        return self.color(info.spans, overlap)

    def check(self, info: ISpanActiveInfo):
        for node, spans in info.active.items():
            for edge in node.getAllEdges():
                if isinstance(edge.node, SpanStart):
                    continue

                # Skip terminal nodes
                # print(len(edge.node.getAllEdges()))
                # print(info.active)
                if len(edge.node.getAllEdges()) == 0:
                    continue

                # assert node.name != edge.node.name
                # print("checking edge from %s to %s" % (node.name,edge.node.name))
                # check edge

                edgeSpans: set[Span] = info.active[edge.node]
                # print("SPAN:%s  NODE:%s" % (edgeSpans,edge.node.__dict__))
                for subSpan in edgeSpans:
                    if subSpan not in spans:
                        raise Error(
                            f'unmatched span end for "{subSpan.callback.name}"'
                            f'at "{edge.node.name}", coming from "{node.name}"'
                        )

                if isinstance(edge.node, SpanEnd):
                    span = _id(edge.node)
                    if span not in spans:
                        raise Error(f'unmatched span end for "{span.callback.name}"')

    def computeActive(self, nodes: list[Node]):
        activeMap: dict[Node, SpanSet] = dict()
        for node in nodes:
            activeMap[node] = set()

        queue = set(nodes)
        spans: SpanSet = set()
        # This fixes an issue when using a for loop which unlike in typescript
        # we cannot remove items when in a for-loop in python this also ensures
        # that all spans are visited.
        while queue:
            node = queue.pop()
            active = activeMap[node]
            if isinstance(node, SpanStart):
                span = _id(node)
                spans.add(span)
                active.add(span)

            for span in active:
                if isinstance(node, SpanEnd) and span == _id(node):
                    break

                for edge in node.getAllEdges():
                    edgeNode = edge.node

                    if isinstance(edgeNode, SpanStart):
                        if _id(edgeNode) == span:
                            raise Error(
                                f'Detected loop in span {span.callback.name} at "{node.name}"'
                            )

                    edgeActive = activeMap[edgeNode]
                    if span in edgeActive:
                        break

                    edgeActive.add(span)
                    queue.add(edgeNode)

        return ISpanActiveInfo(active=activeMap, spans=list(spans))

    def computeOverlap(self, info: ISpanActiveInfo):
        active = info.active

        overlap: dict[Span, set[Span]] = {span: set() for span in info.spans}
        for _, spans in active.items():
            for one in spans:
                for other in spans:
                    if other != one:
                        overlap[one].add(other)
        return overlap

    def _allocate(self, span: Span):
        if span in self._colors:
            return self._colors[span]

        overlap = self._overlapMap[span]

        used: set[int] = set()
        for subSpan in overlap:
            if subSpan in self._colors:
                used.add(self._colors.get(subSpan))
        i = 0
        while i in used:
            i += 1

        self._mx = max(self._mx, i)
        self._colors[span] = i
        return i

    def color(self, spans: list[Span], overlapDict: SpanOverlap):
        # Used _max instead of max because max() is an api called function needed in a bit...
        self._mx = -1
        self._colors: dict[Span, int] = {}

        self._overlapMap = overlapDict

        colors = {span: self._allocate(span) for span in spans}

        concurrency = list()
        for _ in range(self._mx + 1):
            # NOTE : concurrency[i] = [] doesn't work but this does :P
            concurrency.append([])

        for s in sorted(spans, key=lambda s: s.callback.name):
            concurrency[self._allocate(s)].append(s)
        return ISpanAllocatorResult(colors, concurrency, self._mx)


# TODO (Vizonex) Use Indutny's Mini Http parser to help with testing ours to verify that ours is correct...
