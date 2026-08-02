from .field import Field


class Load(Field):
    def __init__(self, name: str, field: str) -> None:
        super().__init__("match", f"load_{field}", name, field)
