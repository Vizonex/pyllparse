from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from llparse_frontend.namespace import frontend
from llparse_frontend.wrap import Wrap

from .. import compilation as comp  # Don't let python freak out
from ..constants import LABEL_PREFIX, STATE_PREFIX

T = TypeVar("T")


@dataclass
class NodeEdge:
    node: Wrap[frontend.node.Node]
    no_advance: bool
    value: int | None = None


class Node(ABC, Generic[T]):
    __slots__ = ("cached_decl", "priv_compilation", "ref")

    def __init__(self, ref: T) -> None:
        self.ref = ref
        self.cached_decl = None
        self.priv_compilation: comp.Compilation | None = None

    def build(self, compilation: "comp.Compilation") -> str:
        if self.cached_decl is not None:
            return self.cached_decl

        res = STATE_PREFIX + self.ref.id.name
        self.cached_decl = res
        out = []

        compilation.debug(
            out, f'Entering node "{self.ref.id.original_name}" ("{self.ref.id.name}")'
        )
        self.priv_compilation = compilation
        self.do_build(out)
        compilation.add_state(res, out)

        return res

    @property
    def compilation(self):
        assert self.priv_compilation
        return self.priv_compilation

    def prologue(self, out: list[str]):
        ctx = self.compilation

        out.append(f"if ({ctx.pos_arg()} == {ctx.end_pos_arg()}) {{")
        tmp: list[str] = []
        self.pause(tmp)
        self.compilation.indent(out, tmp, "  ")

        out.append("}")

    def pause(self, out: list[str]) -> None:
        out.append(f"return {self.cached_decl};")

    def tail_to(self, out: list[str], edge: NodeEdge) -> None:
        ctx = self.compilation
        target = ctx.unwrap_node(edge.node).build(ctx)

        if edge.no_advance:
            out.append(f"{ctx.pos_arg()}++;")

        if edge.value is not None:
            out.append(f"{ctx.match_var()} = {edge.value};")

        out.append(f"goto {LABEL_PREFIX}{target};")

    @abstractmethod
    def do_build(self, out: list[str]) -> None: ...
