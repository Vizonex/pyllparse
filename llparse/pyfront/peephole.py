from .code import IWrap
from ..pyfront.nodes import Empty, Node

WrapNode = IWrap[Node]
WrapList = list[WrapNode]


# TODO (Vizonex) Make peephole into 2 seperate functions instead of a class to
# Optimize everything down further...
class Peephole:
    def optimize(self, root: WrapNode, nodes: WrapList) -> WrapNode:
        changed = set(nodes)

        while changed:
            previous = changed.copy()
            changed.clear()

            for node in previous:
                # Combined 2 functions from node-js llparse to
                # just needing 1 this refactoring change allows for more speed. and less costly calls..
                altered = False

                for slot in node.ref.getSlots():
                    if (
                        not isinstance(slot.node.ref, Empty)
                        or not slot.node.ref.otherwise
                    ):
                        continue

                    otherwise = slot.node.ref.otherwise

                    # Node skips so we cannot optimize
                    if not otherwise.noAdvance:
                        continue

                    slot.node.ref = otherwise.node.ref
                    altered = True

                if altered:
                    changed.add(node)

        while isinstance(root.ref, Empty):
            if not root.ref.otherwise or not root.ref.otherwise.noAdvance:
                break
            root = root.ref.otherwise.node

        return root
