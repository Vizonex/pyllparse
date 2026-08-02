from ..utils import to_cache_key
from .field_value import FieldValue


class IsEqual(FieldValue):
    def __init__(self, name: str, field: str, value: int) -> None:
        super().__init__(
            "match", f"is_equal_{field}_{to_cache_key(value)}", name, field, value
        )
