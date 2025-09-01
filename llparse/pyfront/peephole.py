from ..pyfront.front import IWrap
from ..pyfront.nodes import Empty, Node

WrapNode = IWrap[Node]
WrapList = list[WrapNode]


# TODO (Vizonex) Make peephole into 2 seperate functions instead of a class to
# Optimize everything down further...
class Peephole:
    def optimize(self, root: WrapNode, nodes: WrapList):
        changed = set(nodes)

        while changed:
            previous = changed
            changed = set()

            for node in previous:
                if self.optimizeNode(node):
                    changed.add(node)

        while isinstance(root.ref, Empty):
            if not root.ref.otherwise or not root.ref.otherwise.noAdvance:
                break
            root = root.ref.otherwise.node

        return root

    def optimizeNode(self, node: WrapNode):
        changed = False
        for slot in node.ref.getSlots():
            # TODO Find an Actual way to check that a Node maybe empty...
            if not isinstance(slot.node.ref, Empty) or not slot.node.ref.otherwise:
                continue

            otherwise = slot.node.ref.otherwise

            # Node skips so we cannot optimize
            if not otherwise.noAdvance:
                continue

            slot.node.ref = otherwise.node.ref

            changed = True
        return changed
