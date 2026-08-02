from typing import Literal

from . import code, transform
from . import node as _node
from .edge import Edge
from .loop_checker import LoopChecker
from .property import Property, PropertyType, PropertyTypes
from .reachability import Reachability
from .span import Span
from .span_allocator import ISpanAllocatorResult, SpanAllocator
from .unpack_creator import StructUnpack, UnpackCreator

node = _node

__all__ = (
    "Builder",
    "Edge",
    "ISpanAllocatorResult",
    "LoopChecker",
    "Property",
    "PropertyType",
    "Reachability",
    "Span",
    "SpanAllocator",
    "code",
    "node",
    "transform",
)

code_span = code.Span
Unpack = _node.Unpack


# TODO (Vizonex) Add more Documentation later , I got tired of it...
class Builder:
    __slots__ = ("code", "priv_properties", "transform", "unpack_creator")

    def __init__(self) -> None:
        self.code = code.Creator()
        " API for creating external callbacks and intrinsic operations."
        self.transform = transform.Creator()
        self.priv_properties: dict[str, Property] = {}
        self.unpack_creator = UnpackCreator()

    def node(self, name: str) -> _node.Match:
        return _node.Match(name)

    def error(self, errorCode: int, reason: str):
        return _node.Error(errorCode, reason)

    def invoke(
        self,
        fn: "code.base.Code",
        map: dict[int, _node.Node] | _node.Node | None = None,
        otherwise: _node.Node | None = None,
    ):
        if not map:
            res = _node.Invoke(fn, {})

        elif isinstance(map, node.Node):
            res = _node.Invoke(fn, {})
            otherwise = map

        else:
            res = _node.Invoke(fn, map)

        if otherwise:
            res.otherwise(otherwise)

        return res

    def consume(self, field: str):
        return _node.Consume(field)

    def pause(self, errorCode: int, reason: str):
        return _node.Pause(errorCode, reason)

    def span(self, callback: code_span) -> Span:
        return Span(callback)

    def property(self, ty: Literal["i8", "i16", "i32", "i64", "ptr"], name: str):
        if ty not in PropertyTypes:
            raise TypeError(f"ty:{ty} is not an existing Parser Property")

        if name in self.priv_properties:
            raise RuntimeError(f"Duplicate property with name:{name}")

        self.priv_properties[name] = Property(ty, name)

    def properties(self) -> list[Property]:
        """Return list of all allocated properties in parser's state."""
        return list(self.priv_properties.values())

    def intBE(self, field: str, bits: int):
        """
        :param field: State's property name
        :param bits: Number of bits to use

        """
        return Unpack(field, bits, True, False)

    def intLE(self, field: str, bits: int):
        """
        return a node for unpacking arrays to integers

        :param field: State's property name
        :param bits: Number of bits to use
        """
        return Unpack(field, bits, True, True)

    def uintBE(self, field: str, bits: int):
        """
        return a node for unpacking arrays to integers

        :param field: State's property name
        :param bits: Number of bits to use
        """
        return Unpack(field, bits, False, False)

    def uintLE(self, field: str, bits: int):
        """
        return a node for unpacking arrays to integers

        :param field: State's property name
        :param bits: Number of bits to use
        """
        return Unpack(field, bits, False, True)

    def unpack(self, field: str, fmt: str):
        """Enables unpacking in python struct notation
        they are mapped as.

        - value, type in rust notation, bit length
        - 'b' i8, 1
        - 'c' i8, 1
        - '?' bool, 1
        - 'h' i16, 2
        - 'i' i32, 4
        - 'l' i32, 4
        - 'q' i64, 8
        - 'B' u8, 1
        - 'H' u16, 2
        - 'I' u32, 4
        - 'L' u32, 4
        - 'Q' u64, 8

        These ones are custom and not apart of CPython at all.
        They are added incase only 3 bits are needed. They
        are used to describe a hybrid (H was already taken by short so will use a y)
        - 'y', i24, 3
        - 'Y', u24, 3

        :param field: the property's name
        :param fmt: the struct format as described above
        """
        return Unpack.from_format(field, fmt)

    def unpack_structure(self, fmt: str) -> StructUnpack:
        """Provides an unpackable structure to lazily unpack into different paths.
        :param fmt: format of the nodes
            `name:format|name:format`
        """
        return self.unpack_creator.struct(fmt)

    # XXX: String annotations needed due to VSCode + Pyright wanting to screw around.
    def unpack_to(self, fmt: str, node: _node.Node) -> "_node.Unpack":
        """takes a list of elements as `property_name:value|etc...`
        :param fmt: format of the nodes
            `name:format|name:format`
        :param node: the node to skip to afterwards
            it is required due to the way all of this works.
        """
        return self.unpack_creator.with_format(fmt, node)
