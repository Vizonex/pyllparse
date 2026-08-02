from .field_value import Field


class Store(Field):
    def __init__(self, name: str, field: str):
        super().__init__("value", f"store_{field}", name, field)
