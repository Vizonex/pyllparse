from ..errors import Error
from .identifier import Identifier, UniqueName


def to_cache_key(value: int | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, int):
        return f"m{-value}" if value < 0 else f"{value}"
    else:
        raise Error(f'Unsupported value: "{value}"')


__all__ = ("Identifier", "UniqueName")
