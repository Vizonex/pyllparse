from dataclasses import dataclass

from ..utils import to_cache_key
from .field import Field


@dataclass(slots=True, frozen=True)
class MulAddOptions:
    base: int
    max: int | None
    signed: bool


def to_options_key(options: MulAddOptions) -> str:
    res = f"base_{to_cache_key(options.base)}"
    if options.max is not None:
        res += f"_max_{to_cache_key(options.max)}"
    if options.signed is not None:
        res += f"_signed_{to_cache_key(options.signed)}"
    return res


class MulAdd(Field):
    __slots__ = ("options",)

    def __init__(self, name: str, field: str, options: MulAddOptions):
        super().__init__(
            "value", f"mul_add_{field}_{to_options_key(options)}", name, field
        )
        self.options = options
