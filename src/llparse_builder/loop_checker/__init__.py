import logging
from collections.abc import Sequence
from typing import TypeVar

from ..errors import Error
from ..node import Node
from ..reachability import Reachability
from .lattice import Lattice

logger = logging.getLogger(__name__)
debug = logger.debug
EMPTY_VALUE = Lattice("empty")
ANY_VALUE = Lattice("any")

T = TypeVar("T")


def js_indexof(array: Sequence[Node], item: Node) -> int:
    """mimics typescript's indexOf functionality"""
    for a in array:
        if a.name == item.name:
            return 0
    return -1


class LoopChecker:
    __slots__ = ("__weakref__", "lattice", "terminated_cache")

    def __init__(self):
        self.lattice: dict[Node, Lattice] = {}
        self.terminated_cache: dict[Node, Lattice] = {}

    def check(self, root: Node):
        r = Reachability()
        nodes = r.build(root)

        for node in nodes:
            debug(f"checking loops starting with {node.name!r}")
            self.clear(nodes)
            self.lattice[node] = ANY_VALUE
            changed = {root}
            while changed:
                if not logger.disabled:
                    debug("changed %s", [other.name for other in changed])
                next_node = set()
                for changed_node in changed:
                    self.propagate(changed_node, next_node)
                changed = next_node

            debug("lattice stabilized")
            self.visit(node, [])

    def clear(self, nodes: list[Node]):
        for n in nodes:
            self.lattice[n] = EMPTY_VALUE

    def propagate(self, node: Node, changed: set[Node]) -> None:
        value = self.lattice[node]
        debug(f"propagate({node.name!r}), initial value {value.to_json()}")

        # Termine values that are consume by match/select
        terminated = self.terminate(node)
        if not terminated.is_empty():
            debug(f"node {node.name!r} terminates {terminated.to_json()!r}")
            value = value.subtract(terminated)
            if value.is_empty():
                return

        keys_by_target: dict[Node, Lattice] = {}

        for edge in node.get_all_edges():
            if not edge.no_advance:
                continue

            if edge.node in keys_by_target:
                target_value = keys_by_target[edge.node]
            else:
                target_value = self.lattice[edge.node]

            if edge.key is None or isinstance(edge.key, int):
                # .otherwise()
                keys_by_target[edge.node] = target_value.union(value)
            else:
                # .peek()
                edge_value = Lattice([edge.key[0]]).intersect(value)
                if edge_value.is_empty():
                    continue
                keys_by_target[edge.node] = target_value.union(edge_value)

        for child, child_value in keys_by_target.items():
            debug(
                f"node {node.name!r} propagates {child_value.to_json()!r} to {child.name!r}"
            )
            self.update(child, child_value, changed)

    def update(self, node: Node, new_value: Lattice, changed: set[Node]):
        value = self.lattice[node]
        if new_value.is_equal(value):
            return False

        self.lattice[node] = new_value
        changed.add(node)
        return True

    def terminate(self, node: Node) -> Lattice:
        # print("determining termination of \"%s\"" % node.name)
        if node.name in self.terminated_cache:
            return self.terminated_cache[node]

        terminated: list[int] = []

        for edge in node.get_all_edges():
            if edge.no_advance:
                continue

            if edge.key is None or isinstance(edge.key, int):
                continue

            terminated.append(edge.key[0])

        result = Lattice(terminated)
        self.terminated_cache[node] = result
        return result

    def visit(self, node: Node, path: list[Node]) -> None:
        value = self.lattice[node]
        debug(f"enter {node.name!r}, value is {value.to_json()!r}")

        terminated = self.terminated_cache.get(node, EMPTY_VALUE)
        if not terminated.is_equal(EMPTY_VALUE):
            debug(f"subtract terminated {node.name} {terminated.to_json()!r}")
            value = value.subtract(terminated)
            if value.is_equal(EMPTY_VALUE):
                debug("terminated everything")
                return

        for edge in node.get_all_edges():
            if not edge.no_advance:
                continue

            edge_value = value
            if edge.key is None or isinstance(edge.key, int):
                pass
            else:
                edge_value = edge_value.intersect(Lattice([edge.key[0]]))

            if edge_value.is_equal(EMPTY_VALUE):
                continue

            if edge.node in path:
                if not path:
                    raise Error(
                        f'Detected loop in "{edge.node.name}" through "{edge.node.name}"'
                    )
                raise Error(
                    'Detected loop in "'
                    + edge.node.name
                    + '" through chain '
                    + (" -> ").join(['"' + parent.name + '"' for parent in path])
                )

            self.visit(edge.node, path + [edge.node])
        debug(f"leave {node.name!r}")
