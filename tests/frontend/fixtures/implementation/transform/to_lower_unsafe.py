from llparse_frontend import transform as frontend

from .base import Transform


class ToLowerUnsafe(Transform[frontend.ToLowerUnsafe]):
    def build(self) -> str:
        return ""
