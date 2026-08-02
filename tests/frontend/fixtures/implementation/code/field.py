from .base import Code, TypeVar

T = TypeVar("T", bound=Code)


class Field(Code[T]):
    pass
