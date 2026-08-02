from dataclasses import dataclass

from .field import Field


@dataclass(slots=True)
class MulAddOptions:
    base: int
    max: int | None = None
    signed: bool | None = None


class MulAdd(Field):
    __slots__ = ("name", "options", "signature")

    def __init__(
        self, field: str, base: int, max: int | None = None, signed: int | None = None
    ):
        super().__init__("value", "mul_add", field)
        self.options = MulAddOptions(base, max, signed)
