
from .pybuilder.main_code import Edge, Node 

from typing import  Union, Optional

# TODO Vizonex Fix all graphs and more...

COLOR_ADVANCE = 'black'
COLOR_NO_ADVANCE = 'blue'
COLOR_INVOKE = 'green'
COLOR_OTHERWISE = 'red'


class Dot:
    """Used to create a graphviz of your parser"""
    def __init__(self) -> None:
        self.idCache:dict[Node,str] = {}
        self.ns : set[str] = set()
        
    
    def build(self,root:Node):
        res = ''
        res += "digraph {\n"
        res += "  concentrate=\"true\"\n"

        for node in self.enumerateNodes(root):
            res += self.buildNode(node)
        
        res += "}\n"
        return res 
    
    def enumerateNodes(self,root:Node):
        queue = [ root ]
        seen : set[Node] = set()

        while len(queue) != 0:
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
    
    def buildNode(self,node:Node):
        res:str = ""
        edges = list(node)
        otherwise = node.getOtherwiseEdge()
        if otherwise:
            edges.append(otherwise)
        
        advance: dict[Node,list[Edge]] = {}
        noAdvance : dict[Node,list[Edge]] = {}

        for edge in edges:
            targets = noAdvance if edge.noAdvance else advance

            if targets.get(edge.node):
                targets[edge.node].append(edge)
            else:
                targets[edge.node] = [edge]
            
        res += self.buildEdgeMap(node,advance,"advance")
        res += self.buildEdgeMap(node,advance,"noAdvance")

        return res 
    
    def buildEdgeMap(self,node:Node,Map: dict[Node,list[Edge]],kind:str):
        res = ''
        for target , edges  in Map.items():
            otherwise:list[Edge] = []
            single :list[Edge] = []
            sequence :list[Edge] = []
            code : list[Edge] = []

            for edge in edges:
                
                if not edge.key:
                    otherwise.append(edge)
                elif isinstance(edge.key,int):
                    code.append(edge)
                elif len(edge.key) == 1:
                    single.append(edge)
                else:
                    sequence.append(edge)
            labels: list[str] = []

            # end:int node:Node start:int 
            ranges : list[dict[str,Union[int,Node]]] = []

            firstKey : Optional[int] = None
            lastKey : Optional[int] = None

            for edge in single:
                # print(type(edge.key))
                key = edge.key[0] if isinstance(edge.key,bytes) else edge.key

                if lastKey and lastKey == key - 1:
                    lastKey = key 
                    continue

                if lastKey != None:
                    ranges.append({"start":firstKey,"end":lastKey,"node":target})

                firstKey = key 
                lastKey = key 
            
            if lastKey:
                ranges.append({"start":firstKey,"end":lastKey,"node":target})
            
            for _range in ranges:
                # print((_range,node))
                labels.append(self.buildRangeLabel(node,_range))

            for edge in sequence:
                labels.append(self.buildEdgeLabel(node,edge))
            
            for edge in code:
                labels.append(self.buildInvokeLabel(node,edge))
            
            for edge in otherwise:
                labels.append(self.buildOtherwiseLabel(node,edge))

            
            color = COLOR_ADVANCE if kind == 'noAdvance' else COLOR_NO_ADVANCE 
            res += f'  "{self.id(node)}" -> "{self.id(target)}"'\
                f"[label=\"{'|'.join(labels)}\" color=\"{color}\" decorate=true];\n"

        return res 
    
    def buildRangeLabel(self,node:Node,_range:dict[str,Union[int,Node]]):
        start = self.buildChar(_range["start"])
        end = self.buildChar(_range["end"])
        return start if _range["start"] == _range["end"] else f"{start}:{end}"
    
    def buildEdgeLabel(self,node:Node,edge:Edge):
        return f"{self.buildBuffer(edge.key)}"

    def buildInvokeLabel(self,node:Node,edge:Edge):
        return f"code={int(edge.key)}"

    def buildOtherwiseLabel(self,node:Node,edge:Edge):
        return 'otherwise' if edge.noAdvance else 'skipTo'

    def buildChar(self,code:int):
        if code == 0x0a:
            return self.escape('\'\\n\'')
        if code == 0x0d:
            return self.escape('\'\\r\'')
        if code == 0x09:
            return self.escape('\'\\t\'')
        
        if (0x20 <= code and code <= 0x7e):
            return self.escape('%i' % code)
        # I Don't know how accurate this is but it was worth a shot
        res = hex(code)
        if len(res):
            return res 

    def buildBuffer(self,buffer:bytes):
        s = buffer.decode() if isinstance(buffer,bytes) else buffer 
        return "'" + s.replace('\n','\\n').replace('\t','\\t').replace('\r','\\r').replace("\\","\\$1") + "'"
    
    def id(self,node:Node):
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
    
    def escape(self,value:str):
        return "'" + value.replace("\\","\\$1").replace("\"","\\$1") + "'"

# TODO FIX ALL BUFFERS BACK TO STRINGS!
