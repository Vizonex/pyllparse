from llparse_frontend import transform as frontend

from .base import Transform


class ToLowerUnsafe(Transform[frontend.ToLowerUnsafe]):
    def build(self, ctx, value: str) -> str:
        return f"(({value}) | 0x20)"
