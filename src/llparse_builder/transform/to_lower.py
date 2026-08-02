from .base import Transform


class ToLower(Transform):
    __slots__ = ("name",)

    def __init__(self) -> None:
        super().__init__("to_lower")
