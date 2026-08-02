from .node import Empty, Node
from .wrap import Wrap


# There's no point to having a Peephole class it's been optimized
# into a single function
def optimize(root: Wrap[Node], nodes: list[Wrap[Node]]) -> Wrap[Node]:
    changed = set(nodes)

    while changed:
        previous = changed.copy()
        changed.clear()

        for node in previous:
            # Combined 2 functions from typescript llparse to
            # just needing 1, this refactoring change allows for more speed. and less costly calls..
            altered = False

            for slot in node.ref.get_slots():
                if not isinstance(slot.node.ref, Empty) or not slot.node.ref.otherwise:
                    continue

                otherwise = slot.node.ref.otherwise

                # Node skips so we cannot optimize
                if not otherwise.no_advance:
                    continue

                slot.node.ref = otherwise.node.ref
                altered = True

            if altered:
                changed.add(node)

    while isinstance(root.ref, Empty):
        if not root.ref.otherwise or not root.ref.otherwise.no_advance:
            break
        root = root.ref.otherwise.node

    return root


__all__ = ("optimize",)
