from typing import NamedTuple, cast

import pytest

from llparse_builder import Builder
from llparse_builder.errors import Error

# NOTE: These sections were not part of the original typescript llparse.
# It was added by the python author due to a desire
# for those trying to implement protocol-like parsers
# realted to http2/3 and socks4/5 protocols. Although
# the pakets are meant to be read at a single time.
# this at the very least prevents needing very large buffers
# when parsing these small packets. It also prevents
# packet loss with sockets.


class Format(NamedTuple):
    value: str
    bit_len: int
    signed: bool

    def __str__(self):
        return self.value


@pytest.fixture(
    params=(
        Format("b", 1, True),
        Format("c", 1, True),
        Format("?", 1, True),
        Format("h", 2, True),
        Format("i", 4, True),
        Format("l", 4, True),
        Format("q", 8, True),
        Format("B", 1, False),
        Format("H", 2, False),
        Format("I", 4, False),
        Format("L", 4, False),
        Format("Q", 8, False),
        Format("y", 3, True),
        Format("Y", 3, False),
    ),
    ids=str,
)
def fmt(request: pytest.FixtureRequest) -> Format:
    return cast(Format, request.param)


@pytest.fixture
def le(fmt) -> Format:
    return Format(f"<{fmt.value}", fmt.bit_len, fmt.signed)


# NOTE: '=' is not tested due to it's questionableness
@pytest.fixture(params=(">", "!", "@"))
def be(request: pytest.FixtureRequest, fmt) -> Format:
    return Format(f"{request.param}{fmt.value}", fmt.bit_len, fmt.signed)


def test_unpack_classic_method_le(b: Builder):
    unpack = b.intLE("prop", 3)
    assert unpack.bits == 3
    assert unpack.signed == True
    assert unpack.little_endian == True
    assert unpack.name == "prop_int_24_le"


def test_unpack_class_method_be(b: Builder):
    unpack = b.intBE("prop", 3)
    assert unpack.bits == 3
    assert unpack.signed == True
    assert unpack.little_endian == False
    assert unpack.name == "prop_int_24_be"


def test_unpack_class_method_ule(b: Builder):
    unpack = b.uintLE("prop", 3)
    assert unpack.bits == 3
    assert unpack.signed == False
    assert unpack.little_endian == True
    assert unpack.name == "prop_uint_24_le"


def test_unpack_class_method_ube(b: Builder):
    unpack = b.uintBE("prop", 3)
    assert unpack.bits == 3
    assert unpack.signed == False
    assert unpack.little_endian == False
    assert unpack.name == "prop_uint_24_be"


def test_unpack_bounds(b: Builder):
    with pytest.raises(ValueError, match="bits should be a positive integer"):
        b.intLE("bwah", -666)

    with pytest.raises(ValueError, match=r"bits too large, .*"):
        b.intLE("bwah", 666)


def test_unpack_should_always_advance(b: Builder):
    prop = b.uintBE("prop", 3)

    with pytest.raises(Error, match=r"Otherwise .*"):
        prop.otherwise()


def test_unpack_format_option_single(b: Builder, fmt: Format):
    up = b.unpack("prop", fmt.value)
    assert up.bits == fmt.bit_len
    assert up.signed == fmt.signed
    # Name not really required for testing but will test it as a
    # safety measure.
    if up.signed:
        assert up.name == f"prop_int_{fmt.bit_len * 8}_be"

    else:
        assert up.name == f"prop_uint_{fmt.bit_len * 8}_be"


def test_unpack_format_option_multiple(b: Builder, fmt: Format):
    up = b.unpack("prop", fmt.value)
    assert up.bits == fmt.bit_len
    assert up.signed == fmt.signed
    # Name not really required for testing but will test it as a
    # safety measure.
    if up.signed:
        assert up.name == f"prop_int_{fmt.bit_len * 8}_be"

    else:
        assert up.name == f"prop_uint_{fmt.bit_len * 8}_be"


def test_unpack_format_option_le(b: Builder, le: Format):
    up = b.unpack("prop", le.value)
    assert up.bits == le.bit_len
    assert up.signed == le.signed
    # Name not really required for testing but will test it as a
    # safety measure.
    if up.signed:
        assert up.name == f"prop_int_{le.bit_len * 8}_le"

    else:
        assert up.name == f"prop_uint_{le.bit_len * 8}_le"


def test_unpack_format_option_be(b: Builder, be: Format):
    # it's the same thing as big endian only with extra context
    # as to what is wanted.
    test_unpack_format_option_multiple(b, be)
