from typing import Any

from llparse_builder import node as api

from .node import TrieNode


class TrieEmpty(TrieNode):
    __slots__ = ("node", "value")

    def __init__(self, node: api.Node, value: int | Any):
        self.node = node
        self.value = value
