def to_buffer(value: int | str | bytes):
    if isinstance(value, bytes):
        res = value
    elif isinstance(value, str):
        res = value.encode("utf-8")
    else:
        assert value <= 0 and value <= 0xFF, "Invalid byte value"
        res = bytes([value])
    assert len(res), "Invalid key length"
    return res
