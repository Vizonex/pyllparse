from dataclasses import dataclass, field
from typing import Any, Optional, Callable

from ..pyfront.front import Code, IWrap, Span, SpanField
from ..pyfront.transform import Transform


class Slot:
    # ONLY NODE SHOULD BE ALLOWED TO BE SEEN

    def __init__(
        self, node: IWrap["Node"], value: Callable[[IWrap["Node"]], None]
    ) -> None:
        self.privNode = node
        """Same as calling it from get and setting the value etc..."""
        self.privUpdate = value

    # TODO Vizonex Figure out how to actually implement
    # Slots -> private readonly privUpdate: (value: IWrap<Node>) => void
    # For Now use this backup by using the unique name to hash the values
    # I spent 4 hours trying to figure this how this could be implemented
    # so this is my only ideal sloution
    def __hash__(self) -> int:
        return hash(self.privNode.ref.id.name)

    @property
    def node(self):
        return self.privNode

    @node.setter
    def node(self, value: IWrap["Node"]):
        self.privNode = value
        self.privUpdate(value)


@dataclass(unsafe_hash=True)
class IUniqueName:
    name: str
    originalName: str

    # def __hash__(self):
    #     return hash(self.name)


@dataclass
class IOtherwiseEdge:
    node: IWrap["Node"]
    noAdvance: bool
    value: Optional[int]


@dataclass
class Identifier:
    prefix: str = ""
    postfix: str = ""
    ns: set[str] = field(default_factory=set, init=False)

    def id(self, name: str):
        """Creates a Unique name for the switches"""
        target = self.prefix + name + self.postfix

        if target in self.ns:
            i = 1
            for i in range(1, len(self.ns)):
                if (target + "_%i" % i) not in self.ns:
                    break
            target += "_%i" % i

        self.ns.add(target)
        return IUniqueName(target, name)


@dataclass
class Node:
    id: IUniqueName
    otherwise: Optional[IOtherwiseEdge] = field(default=None, init=False)
    Slots: Optional[list[Slot]] = field(default_factory=list, init=False)

    def setOtherwise(
        self, node: IWrap["Node"], noAdvance: bool, value: Optional[int] = None
    ):
        self.otherwise = IOtherwiseEdge(node, noAdvance, value)

    def getSlots(self):
        if self.Slots == []:
            self.Slots.extend(self.buildSlots())
        yield from self.Slots

    def buildSlots(self):
        otherwise = self.otherwise
        if otherwise:
            yield Slot(otherwise.node, otherwise.node)

    def __hash__(self):
        return hash(self.id)


class Consume(Node):
    def __init__(self, id: IUniqueName, field: str) -> None:
        self.field = field
        super().__init__(id)


@dataclass
class IInvokeEdge:
    code: int
    node: IWrap[Node]


class Invoke(Node):
    def __init__(self, id: IUniqueName, code: IWrap[Code]) -> None:
        self.Edges: list[IInvokeEdge] = []
        self.code = code
        super().__init__(id)

    def addEdge(self, code: int, node: IWrap[Node]):
        self.Edges.append(IInvokeEdge(code, node))

    def edges(self):
        return self.Edges

    def buildSlots(self):
        for edge in self.Edges:
            yield Slot(edge.node, edge.node)

        for e in super().buildSlots():
            yield e


class Empty(Node):
    def __hash__(self):
        return hash(self.id)


class Error(Node):
    def __init__(self, id: IUniqueName, code: int, reason: str) -> None:
        self.code = code
        self.reason = reason
        super().__init__(id)


class Match(Node):
    def __init__(self, id: IUniqueName) -> None:
        self.transform: Optional[IWrap[Transform]] = None
        super().__init__(id)

    def setTransform(self, transform: IWrap[Transform]):
        self.transform = transform


class Pause(Error):
    def __init__(self, id: IUniqueName, code: int, reason: str) -> None:
        super().__init__(id, code, reason)


@dataclass
class ISeqEdge:
    node: IWrap[Node]
    value: Optional[int]


# TODO Make Sure TypeHinting doesn't overlap with the Real Sequence typehint!
# So I'll add an extra S to it for now...
class Sequence(Match):
    def __init__(self, id: IUniqueName, select: str) -> None:
        self.select = select
        self.Edge: Optional[ISeqEdge] = None
        super().__init__(id)

    def setEdge(self, node: Node, value: Optional[int]):
        assert True if not self.Edge else False
        self.Edge = ISeqEdge(node, value)

    def buildSlots(self):
        edge = self.Edge
        yield Slot(edge.node, edge.node)
        for e in super().buildSlots():
            yield e


class SpanStart(Node):
    def __init__(
        self, id: IUniqueName, field: SpanField, callback: IWrap[Span]
    ) -> None:
        self.field = field
        self.callback = callback
        super().__init__(id)


class SpanEnd(Node):
    def __init__(
        self, id: IUniqueName, field: SpanField, callback: IWrap[Span]
    ) -> None:
        self.field = field
        self.callback = callback
        super().__init__(id)


@dataclass
class ISingleEdge:
    key: int
    node: IWrap[Node]
    noAdvance: bool
    value: Optional[int] = None


class Single(Match):
    def __init__(self, id: IUniqueName) -> None:
        self.privEdges: list[ISingleEdge] = []

        super().__init__(id)

    def addEdge(
        self, key: int, node: IWrap[Node], noAdvance: bool, value: Optional[int] = None
    ):
        self.privEdges.append(ISingleEdge(key, node, noAdvance, value))

    @property
    def edges(self):
        return self.privEdges

    def buildSlots(self):
        for edge in self.privEdges:
            yield Slot(edge.node, edge.node)
        return super().buildSlots()


@dataclass
class ITableEdge:
    keys: list[int]
    node: IWrap[Node]
    noAdvance: bool


class TableLookup(Match):
    def __init__(self, id: IUniqueName) -> None:
        self.privEdges: list[ITableEdge] = []
        super().__init__(id)

    def addEdge(self, edge: ITableEdge):
        self.privEdges.append(edge)

    def buildSlots(self):
        for e in self.privEdges:
            yield Slot(e.node, lambda value: setattr(e, "node", value))
        yield from super().buildSlots()

