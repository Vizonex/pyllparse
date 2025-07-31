from dataclasses import dataclass


@dataclass
class Transform:
    name: str


class ID(Transform):
    def __init__(self) -> None:
        super().__init__("id")


class ToLowerUnsafe(Transform):
    def __init__(self) -> None:
        super().__init__("to_lower_unsafe")


class ToLower(Transform):
    def __init__(self) -> None:
        super().__init__("to_lower")
