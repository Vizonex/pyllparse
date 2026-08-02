from .node import Node


class Reachability:
    __slots__ = ()

    def build(self, root: Node) -> list[Node]:
        res: set[Node] = set()
        res_add = res.add
        queue = [root]
        while queue:
            node = queue.pop()
            if node in res:
                continue

            res_add(node)
            for edge in node:
                queue.append(edge.node)

            # little shortcut that is not in the typescript code.
            if otherwise := node.get_otherwise_edge():
                queue.append(otherwise.node)

        return list(res)
