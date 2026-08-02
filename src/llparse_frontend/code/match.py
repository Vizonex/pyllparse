from .external import External


class Match(External):
    def __init__(self, name: str):
        super().__init__("match", name)
