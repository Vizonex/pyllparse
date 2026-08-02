from .base import Transform


class ToLower(Transform):
    def __init__(self) -> None:
        super().__init__("to_lower")
