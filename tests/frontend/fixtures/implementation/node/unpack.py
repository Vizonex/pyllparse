from llparse_frontend import node as frontend

from .base import Node

# Unused but defined incase needed in a later update for testing.


class Unpack(Node[frontend.Unpack]):
    def do_build(self, out: list[str]) -> None:
        out.append(
            self.format(
                f'bits="{self.ref.bits}" name="{self.ref.id.name}" signed={self.ref.signed}'
            )
        )
