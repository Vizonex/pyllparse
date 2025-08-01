from .pybuilder.main_code import Node, Edge
from typing import Optional

from dataclasses import dataclass

@dataclass
class IEdge:
    # NOTE THIS SHOULD BE STRICTLY BYTES !!!
    key: bytes
    node: Node 
    noAdvance:bool
    value:Optional[int] = None 

    def __lt__(self,object):
        return self.key < object.key

# TODO RENAME TO TRIE!

class TireNode:
    """Mainly Used as an Abstract Object for typing"""
    def __init__(self) -> None:
        return 

class TireSequence(TireNode):
    def __init__(self,select:bytes,child:TireNode) -> None:
        self.select = select
        self.child = child
        

class ITireSingleChild:
    def __init__(self,key:int,noAdvance:bool,node:TireNode) -> None:
        self.key = key
        self.noAdvance = noAdvance
        self.node = node 

class TireEmpty(TireNode):
    def __init__(self,node:Node,value:int) -> None:
        self.node = node 
        self.value = value 

class TireSingle(TireNode):
    def __init__(self,children:list[ITireSingleChild],otherwise:Optional[TireEmpty] = None) -> None:
        self.children = children
        self.otherwise = otherwise 
        




# TODO Retry making Tire....

class Tire:
    def __init__(self,name:str) -> None:
        self.name = name 
    
    def build(self,edges:list[Edge]):
        if len(edges) == 0:
            return None 
        
        internalEdges: list[IEdge] = []
        
        for edge in edges:
            key = str(edge.key) if isinstance(edge.key,int) else edge.key 
            internalEdges.append(IEdge(key.encode("utf-8") if isinstance(key,str) else key ,edge.node,edge.noAdvance,edge.value))
        return self.level(internalEdges,[])
        
    def level(self,edges:list[IEdge],path:list[bytes]):
        first = edges[0].key
        last = edges[-1].key

        if len(edges) == 1 and len(edges[0].key) == 0:
            return TireEmpty(edges[0].node,edges[0].value)
        
        i = 0 
        for i in range(len(first)):
            if first[i] != last[i]:
                break

        if i > 1:
            # NOTE I think Idutny intended for these sequences 
            # to advance otherwise not having this would case a recursion error
            # This is why first[1:i] is used and not first[0:count] like in typescript...
            return self.sequence(edges,first[: i + 1 ],path)

        return self.single(edges,path) 

    def Slice(self,edges:list[IEdge],off:int):
        slice = [IEdge(edge.key[off:],edge.node,edge.noAdvance,edge.value) for edge in edges]
        return sorted(slice, key = lambda k: k.key)


    def sequence(self,edges:list[IEdge],prefix:bytes,path:list[bytes]):
        sliced = self.Slice(edges,len(prefix))
        assert not any([edge.noAdvance for edge in edges])
        child = self.level(sliced,path + [prefix])
        return TireSequence(prefix,child)
    
    def single(self,edges:list[IEdge],path:list[bytes]):

        if len(edges[0].key) == 0:
            if len(path) == 0:
                AssertionError(f'Empty root entry at "{self.name}"')
            if not (len(edges) == 1 or len(edges[1].key) != 0):
                err = f'Duplicate entries in "{self.name}" at: [' + (b", ".join(path).decode("utf-8")) + ']'
                
                raise AssertionError(err)


        keys : dict[int,list[IEdge]] = {} 

        for edge in edges:
            if len(edge.key) == 0:
                otherwise = TireEmpty(edge.node,edge.value)
                continue

            key = edge.key[0]

            if keys.get(key):
                keys[key].append(edge)
            else:
                keys[key] = [edge]
        
   
        otherwise = None 
        children : list[ITireSingleChild] = []

        for key, subEdges in keys.items():
            # TODO LOG FUNCTION's ARGUMENTS TO DETERMINE WEATHER OR NOT IT'S the Problem...
            # I think this maybe the problem now that I think about it...
            sliced = self.Slice(subEdges, 1)
   
            
            subPath = path + [chr(key).encode("utf-8")]

            noAdvance = any([e.noAdvance for e in subEdges])
            allSame = all([e.noAdvance == noAdvance for e in subEdges])
           
            if not (allSame or len(subEdges) == 0):
                err = f'Conflicting `.peek` and `.match` entries in "{self.name}" at: [' + (b", ".join(subPath).decode("utf-8")) + ']'
                raise TypeError(err)
            child = ITireSingleChild(key,noAdvance,self.level(sliced,subPath))
            children.append(child)

       
        return TireSingle(children,otherwise)




def test():
    t = b"data-to-buffer"

    for _ in range(2):
        t = t[1:4]
        print(t)

if __name__ == "__main__":
    test()