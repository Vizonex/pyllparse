from .base import Code, Signature


class External(Code):
    def __init__(self, signature: Signature, name: str):
        super().__init__(signature, f"external_{name}", name)
