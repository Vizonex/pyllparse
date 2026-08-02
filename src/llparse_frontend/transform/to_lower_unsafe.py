from .base import Transform


class ToLowerUnsafe(Transform):
    def __init__(self) -> None:
        super().__init__("to_lower_unsafe")
