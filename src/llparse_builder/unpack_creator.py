from dataclasses import dataclass, field

from .node import Node, Unpack


@dataclass(slots=True)
class StructUnpack:
    fmt: str
    cache: dict[Node, list[Unpack]] = field(default_factory=dict, init=False)

    def _unpack_items(self, node: Node) -> list[Unpack]:
        if node not in self.cache:
            unpacks: list[Unpack] = []
            for single in self.fmt.split("|"):
                name, single_format = single.split(":", 1)
                unpacks.append(Unpack.from_format(name, single_format))
            self.cache[node] = unpacks
            return unpacks
        else:
            return self.cache[node]

    def unpack(self, node: Node) -> Unpack:
        """unpack from given format and then move onto this node"""
        items = self._unpack_items(node)
        items[-1].skip_to(node)
        return items[0]


@dataclass(slots=True)
class UnpackCreator:
    cache: dict[str, StructUnpack] = field(default_factory=dict, init=False)

    def struct(self, fmt: str) -> StructUnpack:
        """Uses a custom structure for providing multiple ways to handle
        unpackable formats

        :param fmt: format of the nodes
            `name:format|name:format`
        """
        if fmt in self.cache:
            return self.cache[fmt]
        s = StructUnpack(fmt)
        self.cache[fmt] = s
        return s

    def with_format(self, fmt: str, node: Node) -> Unpack:
        """Unpack using this format and then move onto this node.
        :param fmt: format of the nodes
            `name:format|name:format`
        :param node: the node to move to after finishing.

        :returns: the starting unpack node.
        """
        return self.struct(fmt).unpack(node)
