from ..utils import UniqueName
from .base import Node


class Unpack(Node):
    __slots__ = (
        "bits",
        "byte_offset",
        "field",
        "little_endian",
        "signed",
    )

    def __init__(
        self,
        id: UniqueName,
        field: str,
        bits: int,
        signed: bool,
        little_endian: bool,
        byte_offset: int,
    ):
        super().__init__(id)

        self.field = field
        self.bits = bits
        self.signed = signed
        self.little_endian = little_endian
        self.byte_offset = byte_offset
