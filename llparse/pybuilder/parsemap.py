from ..pybuilder.main_code import Edge, Node


class ParserMap:
    def __init__(self, root: Node) -> None:
        self.root = root

    def Jsonize(self):
        queue = [self.root]
        seen: set[Node] = set()
        while queue:
            node = queue.pop()

            if node in seen:
                continue

            seen.add(node)

            for edge in node:
                queue.append(edge.node)

            otherwise = node.getOtherwiseEdge()
            if otherwise:
                queue.append(otherwise.node)

        return [(s.__dict__, list(map(self.get_edges, s))) for s in seen]

    def get_edges(self, edge: Edge):
        if not edge:
            return {}
        data = edge.__dict__
        data["node"] = edge.node
        return data
