from .node import TrieNode


class TrieSequence(TrieNode):
    __slots__ = ("child", "select")

    def __init__(self, select: bytes, child: TrieNode) -> None:
        self.select = select
        self.child = child
