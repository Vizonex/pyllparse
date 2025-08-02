from pathlib import Path
from typing import Optional, Union

from .pybuilder.main_code import Edge, Node

# TODO: Fix all graphs and more It's currently broken...

COLOR_ADVANCE = "black"
COLOR_NO_ADVANCE = "blue"
COLOR_INVOKE = "green"
COLOR_OTHERWISE = "red"


class Dot:
    """Used to create a graphviz of your parser"""

    def __init__(self) -> None:
        self.idCache: dict[Node, str] = {}
        self.ns: set[str] = set()

    def dump_to_file(self, filename: Union[str, Path], root: Node):
        open(filename, "w").write(self.build(root))

    def build(self, root: Node):
        res = ""
        res += "digraph {\n"
        res += '  concentrate="true"\n'

        for node in self.enumerateNodes(root):
            res += self.buildNode(node)

        res += "}\n"
        return res

    def enumerateNodes(self, root: Node):
        queue = [root]
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

        return seen

    def buildNode(self, node: Node):
        res: str = ""
        edges = list(node)
        otherwise = node.getOtherwiseEdge()
        if otherwise:
            edges.append(otherwise)

        advance: dict[Node, list[Edge]] = {}
        noAdvance: dict[Node, list[Edge]] = {}

        for edge in edges:
            targets = noAdvance if edge.noAdvance else advance

            if targets.get(edge.node):
                targets[edge.node].append(edge)
            else:
                targets[edge.node] = [edge]

        res += self.buildEdgeMap(node, advance, "advance")
        res += self.buildEdgeMap(node, noAdvance, "noAdvance")

        return res

    def buildEdgeMap(self, node: Node, Map: dict[Node, list[Edge]], kind: str):
        res = ""
        for target, edges in Map.items():
            otherwise: list[Edge] = []
            single: list[Edge] = []
            sequence: list[Edge] = []
            code: list[Edge] = []

            for edge in edges:
                if not edge.key:
                    otherwise.append(edge)
                elif isinstance(edge.key, int):
                    code.append(edge)
                elif len(edge.key) == 1:
                    single.append(edge)
                else:
                    sequence.append(edge)
            labels: list[str] = []
            # print(target.name,otherwise,code,single,sequence)

            # end:int node:Node start:int
            ranges: list[dict[str, Union[int, Node]]] = []

            firstKey: Optional[int] = None
            lastKey: Optional[int] = None

            for edge in single:
                key = (
                    edge.key[0]
                    if isinstance(edge.key, (bytes, list))
                    else (
                        edge.key
                        if not isinstance(edge.key, str)
                        else edge.key.encode()[0]
                    )
                )

                if lastKey and lastKey == key - 1:
                    lastKey = key
                    continue

                if lastKey is not None:
                    ranges.append({"start": firstKey, "end": lastKey, "node": target})

                firstKey = key
                lastKey = key

            if lastKey:
                assert firstKey
                ranges.append({"start": firstKey, "end": lastKey, "node": target})

            for _range in ranges:
                labels.append(self.buildRangeLabel(node, _range))

            for edge in sequence:
                labels.append(self.buildEdgeLabel(node, edge))

            for edge in code:
                labels.append(self.buildInvokeLabel(node, edge))

            for edge in otherwise:
                labels.append(self.buildOtherwiseLabel(node, edge))

            color = COLOR_NO_ADVANCE if kind == "noAdvance" else COLOR_ADVANCE

            res += (
                f'  "{self.id(node)}" -> "{self.id(target)}"'
                f'[label="{"|".join(labels)}" color="{color}" decorate=true];\n'
            )

        return res

    def buildRangeLabel(self, node: Node, _range: dict[str, Union[int, Node]]):
        start = self.buildChar(_range["start"])
        end = self.buildChar(_range["end"])
        # return range.start === range.end ? start : `${start}:${end}`;
        return start if _range["start"] == _range["end"] else f"{start}:{end}"

    def buildEdgeLabel(self, node: Node, edge: Edge):
        return f"{self.buildBuffer(edge.key)}"

    def buildInvokeLabel(self, node: Node, edge: Edge):
        return f"code={int(edge.key)}"

    def buildOtherwiseLabel(self, node: Node, edge: Edge):
        return "otherwise" if edge.noAdvance else "skipTo"

    def buildChar(self, code: int):
        if not isinstance(code, int):
            code = ord(code)
        if code == 0x0A:
            return self.escape("'\\n'")
        if code == 0x0D:
            return self.escape("'\\r'")
        if code == 0x09:
            return self.escape("'\\t'")

        if 0x20 <= code and code <= 0x7E:
            return self.escape(chr(code))
        # I Don't know how accurate this is but it was worth a shot
        res = hex(code)
        return res

    def buildBuffer(self, buffer: bytes):
        s = buffer.decode() if isinstance(buffer, bytes) else buffer
        return (
            "'"
            + s.replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
            .replace("\\", "\\$1")
            + "'"
        )

    def id(self, node: Node):
        if self.idCache.get(node):
            return self.idCache[node]

        res = node.name
        if res in self.ns:
            for i in range(len(self.ns)):
                if (res + "_%i" % i) in self.ns:
                    break

            res += "_%i" % i

        self.ns.add(res)
        res = self.escape(res)
        self.idCache[node] = res
        return res

    def escape(self, value: str):
        return "'" + value.replace("\\", "\\$1").replace('"', "\\$1") + "'"
