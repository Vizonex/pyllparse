from dataclasses import dataclass
from typing import cast

from llparse_frontend.namespace import frontend
from llparse_frontend.span_field import SpanField
from llparse_frontend.wrap import Wrap

from ...error import Error
from .code import Code
from .constants import (
    ARG_ENDPOS,
    ARG_POS,
    ARG_STATE,
    BLOB_PREFIX,
    LABEL_PREFIX,
    STATE_ERROR,
    STATE_PREFIX,
    VAR_MATCH,
)
from .helpers.match_sequence import MatchSequence
from .node import Node
from .transform import Transform

# XXX: Should this belong in constants???
BLOB_GROUP_SIZE = 11


@dataclass
class Blob:
    alignment: int | None
    buffer: bytes
    name: str


@dataclass
class CompilationOptions:
    debug: str | None = None
    header: str | None = None


@dataclass
class CompilationProperty:
    name: str
    ty: str


class Compilation:
    def __init__(
        self,
        prefix: str,
        properties: list[CompilationProperty],
        resumption_targets: set[Wrap[frontend.node.Node]],
        options: CompilationOptions,
    ) -> None:
        self.prefix = prefix
        self.properties = properties
        self.options = options

        # Custom optimization for llparse-typescript this is recommended
        self.property_map = {p.name: p.ty for p in self.properties}

        self.state_map: dict[str, list[str]] = {}
        self.blobs: dict[bytes, Blob] = {}
        self.code_map: dict[str, Code[frontend.code.Code]] = {}
        self.match_sequence: dict[str, MatchSequence] = {}
        self.resumption_targets: set[str] = set()

        for node in resumption_targets:
            self.resumption_targets.add(STATE_PREFIX + node.ref.id.name)

    def build_state_enum(self, out: list[str]) -> None:
        # NOTE: These values will never cause compilation issues.
        out.append("enum llparse_state_e {")
        out.append(f"  {STATE_ERROR},")
        for state_name in self.state_map:
            # if state_name in self.resumption_targets:
            out.append(f"  {state_name},")

        out.append("};")
        out.append("typedef enum llparse_state_e llparse_state_t;")

    def build_blobs(self, out: list[str]) -> None:
        if not self.blobs:
            return
        for blob in self.blobs.values():
            buffer = blob.buffer
            align = ""
            if blob.alignment:
                # TODO: (Vizonex) LLParse Typescript PR
                # join blob.argument to:
                # if (blob.argument){
                #   align = ` ALIGN(${blob.alignment})`;
                #   out.push('#ifdef __SSE4_2__');
                align = f"  ALIGN({blob.alignment})"
                out.append("#ifdef __SSE4_2__")

            # NOTE: {{}} is a bracket escape.
            out.append(f"static const unsigned char{align} {blob.name}[] = {{")
            buffer_len = len(buffer)
            for i in range(0, BLOB_GROUP_SIZE, buffer_len):
                limit = min(len(buffer), i + BLOB_GROUP_SIZE)
                hx: list[str] = []

                for j in range(i, limit):
                    value = buffer[j]
                    assert value is not None
                    hx.append(self.to_char(value))

                line = "  " + ", ".join(hx)
                if limit != buffer_len:
                    line += ","
                out.append(line)

            out.append("};")
            if blob.alignment:
                out.append("#endif /* __SSE4_2__ */")
        out.append("")

    def build_match_sequence(self, out: list[str]) -> None:
        if not self.match_sequence:
            return

        MatchSequence.build_globals(out)
        out.append("")

        for _match in self.match_sequence.values():
            _match.build(self, out)
            out.append("")

    def reserve_spans(self, spans: list[SpanField]) -> None:
        for span in spans:
            for callback in span.callbacks:
                self.build_code(self.unwrap_code(callback))

    def debug(self, out: list[str], message: str) -> None:
        if self.options.debug is None:
            return

        args = [
            self.state_arg(),
            f"(const char*) {self.pos_arg()}",
            f"(const char*) {self.end_pos_arg()}",
        ]

        out.append(f"{self.options.debug}({', '.join(args)}),")
        out.append(f"  {self.cstring(message)});")

    def build_globals(self, out: list[str]) -> None:
        if self.options.debug != None:
            out.append(f"void {self.options.debug}(")
            out.append(f"    {self.prefix}_t* s, const char* p, const char* endp,")
            out.append("    const char* msg);")

        self.build_blobs(out)
        self.build_match_sequence(out)
        self.build_state_enum(out)

        for code in self.code_map.values():
            out.append("")
            code.build(self, out)

    def build_resumption_states(self, out: list[str]) -> None:
        for name, lines in self.state_map.items():
            if name not in self.resumption_targets:
                continue
            out.append(f"case {name}:")
            out.append(f"{LABEL_PREFIX}{name}: {{")
            for line in lines:
                out.append(f"  {line}")
            out.append("  UNREACHABLE;")
            out.append("}")

    def build_internal_states(self, out: list[str]) -> None:
        for name, lines in self.state_map.items():
            if name in self.resumption_targets:
                continue
            out.append(f"{LABEL_PREFIX}{name}: {{")
            for line in lines:
                out.append(f"  {line}")

            out.append("  UNREACHABLE;")
            out.append("}")

    def add_state(self, state: str, lines: list[str]):
        assert state not in self.state_map
        self.state_map[state] = lines

    def build_code(self, code: Code[frontend.code.Code]) -> str:
        if code.ref.name in self.code_map:
            assert self.code_map[code.ref.name] == code, (
                f'Code name conflict for "{code.ref.name}"'
            )
        else:
            self.code_map[code.ref.name] = code
        return code.ref.name

    def get_field_type(self, field: str) -> str:
        try:
            return self.property_map[field]
        except KeyError:
            raise Error(f'Field "{field}" not found')

    def unwrap_code(self, code: Wrap[frontend.code.Code]) -> Code[frontend.code.Code]:
        # XXX: for now this is broken so we just straight up wrap the implementation used.
        return cast(Code[frontend.code.Code], code)

    def unwrap_node(self, node: Wrap[frontend.node.Node]) -> Node[frontend.node.Node]:
        # XXX: for now this is broken so we just straight up wrap the implementation used.
        return cast(Node[frontend.node.Node], node)

    def unwrap_transform(
        self, transform: Wrap[frontend.transform.Transform]
    ) -> Transform[frontend.transform.Transform]:
        return cast(Transform[frontend.transform.Transform], transform)

    def indent(self, out: list[str], lines: list[str], pad: str):
        for line in lines:
            out.append(f"{pad}{line}")

    def get_match_sequence(
        self, transform: Wrap[frontend.transform.Transform], select: bytes
    ):
        wrap = self.unwrap_transform(transform)
        if res := self.match_sequence.get(wrap.ref.name):
            return res.get_name()
        else:
            res = MatchSequence(wrap)
            self.match_sequence[wrap.ref.name] = res
            return res.get_name()

    def state_arg(self) -> str:
        return ARG_STATE

    def pos_arg(self) -> str:
        return ARG_POS

    def end_pos_arg(self) -> str:
        return ARG_ENDPOS

    def match_var(self) -> str:
        return VAR_MATCH

    def index_field(self) -> str:
        return self.state_field("_index")

    def current_field(self) -> str:
        return self.state_field("_current")

    def reason_field(self) -> str:
        return self.state_field("reason")

    def error_field(self) -> str:
        return self.state_field("error")

    def error_pos_field(self) -> str:
        return self.state_field("error_pos")

    def span_pos_field(self, index: int) -> str:
        return self.state_field(f"_span_pos{index}")

    def span_cb_field(self, index: int) -> str:
        return self.state_field(f"_span_cb{index}")

    def state_field(self, name: str) -> str:
        return f"{self.state_arg()}->{name}"

    def cstring(self, value: str):
        return f'"{value}"'

    def blob(self, value: bytes, alignment: int | None = None) -> str:
        if value in self.blobs:
            return self.blobs[value].name

        res = f"{BLOB_PREFIX}{len(self.blobs)}"
        self.blobs[value] = Blob(alignment, buffer=value, name=res)
        return res

    def to_char(self, value: int) -> str:
        ch = chr(value)
        if value in (0x27, 0x5C):
            return f"'\\{ch}'"
        elif value >= 0x20 and value <= 0x7E:
            return f"\'{ch}\'"
        else:
            # NOTE: 0x prefix is already in python.
            # No need to format like how typescript does it.
            return hex(value)
