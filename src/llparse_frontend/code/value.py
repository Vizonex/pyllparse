from .external import External


class Value(External):
    def __init__(self, name: str) -> None:
        super().__init__("value", name)
