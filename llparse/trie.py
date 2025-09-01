from dataclasses import dataclass
from functools import total_ordering
from typing import Optional

from .pybuilder.main_code import Edge, Node


@total_ordering
@dataclass
class IEdge:
    # NOTE THIS SHOULD BE STRICTLY BYTES !!!
    key: bytes
    node: Node
    noAdvance: bool
    value: Optional[int] = None

    def __lt__(self, object: "IEdge"):
        return self.key < object.key


@dataclass
class TrieNode:
    """Mainly Used as an Abstract Object for typing"""


@dataclass
class TrieSequence(TrieNode):
    select: bytes
    child: TrieNode


@dataclass
class ITrieSingleChild:
    key: int
    noAdvance: bool
    node: TrieNode


@dataclass
class TrieEmpty(TrieNode):
    node: Node
    value: int


@dataclass
class TrieSingle(TrieNode):
    children: list[ITrieSingleChild]
    otherwise: Optional[TrieEmpty] = None


@dataclass
class Trie:
    name: str

    def build(self, edges: list[Edge]):
        if not edges:
            return None
        internalEdges: list[IEdge] = []

        for edge in edges:
            key = chr(edge.key) if isinstance(edge.key, int) else edge.key
            internalEdges.append(
                IEdge(
                    key=key.encode("utf-8") if isinstance(key, str) else key,
                    noAdvance=edge.noAdvance,
                    node=edge.node,
                    value=edge.value,
                )
            )

        return self.level(internalEdges)

    def level(self, edges: list[IEdge], path: list[bytes] = []):
        first = edges[0].key
        last = edges[-1].key
        # print("level", edges, first)
        if len(edges) == 1 and (len(edges[0].key) == 0):
            return TrieEmpty(edges[0].node, edges[0].value)

        i = 0
        # print(first)
        for i in range(len(first)):
            if first[i] != last[i]:
                break

        if i > 1:
            # NOTE I think Indutny intended for these sequences
            # to advance otherwise not having this would result in a recursion error
            # This is why first[:i] is used and not first[0:count] like in typescript...
            return self.sequence(edges, first[: i + 1], path)

        return self.single(edges, path)

    def Slice(self, edges: list[IEdge], off: int):
        _slice = [
            IEdge(edge.key[off:], edge.node, edge.noAdvance, edge.value)
            for edge in edges
        ]
        return sorted(_slice, key=lambda k: k.key)

    def sequence(self, edges: list[IEdge], prefix: bytes, path: list[bytes]):
        sliced = self.Slice(edges, len(prefix))
        assert not any([edge.noAdvance for edge in edges])
        child = self.level(sliced, path + [prefix])
        return TrieSequence(prefix, child)

    def single(self, edges: list[IEdge], path: list[bytes]):
        if not len(edges[0].key):
            assert not path, f'Empty root entry at "{self.name}"'
            assert not (len(edges) == 1 or len(edges[1].key) != 0), (
                f'Duplicate entries in "{self.name}" at: ['
                + (b", ".join(path).decode("utf-8"))
                + "]"
            )
        
        keys: dict[int, list[IEdge]] = {}
        otherwise = None
        for edge in edges:
            if not edge.key:
                otherwise = TrieEmpty(edge.node, edge.value)
                continue

            key = edge.key[0]

            if key in keys:
                keys[key].append(edge)
            else:
                keys[key] = [edge]

        children: list[ITrieSingleChild] = []

        for key, subEdges in keys.items():
            # TODO LOG FUNCTION's ARGUMENTS TO DETERMINE WEATHER OR NOT IT'S the Problem...
            # I think this maybe the problem now that I think about it...
            sliced = self.Slice(subEdges, 1)

            subPath = path + [chr(key).encode("utf-8")]

            noAdvance = any([e.noAdvance for e in subEdges])
            allSame = all([e.noAdvance == noAdvance for e in subEdges])

            if not (allSame or len(subEdges) == 0):
                err = (
                    f'Conflicting `.peek` and `.match` entries in "{self.name}" at: ['
                    + (b", ".join(subPath).decode("utf-8"))
                    + "]"
                )
                raise TypeError(err)
    
            children.append(
                ITrieSingleChild(key, noAdvance, self.level(sliced, subPath))
            )

        return TrieSingle(children, otherwise)
