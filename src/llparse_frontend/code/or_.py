from ..utils import to_cache_key
from .field_value import FieldValue


class Or(FieldValue):
    def __init__(self, name: str, field: str, value: int):
        super().__init__(
            "match", f"or_{field}_{to_cache_key(value)}", name, field, value
        )
