"""
Edge
----

Node's edge in the parser graph.
"""

# Prevent circular importing but also enhance speedups.
from . import node as _node


class Edge:
    """Represents an edge in the parser graph."""

    __slots__ = ("key", "no_advance", "node", "value")

    def __eq__(a: "Edge", b: "Edge"):
        if isinstance(a.key, int):
            return a.key == (b.key[0] if not isinstance(b.key, int) else b.key)
        return a.key == b.key

    def __init__(
        self,
        node: "_node.Node",
        no_advance: bool,
        key: bytes | str | int | None = None,
        value: int | None = None,
    ) -> None:
        if isinstance(key, str):
            key = key.encode("ascii")

        self.node = node
        self.no_advance = no_advance
        self.key = key
        self.value = value
        if isinstance(node, _node.Invoke):
            match node.code.signature:
                case "match":
                    assert value is None, "Invalid Invoke's code signature"
                case "value":
                    assert value is not None, "Invalid Invoke's code signature"

        if isinstance(key, (bytes, str)):
            assert len(key) > 0, "Invalid edge buffer length"
            if no_advance:
                assert len(key) == 1, (
                    "Only 1-character keys are allowed with no_advance edges."
                )

    def __hash__(self):
        return hash((self.node.name, self.no_advance, self.key, self.value))

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(node={self.node.name!r},"
            f"no_advance={self.no_advance!r}, "
            f"key={self.key!r}, value={self.value!r})"
        )
