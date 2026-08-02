from .external import External


class Span(External):
    def __init__(self, name: str) -> None:
        super().__init__("span", name)
