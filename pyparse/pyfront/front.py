

# NOTE The Difference is that names already 
# taken by python standard library modules 
# are Renamed to something else.... - Vizonex


from typing import TypeVar, Union, Optional, Generic

T = TypeVar("T")

Signature = TypeVar("Signature",bytes,str)


from dataclasses import dataclass

# export interface IWrap<T> {
#   readonly ref: T;
# }


class IWrap(Generic[T]):
    def __init__(self,ref:T) -> None:
        self.ref = ref 
        
    def __hash__(self) -> int:
        return hash(self.ref)

def toCacheKey(value:Union[int,bool]) -> str:
    if isinstance(value,int):
        return "m" + (-value) if value < 0 else "%i" % value
    elif isinstance(value,bool):
        return "true" if value == True else "false"
    else:
        raise ValueError(f"Unsupported value: {value}")


class Code:
    def __init__(self,signature : Signature,cacheKey:str ,name:str):
        self.signature = signature
        self.cacheKey = cacheKey
        self.name = name 



class External(Code):
    """Inherits from the `Code` class as a subclass of `Code`"""
    def __init__(self, signature: Signature, name: str):
        super().__init__(signature, "external_" + name,name)



class Field(Code):
    """Inherits from `Code`"""
    def __init__(self, signature: Signature, cacheKey: str, name: str,field:str):
        self.field = field 
        super().__init__(signature, cacheKey, name)
        


class FieldValueError(Exception):
    """FieldValue `value` must be integer"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)




class FieldValue(Field):
    def __init__(self, 
        signature: Signature, 
        cacheKey: str, 
        name: str, 
        field: str,
        value:int):

        self.value = value 
        if not isinstance(self.value,int):
            raise FieldValueError(f"FieldValue \"value\" must be integer not {type(self.value)}")
        super().__init__(signature, cacheKey, name, field)

class And(FieldValue):
    """a Subclass of `FieldValue`"""
    # TODO Reverse Engineer toCacheKey
    def __init__(self, name: str, field: str, value: int):
        super().__init__("match", f"and_{field}_{toCacheKey(value)}", name, field, value)

class IsEqual(FieldValue):
    def __init__(self, name: str, field: str, value: int):
        super().__init__("match", f"is_equal_{field}_{toCacheKey(value)}", name, field, value)

class Load(Field):
    """Subclass of Field"""
    def __init__(self, name: str, field: str):
        super().__init__("match", f"load_{field}", name, field)

class Match(External):
    def __init__(self, name: str):
        super().__init__("match", name)



@dataclass
class IMulAddOptions:
    base:int 
    max:Optional[int]
    signed:bool 

def toOptionsKey(options:IMulAddOptions) -> str:
    res = f"base_{toCacheKey(options.base)}"
    if options.max:
        res += f"_max_{toCacheKey(options.max)}"
    if options.signed:
        res += f"_signed_{toCacheKey(options.signed)}"
    return res 


class MulAdd(Field):
    def __init__(self, name: str, field: str,options:IMulAddOptions):
        self.options = options
        super().__init__("value", f"mul_add_{field}_{toOptionsKey(options)}", name, field)


class Or(FieldValue):
    def __init__(self, name: str, field: str, value: int):
        super().__init__("match",f"or_{field}_{toCacheKey(value)}", name, field, value)



class Span(External):
    """A `Span` Class"""
    def __init__(self, name: str):
        self.name = name 
        super().__init__("span", name)
    


class SpanField:
    def __init__(self,index:int,callbacks:list[IWrap[Span]]) -> None:
        self.index = index
        self.callbacks:list[IWrap[Span]] = callbacks
        pass
    


class Store(Field):
    def __init__(self, name: str, field: str):
        super().__init__("value", f"store_{field}", name, field)


class Test(FieldValue):
    def __init__(self,name: str, field: str, value: int):
        super().__init__("match",f"test_{field}_{toCacheKey(value)}", name, field, value)

class Update(FieldValue):
    def __init__(self, name: str, field: str, value: int):
        super().__init__("match",f"update_{field}_{toCacheKey(value)}", name, field, value)
    
class Value(External):
    def __init__(self, name: str):
        super().__init__('value', name)


@dataclass
class IUniqueName:
    name:str 
    originalName:str 


class Identifier:
    def __init__(self,prefix:str,postfix:str = "") -> None:
        self.ns : set[str] = set()
        self.prefix = prefix
        self.postfix = postfix

    def id(self,name:str) -> IUniqueName:
        target = self.prefix + name + self.postfix
        if target in self.ns:
            i = 0
            for i in range(1,len(self.ns)):
                if not (target + "_%i" % i) in self.ns:
                    break
            
            target += ("_%i" % i)
        
        self.ns.add(target)

        return IUniqueName(name=target,originalName=name)


