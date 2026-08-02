from llparse_frontend import transform as frontend

from .base import Transform


class ToLower(Transform[frontend.ToLower]):
    def build(self, ctx, value: str) -> str:
        return (
            f"(({value}) >= 'A' && ({value}) <= 'Z' ? ({value} | 0x20) : ({value}))`;"
        )
