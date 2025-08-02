import logging
from typing import Any, Literal, Union

from ..errors import Error
from ..pybuilder.main_code import Node

logger = logging.getLogger("llparse.pybuilder.loopchecker")
logger.setLevel(logging.INFO)


MAX_VALUE = 256
WORD_SIZE = 32
SIZE = MAX_VALUE // WORD_SIZE
WORD_FILL = -1 | 0

assert MAX_VALUE % WORD_SIZE == 0


# NOTE I think it's theroetically Possible to
# Put Lattice Class into Cython as an optional replacement
# for the Sake of speed in the near future once I've
# figured out everything myself from a more deep brain
# point of view/prespective... - Vizonex


class Lattice:
    def __init__(
        self, value: Union[Any, list[int], bytes, Literal["empty"], Literal["any"]]
    ) -> None:
        self.value = value
        self.words: list[int] = []

        # allocate space by filling in data with zeros...
        if value != "any":
            for _ in range(SIZE):
                self.words.append(0)
        else:
            for _ in range(SIZE):
                self.words.append(WORD_FILL)

        if isinstance(value, (list, bytes)):
            for single in value:
                self.add(single)

    def __iter__(self):
        for i in range(MAX_VALUE):
            if self.check(i):
                yield i

    def check(self, bit: int):
        if not (0 <= bit and bit < MAX_VALUE):
            raise AssertionError("Invalid Bit")
        index = (bit // WORD_SIZE) | 0
        off = bit % WORD_SIZE
        return self.words[index] & (1 << off) != 0

    def add(self, bit: int):
        bit = ord(bit) if isinstance(bit, str) else bit
        if not (0 <= bit and bit < MAX_VALUE):
            raise AssertionError("Invalid Bit")

        index = bit // WORD_SIZE
        off = bit % WORD_SIZE

        self.words[index] |= 1 << off

    def union(self, other: "Lattice") -> "Lattice":
        result = Lattice("empty")

        for i in range(SIZE):
            result.words[i] = self.words[i] | other.words[i]

        return result

    def intersect(self, other: "Lattice") -> "Lattice":
        result = Lattice("empty")
        for i in range(SIZE):
            result.words[i] = self.words[i] & other.words[i]
        return result

    def __repr__(self):
        return f"<Lattice {', '.join(f'{k}: {v!r}' for k, v in self.__dict__.items())}>"

    def subtract(self, other: "Lattice") -> "Lattice":
        result = Lattice("empty")
        for i in range(SIZE):
            result.words[i] = self.words[i] & (~other.words[i])
        return result

    def isEqual(self, other: "Lattice"):
        if self.toJSON() == other.toJSON():
            return True
        else:
            for i in range(SIZE):
                if self.words[i] != other.words[i]:
                    return False
        return True

    def toJSON(self):
        isEmpty = True
        isFull = True
        for i in range(SIZE):
            if self.words[i] != 0:
                isEmpty = False
            if self.words[i] != WORD_FILL:
                isFull = False
        if isEmpty:
            return "empty"
        if isFull:
            return "any"
        return list(self)


class Reachability:
    def __init__(self) -> None:
        return

    def build(self, root: Node) -> list[Node]:
        res: set[Node] = set()
        queue = [root]
        while len(queue) != 0:
            node = queue.pop()
            if node in res:
                continue
            res.add(node)
            for edge in node:
                queue.append(edge.node)
            otherwise = node.getOtherwiseEdge()
            if otherwise:
                queue.append(otherwise.node)

        # Reverse the order so that we always
        # throw an error on bad configurations...
        return res


EMPTY_VALUE = Lattice("empty")
ANY_VALUE = Lattice("any")


class LoopChecker:
    def __init__(self) -> None:
        self.lattice: dict[Node, Lattice] = {}
        self.terminatedCache: dict[Node, Lattice] = {}

    def clear(self, nodes: list[Node]):
        for node in nodes:
            self.lattice[node] = EMPTY_VALUE

    def check(self, root: Node):
        r = Reachability()
        nodes = r.build(root)

        for node in nodes:
            self.clear(nodes)
            logger.debug("checking loops starting from %s" % node.name)
            self.lattice[node] = ANY_VALUE
            # we must eliminate randomness so that error always throw
            changed: set[Node] = set([root])

            while changed:
                logger.debug("changed %s" % [n.name for n in changed])
                _next = set()
                for changedNode in changed:
                    self.propagate(changedNode, _next)
                changed = _next
            logger.debug("lattice stabilized")
            self.visit(root, [])

    def propagate(self, node: Node, changed: set[Node]):
        value = self.lattice[node]
        terminated = self.terminate(node)
        logger.debug("propagate(%r), initial value %r" % (node.name, value.toJSON()))
        if not terminated.isEqual(EMPTY_VALUE):
            logger.debug("node %s terminates %r" % (node.name, terminated.toJSON()))
            value = value.subtract(terminated)
            if value.isEqual(EMPTY_VALUE):
                return

        keysbyTarget: dict[Node, Lattice] = {}

        for edge in node.getAllEdges():
            if not edge.noAdvance:
                continue

            if keysbyTarget.get(edge.node):
                targetValue = keysbyTarget[edge.node]
            else:
                targetValue = self.lattice.get(edge.node)

            if edge.key is None or isinstance(edge.key, int):
                targetValue = targetValue.union(value)
            else:
                # From peek()
                edgeValue = Lattice([edge.key[0]]).intersect(value)
                if edgeValue.isEqual(EMPTY_VALUE):
                    continue

                targetValue = targetValue.union(edgeValue)

            keysbyTarget[edge.node] = targetValue

        for child, childValue in keysbyTarget.items():
            logger.debug(
                "node %r propagates %r to %r"
                % (node.name, childValue.toJSON(), child.name)
            )
            self.update(child, childValue, changed)
        # FINISHED!

    def update(self, node: Node, newValue: Lattice, changed: set[Node]):
        value = self.lattice[node]
        if newValue.isEqual(value):
            return False
        self.lattice[node] = newValue
        changed.add(node)
        return True

    def terminate(self, node: Node):
        if node in self.terminatedCache:
            return self.terminatedCache[node]

        terminated: list[int] = []
        for edge in node.getAllEdges():
            if edge.noAdvance:
                continue

            if edge.key is None or isinstance(edge.key, int):
                continue

            terminated.append(edge.key[0])

        result = Lattice(terminated)
        self.terminatedCache[node] = result
        return result

    def visit(self, node: Node, path: list[Node]):
        value = self.lattice[node]
        logger.debug("enter %s, value is %s" % (node.name, value.toJSON()))

        terminated = (
            EMPTY_VALUE
            if node not in self.terminatedCache
            else self.terminatedCache[node]
        )

        if not terminated.isEqual(EMPTY_VALUE):
            logger.debug(f"subtract terminated {terminated}")
            value = value.subtract(terminated)
            if value.isEqual(EMPTY_VALUE):
                logger.debug("terminated everything")
                return

        for edge in node.getAllEdges():
            if not edge.noAdvance:
                continue
            edgeValue = value
            if edge.key is None or isinstance(edge.key, int):
                pass
            else:
                edgeValue = edgeValue.intersect(Lattice([edge.key[0]]))

            if edgeValue.isEqual(EMPTY_VALUE):
                # logger.debug(edge.node.name + " not recursive")
                continue

            def indexOf(path: list[Node], obj: Node) -> int:
                for o in path:
                    if o.name == obj.name:
                        return 0
                return -1

            if indexOf(path, edge.node) != -1:
                if len(path) == 1:
                    raise Error(
                        f'Detected loop in "{edge.node.name}" through "{edge.node.name}"'
                    )

                raise Error(
                    'Detected loop in "'
                    + edge.node.name
                    + '" through chain '
                    + (" -> ").join(['"' + name.name + '"' for name in path])
                )

            self.visit(edge.node, path + [edge.node])
        logger.debug("leave %s" % node.name)
