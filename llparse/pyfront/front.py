# NOTE The Difference with typescript llparse is that names already
# taken by python standard library modules
# are renamed to something else.... - Vizonex

from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar, Union

T = TypeVar("T")

Signature = TypeVar("Signature", bytes, str)


@dataclass(unsafe_hash=True)
class IWrap(Generic[T]):
    ref: T

    # def __hash__(self) -> int:
    #     return hash(self.ref)


def toCacheKey(value: Union[int, bool]) -> str:
    if isinstance(value, int):
        return "m" + (-value) if value < 0 else "%i" % value
    elif isinstance(value, bool):
        return "true" if value else "false"
    else:
        raise ValueError(f"Unsupported value: {value}")


@dataclass
class Code:
    signature: Signature
    cacheKey: str
    name: str

    def __hash__(self):
        return hash(self.cacheKey)


class External(Code):
    """Inherits from the `Code` class as a subclass of `Code`"""

    def __init__(self, signature: Signature, name: str):
        super().__init__(signature, "external_" + name, name)


@dataclass
class Field(Code):
    """Inherits from `Code`"""

    field: str

    def __hash__(self):
        return hash(self.cacheKey)


class FieldValueError(Exception):
    """FieldValue `value` must be integer"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class FieldValue(Field):
    def __init__(
        self, signature: Signature, cacheKey: str, name: str, field: str, value: int
    ):
        self.value = value
        if not isinstance(self.value, int):
            raise FieldValueError(
                f'FieldValue "value" must be integer not {type(self.value)}'
            )
        super().__init__(signature, cacheKey, name, field)


class And(FieldValue):
    """a Subclass of `FieldValue`"""

    def __init__(self, name: str, field: str, value: int):
        super().__init__(
            "match", f"and_{field}_{toCacheKey(value)}", name, field, value
        )


class IsEqual(FieldValue):
    def __init__(self, name: str, field: str, value: int):
        super().__init__(
            "match", f"is_equal_{field}_{toCacheKey(value)}", name, field, value
        )


class Load(Field):
    """Subclass of Field"""

    def __init__(self, name: str, field: str):
        super().__init__("match", f"load_{field}", name, field)


class Match(External):
    def __init__(self, name: str):
        super().__init__("match", name)


@dataclass
class IMulAddOptions:
    base: int
    max: Optional[int]
    signed: bool


def toOptionsKey(options: IMulAddOptions) -> str:
    res = f"base_{toCacheKey(options.base)}"
    if options.max:
        res += f"_max_{toCacheKey(options.max)}"
    if options.signed:
        res += f"_signed_{toCacheKey(options.signed)}"
    return res


class MulAdd(Field):
    def __init__(self, name: str, field: str, options: IMulAddOptions):
        self.options = options
        super().__init__(
            "value", f"mul_add_{field}_{toOptionsKey(options)}", name, field
        )


class Or(FieldValue):
    def __init__(self, name: str, field: str, value: int):
        super().__init__("match", f"or_{field}_{toCacheKey(value)}", name, field, value)


class Span(External):
    """A `Span` Class"""

    def __init__(self, name: str):
        self.name = name
        super().__init__("span", name)


@dataclass
class SpanField:
    index: int
    callbacks: list[IWrap[Span]]


class Store(Field):
    def __init__(self, name: str, field: str):
        super().__init__("value", f"store_{field}", name, field)


class Test(FieldValue):
    def __init__(self, name: str, field: str, value: int):
        super().__init__(
            "match", f"test_{field}_{toCacheKey(value)}", name, field, value
        )


class Update(FieldValue):
    def __init__(self, name: str, field: str, value: int):
        super().__init__(
            "match", f"update_{field}_{toCacheKey(value)}", name, field, value
        )


class Value(External):
    def __init__(self, name: str):
        super().__init__("value", name)


@dataclass
class IUniqueName:
    name: str
    originalName: str

    def __hash__(self):
        return hash(self.originalName)


@dataclass
class Identifier:
    prefix: str
    postfix: str = ""
    ns: set[str] = field(default_factory=set, init=False)

    def id(self, name: str) -> IUniqueName:
        target = self.prefix + name + self.postfix
        if target in self.ns:
            i = 0
            for i in range(1, len(self.ns)):
                if (target + "_%i" % i) not in self.ns:
                    break

            target += "_%i" % i

        self.ns.add(target)

        return IUniqueName(name=target, originalName=name)
