from .to_lower import ToLower
from .to_lower_unsafe import ToLowerUnsafe


class Creator:
    __slots__ = ()

    def to_lower_unsafe(self):
        return ToLowerUnsafe()

    def to_lower(self):
        return ToLower()
