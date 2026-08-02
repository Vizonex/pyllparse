"""
unpack
------

while unpack is not implemented as of yet in typescript llparse
the desire for enabling socket protocols has always been a desire
to extend llparse's usefulness in real world scenarios.

It is an extension based on some older work that has been
previously proposed to Indutny by Arthurschreiber.

This change uses python's struct protocols
to determine how the nodes should unpack into a
given property. Know however that it can only take a
single value at a time.

"""

import sys
import warnings
from enum import IntEnum
from io import StringIO

from ..errors import Error
from .base import Node


class ByteOrder(IntEnum):
    LITTLE = 0
    BIG = 1


# based off CPython _struct.c's whichtable function
def whichtable(pfmt: StringIO) -> ByteOrder:
    """Determines what kind of byte format llparse should be using
    defaults to big-endian if this can't be determined.
    """
    fmt = pfmt.read(1)
    match fmt:
        case "<":
            return ByteOrder.LITTLE
        case ">":
            return ByteOrder.BIG
        case "!":  # network byte-order is always big-endian
            return ByteOrder.BIG
        case "@":
            # Just call it big
            return ByteOrder.BIG
        case "=":
            warnings.warn(
                "llparse will be compiling based off "
                "your cpu's endianness "
                "output may result different parsers "
                "for different users and developers,"
                "this may not be what you want."
            )
            return ByteOrder.LITTLE if sys.byteorder == "little" else ByteOrder.BIG
        case _:
            # assume the format is already given to us, big is all we need.
            pfmt.seek(0)
            return ByteOrder.BIG


# SEE: https://docs.python.org/3/library/struct.html#format-characters
# TODO: A new value to map 24 bit integers would be a good idea for
# http2 parsers.
TABLE_SIZE = {
    "b": (1, True),
    "c": (1, True),
    "?": (1, True),
    "h": (2, True),
    "i": (4, True),
    "l": (4, True),
    "q": (8, True),
    "B": (1, False),
    "H": (2, False),
    "I": (4, False),
    "L": (4, False),
    "Q": (8, False),
    # Entirely Custom. They are named after the word H'y'brid
    "y": (3, True),
    "Y": (3, False),
    # Throw an issue on Github if you need any values between 5 to 8
}


def whichsize(pfmt: StringIO) -> tuple[int, bool]:
    """Determines the length of the byte wanted for parsing with.
    It uses python's array.array/struct module number format to
    determine the size of the value being unpacked. Know that floats
    and doubles are not implemented as llparse has not histrocially
    supported it yet.

    - value, type in rust notation, bit length
    - 'b' i8, 1
    - 'c' i8, 1
    - '?' bool, 1
    - 'h' i16, 2
    - 'i' i32, 4
    - 'l' i32, 4
    - 'q' i64, 8
    - 'B' u8, 1
    - 'H' u16, 2
    - 'I' u32, 4
    - 'L' u32, 4
    - 'Q' u64, 8

    These ones are custom and not apart of CPython at all.
    They are added incase only 3 bits are needed. They
    are used to describe a hybrid (H was already taken by short so will use a y)
    - 'y', i24, 3
    - 'Y', u24, 3

    Example of hybrid's usage could be making a parser for the
    socks5 protocol or http2/3.

    """
    value = pfmt.read(1)

    try:
        return TABLE_SIZE[value]
    except KeyError:
        raise Error(f"{value!r} not implemented or is invalid.")


def define_name(field: str, bits: int, signed: bool, little_endian: bool) -> str:
    result = f"{field}_{'int' if signed else 'uint'}_{bits * 8}"
    return result + ("_le" if little_endian else "_be")


class Unpack(Node):
    __slots__ = ("bits", "field", "little_endian", "signed")

    def __init__(self, field: str, bits: int, signed: bool, little_endian: bool):
        if bits <= 0:
            raise ValueError("bits should be a positive integer")
        if bits > 64:
            raise ValueError(f"bits too large, field {field!r} could overflow")
        self.field = field
        self.bits = bits
        self.signed = signed
        self.little_endian = little_endian
        super().__init__(define_name(field, bits, signed, little_endian))

    @classmethod
    def from_format(cls, field: str, fmt: str):
        """Defines the format of an Unpack Node and which direction
        to unpack the provided bytes in."""
        fmt_len = len(fmt)
        assert fmt_len in (1, 2), "format must be greater than zero or less than 3"
        pfmt = StringIO(fmt)
        is_le = whichtable(pfmt) == ByteOrder.LITTLE
        size, signed = whichsize(pfmt)
        return cls(field, size, signed, is_le)

    def otherwise(self):
        """
        WARNING!
        --------

        Otherwise is not implemented as
        bytes must advance after unpacking
        values."""
        raise Error(
            "Otherwise is not implemented as "
            "skip_to(...) on an unpack variable is required"
        )
