from collections import deque

from .node import Node
from .wrap import Wrap


def get_all_nodes(root: Wrap[Node]) -> list[Wrap[Node]]:
    nodes: set[Wrap[Node]] = set()
    queue = deque([root])

    while queue:
        node = queue.pop()
        for slot in node.ref.get_slots():
            slot_node = slot.node

            if slot_node in nodes:
                continue
            nodes.add(slot_node)
            queue.append(slot_node)

    return list(nodes)
