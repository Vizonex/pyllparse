import re
import sys
from dataclasses import dataclass
from typing import Callable, Literal, Optional, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

_P = ParamSpec("_P")
_T = TypeVar("_T")


Signature = ["match", "value"]


def toBuffer(value: Union[str, int]):
    if isinstance(value, str):
        res = value
    else:
        assert 0 <= value and value <= 0xFF
        res = [value]
    assert len(res) >= 1
    return res


# TODO Add text validataion...


def validate_text(init: Callable[_P, _T]) -> Callable[_P, _T]:
    def is_valid(args, kwargs):
        if kwargs.get("field"):
            field = kwargs["field"]
            if re.search(r"[//\s\\]+", field):
                raise TypeError(
                    f'Can\'t access internal field because the field: "{field}" conatins invalid characters'
                )
        return init(args, kwargs)

    return is_valid


class Code:
    def __init__(self, signature: Literal["match", "value"], name: str) -> None:
        assert signature in Signature, "Invalid signature %s" % signature

        self.signature = signature
        self.name = name

    def __hash__(self):
        return hash(self.signature + self.name)


class Field(Code):
    def __init__(
        self, signature: Literal["match", "value"], name: str, field: str
    ) -> None:
        self.field = field
        # if re.search(r"[//\s\\]+",field):
        #     raise TypeError(f"Can\'t access internal field from user code because the field: {name} conatins invalid characters")
        super().__init__(signature, name + "_" + field)


class FieldValue(Field):
    def __init__(
        self, signature: Literal["match", "value"], name: str, field: str, value: int
    ) -> None:
        self.value = value
        super().__init__(signature, name, field)


class And(FieldValue):
    def __init__(self, field: str, value: int) -> None:
        super().__init__("match", "and", field, value)


class IsEqual(FieldValue):
    def __init__(self, field: str, value: int) -> None:
        super().__init__("match", "is_equal", field, value)


class Load(Field):
    def __init__(self, field: str) -> None:
        super().__init__("match", "load", field)


class _Match(Code):
    """Refers to the Code's Match Not the Node's Match"""

    def __init__(self, name: str) -> None:
        super().__init__("match", name)


@dataclass
class IMulAddOptions:
    base: int
    max: int
    signed: bool = False


class MulAdd(Field):
    def __init__(self, field: str, base: int, max: int, signed: bool = False) -> None:
        self.options = IMulAddOptions(base, max, signed)
        super().__init__("value", "mul_add", field)


class Or(FieldValue):
    def __init__(self, field: str, value: int) -> None:
        super().__init__("match", "or", field, value)


# class Span(Match):
#     def __init__(self, name: str) -> None:
#         super().__init__(name)


class Store(Field):
    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__("value", "store", field)


class Test(FieldValue):
    def __init__(self, field: str, value: int) -> None:
        super().__init__("match", "test", field, value)


class Update(FieldValue):
    def __init__(self, field: str, value: int) -> None:
        super().__init__("match", "update", field, value)


class Value(Code):
    def __init__(self, name: str) -> None:
        super().__init__("value", name)


# Nodes...


class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.otherwiseEdge: Optional["Edge"] = None
        self.privEdges: list["Edge"] = []

    def key(self):
        """reversed for sorting to prevent python from creating artificial randomness"""
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def otherwise(self, node: "Node"):
        if self.otherwiseEdge:
            raise TypeError("Node Already has an 'otherwise' or 'skipto'")
        self.otherwiseEdge = Edge(node, True, None, None)
        return self

    def skipTo(self, node: "Node"):
        if self.otherwiseEdge:
            raise TypeError("Node Already has an 'otherwise' or 'skipto'")
        self.otherwiseEdge = Edge(node, False, None, None)
        return self

    def getOtherwiseEdge(self):
        return self.otherwiseEdge

    def getEdges(self):
        """Returns non if object is empty"""
        return None if self.privEdges == [] else self.privEdges

    def getAllEdges(self):
        r"Get list of all edges (including otherwise, if present)"
        res = self.privEdges
        if not self.otherwiseEdge:
            return res
        else:
            # Concate DO NOT ADD TO RES!!!!

            return res + [self.otherwiseEdge]

    def __iter__(self):
        if self.privEdges != []:
            for e in self.privEdges:
                yield e

    def addEdge(self, edge: "Edge"):
        assert isinstance(edge.key, (int, str)) or edge.key

        if len(self.privEdges) > 0:
            assert edge.key not in [e.key for e in self.privEdges]
        self.privEdges.insert(0, edge)


# TODO Add strict type checking to \"Pause.__init__\"" parameters to prevent the
# bypassing arbtrary values


class Pause(Node):
    def __init__(self, code: int, reason: str) -> None:
        self.code = code
        self.reason = reason
        super().__init__("pause")

    def skipTo(self, node: "Node"):
        """`WARNING!` `Pause.skipTo()` IS NOT SUPPORTED AND WILL IMMEDIATELY THROW AN `Execption` IF YOU DO IT"""
        raise Exception("Not supported in Pause Class, please use '.otherwise'")


class Comsume(Node):
    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__("consume_" + field)


class Error(Node):
    def __init__(self, code: int, reason: str) -> None:
        super().__init__("error")
        # print(code)
        assert isinstance(code, int), "code is supposed to be an int not %s" % (
            type(code).__name__
        )
        self.code = code
        self.reason = reason

    def otherwise(self, node: "Node"):
        raise TypeError("Not Supported")

    def skipTo(self, node: "Node"):
        raise TypeError("Not Supported")


class Invoke(Node):
    def __init__(self, code: Code, IInvokeMap: dict[int, Node]) -> None:
        self.code = code
        super().__init__("invoke_" + code.name)
        for numKey, targetNode in IInvokeMap.items():
            if isinstance(numKey, int) and targetNode is None:
                raise TypeError(
                    "Invoke's map keys must be integers and values must not be left blank!"
                )
            self.addEdge(Edge(targetNode, True, numKey, None))


# -- Transfroms --

TransformName = ["to_lower_unsafe", "to_lower"]


class Transform:
    def __init__(self, name: str) -> None:
        assert name in TransformName
        self.name = name


class ToLower(Transform):
    def __init__(self) -> None:
        super().__init__("to_lower")


class ToLowerUnsafe(Transform):
    def __init__(self) -> None:
        super().__init__("to_lower_unsafe")


class TransfromCreator:
    """API For Character transformations used in::

    p.node().transform(...)"""

    def toLowerUnsafe(self):
        return ToLowerUnsafe()

    def toLower(self):
        return ToLower()


# def toBuffer(value:Union[int,str,bytes]) -> bytes:
#     """Returns a bytes to use when making switch cases in C..."""
#     if isinstance(value,bytes):
#         res = value
#     elif isinstance(value,str):
#         res = value.encode("utf-8","surrogateescape")
#     else:
#         if not (0 <= value and value <= 0xff):
#             raise BufferError("Invalid byte value")
#         res = chr(value).encode("utf-8","surrogateescape")
#     if len(res) >= 1:
#         raise AssertionError("Invalid key length")
#     return res


MatchSingleValue = TypeVar("MatchSingleValue", str, int, bytes)


class Edge:
    def __init__(
        self,
        node: Node,
        noAdvance: bool,
        key: Optional[Union[int, str]],
        value: Optional[int],
    ) -> None:
        self.node = node
        self.noAdvance = noAdvance

        self.key = key.encode() if isinstance(key, str) else key
        self.value = value

        # Validation...
        if isinstance(node, Invoke):
            # NOTE In python 0 is seen as none so simply checking for it is not an option!
            # in llparse This bould be is it's equvilent of "if (value === undefined) {""
            if (not isinstance(value, int)) and value is None:
                if node.code.signature != "match":
                    raise TypeError(
                        f"Invalid invoke code signature : {node.code.signature} is not match"
                    )

            elif node.code.signature != "value":
                raise TypeError(
                    f"Invalid invoke code signature : {node.code.signature} is not value"
                )

            elif noAdvance:
                if key and not isinstance(key, int) and len(key) != 1:
                    raise TypeError("Only 1-char keys are allowed in 'noAdvance' edges")

        else:
            # print(node)
            if not isinstance(node, Node):
                raise TypeError(
                    f"Attempted to pass value to non-Invoke node as :{type(node)}"
                )

    def __hash__(self) -> int:
        return hash(self.node.name)

    # Very Big Function but it works....
    @staticmethod
    def compare(a: "Edge", b: "Edge"):
        return a.key == b.key


# This is where the fun begins...


class Match(Node):
    """This node matches characters/sequences and forwards the execution according
    to matched character with optional attached value (See `.select()`)"""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.transformFn: Optional[Transform] = None

    def transform(self, transformFn: Transform):
        self.transformFn = transformFn
        return self

    def match(self, value: Union[str, int, list[int], list[str]], next: Node):
        """
        Match sequence/character and forward execution to `next` on success,

        consuming matched bytes of the input.

        No value is attached on such execution forwarding, and the target node

        **must not** be an `Invoke` node with a callback expecting the value.

        Parameters
        ----------

        - `value`  Sequence/character to be matched

        - `next`  Target node to be executed on success.
        """
        # if isinstance(value,str):
        #     value = value.encode("utf-8")
        if isinstance(value, list) and len(value) > 1:
            for i in value:
                self.match(i.encode("utf-8") if isinstance(i, str) else i, next)
            return self

        edge = Edge(next, False, value, None)
        self.addEdge(edge)
        return self

    def peek(self, value: Union[str, int, list[Union[str, int]]], next: Node):
        """Match character and forward execution to `next` on success
        without consuming one byte of the input.

        No value is attached on such execution forwarding, and the target node
        must not be an `Invoke` with a callback expecting the value.

        Parameters
        ----------

        - `value` Character to be matched
        - `next`  Target node to be executed on success."""

        if isinstance(value, list):
            for i in value:
                self.peek(i, next)
            return self

        if (isinstance(value, str)) and (len(value) != 1):
            raise AssertionError(
                ".peek() accepts only singular character keys "
                + f"perhaps you meant to say : {value.split()}"
                if isinstance(str, value)
                else ""
            )
        edge = Edge(next, True, value, None)
        self.addEdge(edge)
        return self

    # You may be asking why I'm not using Other types of Errors why assertion errors when there is not assert?
    # It's beacuse it wanted to stay close to the orginal llparse library for better troubleshooting and error diagnosis - Vizonex
    def select(
        self,
        keyOrDict: Union[int, str, dict[str, int]],
        valueOrNext: Optional[Union[int, Node]] = None,
        next: Optional[Node] = None,
    ):
        """Match character/sequence and forward execution to `next` on success
        consumed matched bytes of the input.

        Value is attached on such execution forwarding, and the target node
        must be an `Invoke` with a callback expecting the value.

        Possible signatures:

           `.select(key, value [, next ])`
           `.select({ key: value } [, next])`

        - `keyOrDict` Either a sequence to match, or a dictionary from sequences to values
        - `valueOrNext` Either an integer value to be forwarded to the target node, or an otherwise node
        - `next` Convenience param. Same as calling `.otherwise(...)`"""
        if isinstance(keyOrDict, dict):
            if not isinstance(valueOrNext, Node):
                raise AssertionError("Invalid next argument of '.select()'")
            if next:
                raise AssertionError("Invalid argument count of '.select()'")

            next = valueOrNext
            for numKey, key in keyOrDict.items():
                # print(f"{key}:{numKey}:{next}")
                self.select(numKey, keyOrDict[numKey], next)

            return self

        # select(key,value,next)
        assert isinstance(valueOrNext, int), (
            "value Argument should be an integer not, %s" % (type(valueOrNext).__name__)
        )
        # raise AssertionError("Invalid `value` of argument .select()")
        assert next is not None, "Invalid `next` of argument .select()"
        value = int(valueOrNext)
        key = toBuffer(keyOrDict)
        edge = Edge(next, False, key, value)
        if self.name == "nmethods":
            print(f"{self.name}: {key} -> {edge.node.name}")

        self.addEdge(edge)
        return self

    def getTransform(self):
        return self.transformFn


class _Span(Match):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name)


class SpanStart(Node):
    def __init__(self, span: "Span") -> None:
        self.span = span
        super().__init__(f"span_start_{span.callback.name}")


class SpanEnd(Node):
    def __init__(self, span: "Span") -> None:
        self.span = span
        super().__init__(f"span_end_{span.callback.name}")


class Span:
    def __init__(self, callback: _Span) -> None:
        self.callback = callback
        # NOTE Both SpanStart and SpanEnd have hash
        # functions inherited from Node so no need to
        # add anything special over there...
        self.startCache: dict[Node, SpanStart] = {}
        self.endCache: dict[Node, SpanEnd] = {}

    # NOTE The thing that I'm greatful for seen in the orginal llparse typescript library
    # is the ability to fork out and create all sorts of nodes whenever possible, these two
    # functions personally demonstrate just that branching out concept alone - Vizonex

    def start(self, otherwise: Optional[Node] = None):
        if otherwise and self.startCache.get(otherwise):
            return self.startCache[otherwise]

        res = SpanStart(self)

        if otherwise:
            res.otherwise(otherwise)
            self.startCache[otherwise] = res

        return res

    def end(self, otherwise: Optional[Node] = None):
        if otherwise and self.endCache.get(otherwise):
            return self.endCache[otherwise]

        res = SpanEnd(self)

        if otherwise:
            res.otherwise(otherwise)
            self.endCache[otherwise] = res

        return res


class Reachability:
    @staticmethod
    def build(root: Node) -> list[Node]:
        res: set[Node] = set()
        queue = [root]

        while queue:
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


# On_User_Key = Match("On_User_Key")

# On_User_Value = Match("On_User_Value")

# data_extraction = Node("On_Data_Extraction").skipTo(On_User_Key)

# node = Match("On_Level_Comment").skipTo(data_extraction)


# On_User_Key.match(["0","1","2","3","4","5","6","7","8","9"],On_User_Key)\
#     .peek("~",On_User_Value)\
#     .otherwise(Error(1,"[BAD KEY] Some retard decided to hijack your server! Oh SHIT!"))


# print([d.node.name for d in node.getAllEdges()])
