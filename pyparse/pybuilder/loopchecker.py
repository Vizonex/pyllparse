
from typing import Any , Union , Literal
from ..pybuilder.main_code import Node 


MAX_VALUE = 256
WORD_SIZE = 32
SIZE = (MAX_VALUE // WORD_SIZE)
WORD_FILL = -1 | 0

assert MAX_VALUE % WORD_SIZE == 0 


# NOTE I think it's theroetically Possible to 
# Put Lattice Class into Cython as an optional replacement 
# for the Sake of speed in the near future once I've 
# figured out everything myself from a more deep brain 
# point of view/prespective... - Vizonex 


class Lattice:

    def __init__(self,value:Union[Any,list[int],Literal["empty"],Literal["any"]]) -> None:
        self.value = value 
        self.words :list[int] = []

        # allocate space by filling in data with zeros...

        for _ in range(SIZE):
            self.words.append(0)

        if len(value) > 1:
            for single in value:
                self.add(single)
    
    def __iter__(self):
        for i in range(MAX_VALUE):
            if self.check(i):
                yield i 
    
    def check(self,bit:int):
        if not (0 <= bit and bit < MAX_VALUE):
            raise AssertionError("Invalid Bit")
        index = (bit // WORD_SIZE) | 0
        off = bit % WORD_SIZE
        return self.words[index] & (1 << off) != 0
    

    def add(self,bit:int):
        bit = ord(bit) if isinstance(bit,str) else bit 
        if not (0 <= bit and bit < MAX_VALUE):
            raise AssertionError("Invalid Bit")
        
        index = (bit // WORD_SIZE)
        off = bit % WORD_SIZE;
        
        self.words[index] |= 1 << off 
    
    def union(self,other:"Lattice") -> "Lattice":
        result = Lattice("empty")
        
        for i in range(SIZE):
            result.words[i] = self.words[i] | other.words[i]
        
        return result

    def intersect(self,other:"Lattice") -> "Lattice":
        result = Lattice("empty")
        for i in range(SIZE):
            result.words[i] = self.words[i] & other.words[i]
        return result 
    
    def subtract(self,other:"Lattice") -> "Lattice":
        result = Lattice("empty")
        for i in range(SIZE):
            result.words[i] = self.words[i] & (~other.words[i])
        return result 

    def isEqual(self,other:"Lattice"):
        return True if (self.value == other.value) else False 
            
        
    def toJSON(self):
        isEmpty= True 
        isFull = True 
        for i in range(SIZE):
            if self.words[i] != 0:
                isEmpty = False 
            if self.words[i] != WORD_FILL:
                isFull = False 
        if isEmpty:
            return 'empty'
        if isFull:
            return 'any'
        return list(self)


class Reachability:
    def __init__(self) -> None:
        return 
    def build(self,root:Node) -> list[Node]:
        res:set[Node] = set()
        queue = [root]
        while len(queue) != 0:
            node = queue.pop()
            if node in res:
                continue
            res.add(node)
            for edge in node:
                queue.append(edge.node)
            otherwise = node.getOtherwiseEdge()
            if otherwise:
                queue.append(otherwise.node)
        
        return list(res)


EMPTY_VALUE = Lattice("empty")
ANY_VALUE = Lattice("any")

class LoopChecker:
    def __init__(self) -> None:
        self.lattice: dict[Node,Lattice] = {}
        self.terminatedCache: dict[Node,Lattice] = {}

    def clear(self,nodes:list[Node]):
        self.lattice.update({(node,EMPTY_VALUE) for node in nodes})
            

    def check(self,root:Node):
        r = Reachability()
        nodes = r.build(root)
        for node in nodes:
            self.clear(nodes)
            self.lattice[node] = ANY_VALUE
            changed: set[Node] = set([root])
            while len(changed) != 0:
                next = set()
                for changedNode in next:
                    self.propagate(changedNode, next)
                changed = next 
        
        self.visit(root,list(changed))
    
    def propagate(self,node:Node,changed:set[Node]):
        value = self.lattice[node]
        terminated : "Lattice" = self.terminate(node,value,changed)
        if terminated.value == EMPTY_VALUE.value:
            value = value.subtract(terminated)
            if value.isEqual(EMPTY_VALUE):
                return 
        
        keysbyTarget: dict[Node,Lattice] = dict()

        for edge in node.getAllEdges():
            if not edge.noAdvance:
                continue
                
            targetValue : Lattice
            if keysbyTarget.get(edge.node):
                targetValue = keysbyTarget[edge.node]
            else:
                targetValue = self.lattice.get(edge.node)
            
            if edge.key is None or isinstance(edge.key,int):
                targetValue = targetValue.union(value)
            else:
                # From peek()
                edgeValue = Lattice([edge.key[0]]).intersect(value)
                if edgeValue.isEqual(EMPTY_VALUE):
                    continue
                    
                targetValue = targetValue.union(edgeValue)
            keysbyTarget[edge.node] = targetValue

        for child, childValue in keysbyTarget.items():
            self.update(child,childValue,changed)
        # FINISHED! 

    def update(self , node:Node,newValue:Lattice,changed:set[Node]):
        value = self.lattice[node]
        if newValue.isEqual(value):
            return False 
        self.lattice[node] = newValue
        changed.add(node)
    

    def terminate(self,node:Node,value:Lattice,changed:set[Node]):
        if self.terminatedCache.get(node):
            return self.terminatedCache[node]
        
        terminated : list[int] = []

        for edge in node.getAllEdges():
            if edge.noAdvance:
                continue
            
            if edge.key == None or isinstance(edge.key,int):
                continue

            terminated.append(edge.key[0])
        
        result = Lattice(terminated)
        self.terminatedCache[node] = result 
        return result 
    
    def visit(self,node:Node,path:list[Node]):
        value = self.lattice[node]
        terminated = self.terminatedCache[node] if self.terminatedCache.get(node) else EMPTY_VALUE
        if terminated.isEqual(EMPTY_VALUE):
            value = value.subtract(terminated)
            if value.isEqual(EMPTY_VALUE):
                return 
        
        for edge in node.getAllEdges():
            if edge.noAdvance:
                continue
            edgeValue = value 
            if not (not edge.key or isinstance(edge.key,int)):
                edgeValue = edgeValue.intersect(Lattice([edge.key[0]]))
            
            if edgeValue.isEqual(EMPTY_VALUE):
                continue
                
            def indexOf(path:list,obj):
                try:
                    return path.index(obj)
                except:
                    return -1
            
            if indexOf(path,node) != -1:
                if len(path) == 0:
                    raise Exception(f"Detected a loop in \"{edge.node.name}\" though : {edge.node.name}")
                
                raise Exception("Detected loop in \"" + edge.node.name + "\" through chain " + (' -> ').join([ '\"'+ name.name +'\"' for name in path]))
            
            self.visit(edge.node,path.extend([edge.node]))







