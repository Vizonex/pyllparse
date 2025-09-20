from typing import Literal, Optional, Union
from ..pybuilder import main_code as code

# typehinting node and code (TODO: Vizonex) Lets seperate the modules soon...
node = code
# from pydot import graph_from_dot_data


i8 = "i8"
i16 = "i16"
i32 = "i32"
i64 = "i64"
ptr = "ptr"


PropertyTypes = [i8, i16, i32, i64, ptr]


class Property:
    def __init__(self, ty: str, name: str) -> None:
        if ty not in PropertyTypes:
            raise Exception(
                f"Can't use property : {ty}  Because it is not a valid property type in ['i8' , 'i16' , 'i32' , 'i64' , 'ptr']"
            )
        if any([(True if n in name else False) for n in ["\\\\", "/", " "]]):
            raise Exception(
                f"Flag/Pointer Name:{name} cannot have spaces or other strange characters in C..."
            )
        self.name = name
        self.ty = ty


class Creator:
    """API for creating external callbacks and intrinsic operations."""

    def __init__(self) -> None:
        return

    # TODO (Vizonex): I think we could add a node for property copying from a to b
    # and addition and subtraction nodes like a counter unlike consume and I think the typescript
    # Library could have the same features as us. I seem to come up with new nodes often
    # which is a rare thing to see. :)

    # Thank goodness I can do C example documentation in here :) - Vizonex
    def match(self, name: str) -> code.Match:
        """Create an external callback that **has no** `value` argument.

        This callback can be used in all `Invoke` nodes except those that are
        targets of `.select()` method.

        C signature of callback must be:

        ```c
        int name(llparse_t* state,  char* p,     char* endp)
        ```

        Where `llparse_t` is parser state's type name.

        :param name: External function name.
        """
        return code._Match(name)

    def value(self, name: str) -> code.Value:
        """

        Create an external callback that **has** `value` argument.

        This callback can be used only in `Invoke` nodes that are targets of
        `.select()` method.

        C signature of callback must be:

        ```c
        int name(llparse_t* state, char* p, char* endp, int value)
        ```

        Where `llparse_t` is parser state's type name.

        :param name: External function name.

        """
        return code.Value(name)

    def span(self, name: str) -> code._Span:
        """Create an external span callback.

        This callback can be used only in `Span` constructor.

        The difference is that in typescript it's an Arbitrary Span
        in python it's called SpanCallback to try not to be as confusing...

        C signature of callback must be:

        ```c
        int name(llparse_t* state, char* p, char* endp)
        ```

        NOTE: non-zero return value is treated as resumable error.

        :param name: External function name.
        """
        return code._Span(name)

    def store(self, field: str) -> code.Store:
        """
        Intrinsic operation. Stores `value` from `.select()` node into the state's
        property with the name specified by `field`, returns zero.

        ```c
        state[field] = value;
        return 0;
        ```

        :param field:  Property name
        """
        return code.Store(field)

    def load(self, field: str) -> code.Load:
        """Intrinsic operation. Loads and returns state's property with the name
        specified by `field`.

        The value of the property is either truncated or zero-extended to fit into
        32-bit unsigned integer.
        ```c
           return state[field];
        ```

        :param field: Property name.
        """
        return code.Load(field)

    def mulAdd(
        self, field: str, base: int, max: Optional[int] = None, signed: bool = False
    ) -> code.MulAdd:
        """Intrinsic operation. Takes `value` from `.select()`, state's property
        with the name `field` and does:
        ```c
            field = state[field];
            field *= options.base;
            field += value;
            state[field] = field;
            return 0;  // or 1 on overflow
        ```
        Return values are:

            - 0 - success
            - 1 - overflow

        Unlike in Typescript, The values of `IMulAddOptions` have been added here
        since it's Python , not Typescript

        :param field:    Property name

        :param base: Value to multiply the property with in the first step

        :param max: Maximum value of the property. If at any point of computation the
           intermediate result exceeds it - `mulAdd` returns 1 (overflow).

        :param signed: If `true` - all arithmetics perfomed by `mulAdd` will be signed.
           Default value: `false`"""
        return code.MulAdd(field, base, max, signed)

    def update(self, field: str, value: int) -> code.Update:
        """

        Intrinsic operation. Puts `value` integer into the state's property with
        the name specified by `field`.

          state[field] = value;
          return 0;

        :param field: Property name
        :param value: Integer value to be stored into the property.
        """
        return code.Update(field, value)

    def isEqual(self, field: str, value: str) -> code.IsEqual:
        """Intrinsic operation.

        ```c
        state[field] &= value
        return 0;
        ```

        :param field: Property name
        :param value: Integer value
        """
        return code.IsEqual(field, value)

    # NOTE : Unlike in typescript lowercase "and" & "or"
    # cannot be used this might have to be
    # throughly addressed - Vizonex
    def And(self, field: str, value: int) -> code.And:
        """Intrinsic operation.

        ```c
        state[field] &= value
        return 0;
        ```

        :param field: Property name
        :param value: Integer value
        """

        return code.And(field, value)

    def Or(self, field: str, value: int) -> code.Or:
        """
        Intrinsic operation.

           state[field] |= value
           return 0;

        :param field: Property name
        :param value: Integer value

        This will allow us to set our own flags at will
        """
        return code.Or(field, value)

    def test(self, field: str, value: int) -> code.Test:
        """Intrinsic operation.

        ```c
        return (state[field] & value) == value ? 1 : 0;
        ```

        :param field: Property name
        :param value: Integer value
        """
        return code.Test(field, value)

    def is_gt(self, field: str, value: int) -> code.Operator:
        """Intrinsic operation.

        ```c
        return (state[field] > value);
        ```

        :param field: Property name
        :param value: Integer value
        """

        return code.Operator(">", field, value)

    def is_lt(self, field: str, value: int) -> code.Operator:
        """Intrinsic operation.

        ```c
        return (state[field] < value);
        ```

        :param field: Property name
        :param value: Integer value
        """

        return code.Operator("<", field, value)

    def is_le(self, field: str, value: int) -> code.Operator:
        """Intrinsic operation.

        ```c
        return (state[field] <= value);
        ```

        :param field: Property name
        :param value: Integer value
        """

        return code.Operator("<=", field, value)

    def is_ge(self, field: str, value: int) -> code.Operator:
        """Intrinsic operation.

        ```c
        return (state[field] >= value);
        ```

        :param field: Property name
        :param value: Integer value
        """

        return code.Operator(">=", field, value)


# NOTE: I have Nodes and Codes in the same file called `main_code`
# as a tiny convienience for the sake a protability of not wanting
# to Cause Hell for those wishing to move files to other folder
# quickly this was done during development
# as a caution of not needing to
# open too many ides and numerous windows - Vizonex
# so node.Match in typescript is code.Match in python...


# TODO (Vizonex) Add more Documentation later , I got tired of it...
class Builder:
    def __init__(self) -> None:
        self.code = Creator()
        " API for creating external callbacks and intrinsic operations."
        self.transform = code.TransfromCreator()
        self.privProperties: dict[str, Property] = {}

    def node(self, name: str):
        return code.Match(name)

    def error(self, errorCode: int, reason: str):
        return code.Error(errorCode, reason)

    def invoke(
        self,
        fn: code.Code,
        Map: Union[dict[int, code.Node], code.Node, None] = None,
        otherwise: Optional[code.Node] = None,
    ):
        if not Map:
            res = code.Invoke(fn, {})

        elif isinstance(Map, code.Node):
            res = code.Invoke(fn, {})
            otherwise = Map

        else:
            res = code.Invoke(fn, Map)

        if otherwise:
            res.otherwise(otherwise)

        return res

    def consume(self, field: str):
        return code.Comsume(field)

    def pause(self, errorCode: int, reason: str):
        return code.Pause(errorCode, reason)

    # NOTE SpanCallback Can Really be any node, just needed to Calrify that - Vizonex
    def span(self, callback: code._Span):
        return code.Span(callback)

    def property(self, ty: Literal["i8", "i16", "i32", "i64", "ptr"], name: str):
        if ty not in PropertyTypes:
            raise TypeError(f"ty:{ty} is not an existing Parser Property")

        if self.privProperties.get(name):
            raise RuntimeError(f"Duplicate property with name:{name}")

        self.privProperties[name] = Property(ty, name)

    def properties(self) -> list[Property]:
        """Return list of all allocated properties in parser's state."""
        return list(self.privProperties.values())

    def intBE(self, field: str, bits: int):
        """
        :param field: State's property name
        :param bits: Number of bits to use
        """
        return code.Int(field, bits, True, False)

    def intLE(self, field: str, bits: int):
        """
        return a node for unpacking arrays to integers

        :param field: State's property name
        :param bits: Number of bits to use
        """
        return code.Int(field, bits, True, True)

    def uintBE(self, field: str, bits: int):
        """
        return a node for unpacking arrays to integers

        :param field: State's property name
        :param bits: Number of bits to use
        """
        return code.Int(field, bits, False, False)

    def uintLE(self, field: str, bits: int):
        """
        return a node for unpacking arrays to integers

        :param field: State's property name
        :param bits: Number of bits to use
        """
        return code.Int(field, bits, False, True)
