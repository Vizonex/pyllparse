from .base import Transform


class ToLowerUnsafe(Transform):
    __slots__ = ("name",)

    def __init__(self) -> None:
        super().__init__("to_lower_unsafe")
