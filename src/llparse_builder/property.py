from dataclasses import dataclass
from typing import Literal, TypeAlias

from .errors import Error

PropertyTypes = {"i8", "i16", "i32", "i64", "ptr"}

PropertyType: TypeAlias = Literal["i8", "i16", "i32", "i64", "ptr"]


@dataclass(slots=True)
class Property:
    ty: Literal["i8", "i16", "i32", "i64", "ptr"]
    name: str

    def __post_init__(self):
        assert self.ty in PropertyTypes
        if self.name.startswith("_"):
            raise Error(f"Can't use internal property name: {self.name!r}")
