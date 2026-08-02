from llparse_frontend import transform as frontend

from .base import Transform


class ToLower(Transform[frontend.ToLower]):
    def build(self) -> str:
        return ""
