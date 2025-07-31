from .pyfront.front import IWrap
from .pyfront.nodes import Node


class Enumerator:
    @staticmethod
    def getAllNodes(root: IWrap[Node]):
        nodes: set[IWrap[Node]] = set()
        queue: list[IWrap[Node]] = [root]

        while queue:
            node = queue.pop()
            for slot in node.ref.getSlots():
                if slot.node in nodes:
                    continue

                nodes.add(slot.node)
                queue.append(slot.node)

        return list(nodes)
