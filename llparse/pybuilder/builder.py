from typing import Literal, Optional, Union

from ..pybuilder import main_code as code

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

    # TODO Make Sure python llparse match api is compatable with 3.10 and above...

    # Thank goodness I can do C example documentation in here :) - Vizonex
    def match(self, name: str):
        """Create an external callback that **has no** `value` argument.

        This callback can be used in all `Invoke` nodes except those that are
        targets of `.select()` method.

        C signature of callback must be:

        ```c
        int name(llparse_t* state,  char* p,     char* endp)
        ```

        Where `llparse_t` is parser state's type name.

        Parameters
        ----------
        ----------
        - `name` External function name.
        """
        return code._Match(name)

    def value(self, name: str):
        """

        Create an external callback that **has** `value` argument.

        This callback can be used only in `Invoke` nodes that are targets of
        `.select()` method.

        C signature of callback must be:

        ```c
        int name(llparse_t* state, char* p, char* endp, int value)
        ```

        Where `llparse_t` is parser state's type name.

        Parameters
        ----------
        ----------
        - `name` External function name.

        """
        return code.Value(name)

    def span(self, name: str):
        """Create an external span callback.

        This callback can be used only in `Span` constructor.

        The difference is that in typescript it's an Arbitrary Span
        in python it's called SpanCallback to try not to be as confusing...

        C signature of callback must be:

        ```c
        int name(llparse_t* state, char* p, char* endp)
        ```

        NOTE: non-zero return value is treated as resumable error.

        Parameters
        ----------
        - `name` External function name.
        """
        return code._Span(name)

    def store(self, field: str):
        """
        Intrinsic operation. Stores `value` from `.select()` node into the state's
        property with the name specified by `field`, returns zero.

        ```c
           state[field] = value;
           return 0;
        ```

        Parameters
        ----------

        - `field`  Property name
        """
        return code.Store(field)

    def load(self, field: str):
        """Intrinsic operation. Loads and returns state's property with the name
        specified by `field`.

        The value of the property is either truncated or zero-extended to fit into
        32-bit unsigned integer.
        ```c
           return state[field];
        ```
        Parameters
        ----------
        `field`  Property name.
        """
        return code.Load(field)

    def mulAdd(
        self, field: str, base: int, max: Optional[int] = None, signed: bool = False
    ):
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

        Parameters
        ----------
        ----------
        Unlike in Typescript, The values of `IMulAddOptions` have been added here
        since it's Python , not Typescript

        - `field`    Property name

        - `base` Value to multiply the property with in the first step

        - `max` Maximum value of the property. If at any point of computation the
           intermediate result exceeds it - `mulAdd` returns 1 (overflow).

        - `signed` If `true` - all arithmetics perfomed by `mulAdd` will be signed.
           Default value: `false`"""
        return code.MulAdd(field, base, max, signed)

    def update(self, field: str, value: int):
        """

        Intrinsic operation. Puts `value` integer into the state's property with
        the name specified by `field`.

          state[field] = value;
          return 0;

        Parameters
        ----------
        ----------
        - `field` Property name
        - `value` Integer value to be stored into the property.
        """
        return code.Update(field, value)

    def isEqual(self, field: str, value: str):
        """Intrinsic operation.

           state[field] &= value
           return 0;

        Parameters
        ----------
        ----------
        - `field` Property name
        - `value` Integer value
        """
        return code.IsEqual(field, value)

    # NOTE : Unlike in typescript lowercase "and" & "or"
    # cannot be used this might have to be
    # throughly addressed - Vizonex
    def And(self, field: str, value: int):
        """Intrinsic operation.

          state[field] &= value
          return 0;

        Parameters
        ----------
        ----------
        - `field` Property name
        - `value` Integer value"""

        return code.And(field, value)

    def Or(self, field: str, value: int):
        """
        Intrinsic operation.

           state[field] |= value
           return 0;

        Parameters
        ----------
        ----------
        - `field` Property name
        - `value` Integer value

        This will allow us to set our own flags at will
        """
        return code.Or(field, value)

    def test(self, field: str, value: str):
        """Intrinsic operation.

        return (state[field] & value) == value ? 1 : 0;

        Parameters
        ----------
        ----------
        - `field` Property name
        - `value` Integer value
        """
        return code.Test(field, value)


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
