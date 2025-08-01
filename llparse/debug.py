from .pybuilder import Node


class Debugger:
    @staticmethod
    def getAllNodes(root: Node):
        nodes: set[Node] = set()
        queue: list[Node] = [root]

        while queue:
            node = queue.pop()
            print(node.name)
            if node.name == "nmethods":
                print(node.getEdges())
            if edges := node.getEdges():
                for slot in edges:
                    if slot.node in nodes:
                        continue

                    nodes.add(slot.node)
                    queue.append(slot.node)

        return list(nodes)
