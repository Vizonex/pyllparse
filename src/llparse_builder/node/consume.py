from ..errors import Error
from .base import Node


class Consume(Node):
    def __init__(self, name: str):
        super().__init__(f"consume_{name}")
        if name.startswith("_"):
            raise Error("Cannot use internal field in consume")
