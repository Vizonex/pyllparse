from dataclasses import dataclass, field

from llparse_builder.builder import Property
from llparse_frontend.span_field import SpanField

from ..error import Error

TYPE_LOOKUP = {
    "i8": "uint8_t",
    "i16": "uint16_t",
    "i32": "uint32_t",
    "i64": "uint64_t",
    "ptr": "void*",
}


@dataclass(slots=True)
class HeaderBuilder:
    prefix: str
    header_guard: str | None = field(default=None)
    properties: list[Property] = field(default_factory=list)
    spans: list[SpanField] = field(default_factory=list)

    def build(self) -> str:
        """Builds The string to create the header file"""
        res = ""
        PREFIX = self.prefix.upper()
        DEFINE = f"INCLUDE_{PREFIX}_H_" if not self.header_guard else self.header_guard

        res += f"#ifndef {DEFINE}\n"
        res += f"#define {DEFINE}\n"
        res += "#ifdef __cplusplus\n"
        res += 'extern "C" {\n'
        res += "#endif\n"
        res += "\n"

        res += "#include <stdint.h>\n"
        res += "\n"

        # Main Structure
        res += f"typedef struct {self.prefix}_s {self.prefix}_t;\n"
        res += f"struct {self.prefix}_s " + "{\n"
        res += "  int32_t _index;\n"

        for index, f in enumerate(self.spans):
            res += f"  void* _span_pos{index};\n"
            if len(f.callbacks) > 1:
                res += f"  void* _span_cb{index};\n"

        # TODO: Reorganize fields for better heap/memory and performance.
        res += "  int32_t error;\n"
        res += "  const char* reason;\n"
        res += "  const char* error_pos;\n"
        res += "  void* data;\n"
        res += "  void* _current;\n"

        for prop in self.properties:
            if not (ty := TYPE_LOOKUP.get(prop.ty)):
                raise Error(f'Unknown state property type: "{prop.ty}"')

            res += f"  {ty}  {prop.name};\n"
        res += "};"

        res += "\n"

        res += f"int {self.prefix}_init({self.prefix}_t* s);\n"
        res += f"int {self.prefix}_execute({self.prefix}_t* s, const char* p, const char* endp);\n"

        res += "\n"

        res += "#ifdef __cplusplus\n"
        res += '} /* extern "C" */\n'
        res += "#endif\n"
        res += f"#endif /* {DEFINE} */"
        return res
