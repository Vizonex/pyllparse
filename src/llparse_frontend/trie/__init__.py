from collections.abc import Sequence
from dataclasses import dataclass
from functools import total_ordering

from llparse_builder import node as api
from llparse_builder.edge import Edge

from .empty import TrieEmpty
from .node import TrieNode
from .sequence import TrieSequence
from .single import TrieSingle, TrieSingleChild

__all__ = ("IEdge", "Trie", "TrieEmpty", "TrieNode", "TrieSequence", "TrieSingle")


@total_ordering
@dataclass(slots=True, frozen=True)
class IEdge:
    key: bytes
    node: api.Node
    no_advance: bool
    value: int | None = None

    def __lt__(self, object: "IEdge"):
        return self.key < object.key


class Trie:
    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    def build(self, edges: Sequence[Edge]):
        if not edges:
            return

        internal_edges: list[IEdge] = []

        for edge in edges:
            key = chr(edge.key) if isinstance(edge.key, int) else edge.key
            internal_edges.append(
                IEdge(
                    key=key.encode("utf-8") if isinstance(key, str) else key,
                    no_advance=edge.no_advance,
                    node=edge.node,
                    value=edge.value,
                )
            )

        return self.level(internal_edges, [])

    def empty(self, edge: Edge):
        return TrieEmpty(edge.node, edge.value)

    def level(self, edges: Sequence[Edge], path: Sequence[bytes]):
        first = edges[0].key
        last = edges[-1].key

        # Leaf
        if len(edges) == 1 and not len(edges[0].key):
            return self.empty(edges[0])

        # Find the longest common sub-string
        common = 0
        for common in range(len(first)):
            if first[common] != last[common]:
                break

        # Sequence
        if common > 1:
            # We need to slice the common part of the sequence
            # where anything is matching
            # example:  'abc123', 'abc567' -> 'abc'
            return self.sequence(edges, first[: common + 1], path)

        # single
        return self.single(edges, path)

    def slice(self, edges: Sequence[IEdge], off: int) -> Sequence[IEdge]:
        return sorted(
            [
                IEdge(
                    key=edge.key[off:],
                    no_advance=edge.no_advance,
                    node=edge.node,
                    value=edge.value,
                )
                for edge in edges
            ],
            key=lambda k: k.key,
        )

    def sequence(
        self, edges: Sequence[IEdge], prefix: bytes, path: list[bytes]
    ) -> TrieSequence:
        sliced = self.slice(edges, len(prefix))
        assert not any(edge.no_advance for edge in edges)
        child = self.level(sliced, path + [prefix])
        return TrieSequence(prefix, child)

    def single(self, edges: Sequence[IEdge], path: list[bytes]):
        if not len(edges[0].key):
            assert path, f'Empty root entry at "{self.name}"'
            assert len(edges) == 1 or edges[1].key, (
                f'Duplicate entries in "{self.name}" at [ {b"".join(path)} ]'
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

        children: list[TrieSingleChild] = []
        for key, sub_edges in keys.items():
            sliced = self.slice(sub_edges, 1)

            sub_path = path + [chr(key).encode("utf-8")]

            no_advance = any(e.no_advance for e in sub_edges)
            all_same = all(e.no_advance == no_advance for e in sub_edges)

            if not (all_same or len(sub_edges) == 0):
                err = (
                    f'Conflicting `.peek` and `.match` entries in "{self.name}" at: ['
                    + (b", ".join(sub_path).decode("utf-8"))
                    + "]"
                )
                raise TypeError(err)
            children.append(
                TrieSingleChild(key, no_advance, self.level(sliced, sub_path))
            )

        return TrieSingle(children, otherwise)
