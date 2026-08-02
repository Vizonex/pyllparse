from ._and import And
from ._or import Or
from .is_equal import IsEqual
from .load import Load
from .match import Match
from .mul_add import MulAdd
from .span import Span
from .store import Store
from .test import Test
from .update import Update
from .value import Value


class Creator:
    __slots__ = ()

    def match(self, name: str) -> Match:
        return Match(name)

    def value(self, name: str) -> Value:
        return Value(name)

    def span(self, name: str) -> Span:
        return Span(name)

    def store(self, field: str) -> Store:
        return Store(field)

    def load(self, field: str) -> Load:
        return Load(field)

    def mul_add(
        self, field: str, base: int, max: int | None = None, signed: bool | None = None
    ) -> MulAdd:
        return MulAdd(field, base, max, signed)

    def update(self, field: str, value: int) -> Update:
        return Update(field, value)

    def is_equal(self, field: str, value: int) -> IsEqual:
        return IsEqual(field, value)

    def And(self, field: str, value: int) -> And:
        return And(field, value)

    def Or(self, field: str, value: int) -> Or:
        return Or(field, value)

    # secondary options.
    and_ = And
    or_ = Or

    def test(self, field: str, value: int) -> Test:
        return Test(field, value)
