from typing import Literal


class Transform:
    __slots__ = ("name",)

    def __init__(self, name: Literal["to_lower_unsafe", "to_lower"]):
        self.name = name
