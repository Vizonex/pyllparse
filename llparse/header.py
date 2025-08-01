"""
The Second to Final Part I translated to python
translated from typescript

This module helps with building Header Files or `.h` files
In C these can help with defining important definiations

"""

from typing import Optional

from .frontend import SpanField
from .pybuilder import Property


class HeaderBuilder:
    def __init__(
        self,
        prefix: str,
        headerGuard: Optional[str] = None,
        Properties: list[Property] = [],
        spans: list[SpanField] = [],
    ) -> None:
        self.Properties = Properties
        self.prefix = prefix
        self.headerGuard = headerGuard
        self.spans = spans

    def build(self):
        """Builds The string to create the header file"""
        res = ""
        PREFIX = self.prefix.upper()
        DEFINE = f"INCLUDE_{PREFIX}_H_" if not self.headerGuard else self.headerGuard

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

        for index, field in enumerate(self.spans):
            res += f"  void* _span_pos{index};\n"
            if len(field.callbacks) > 1:
                res += f"  void* _span_cb{index};\n"

        res += "  int32_t error;\n"
        res += "  const char* reason;\n"
        res += "  const char* error_pos;\n"
        res += "  void* data;\n"
        res += "  void* _current;\n"

        for prop in self.Properties:
            if prop.ty == "i8":
                ty = "uint8_t"
            elif prop.ty == "i16":
                ty = "uint16_t"
            elif prop.ty == "i32":
                ty = "uint32_t"
            elif prop.ty == "i64":
                ty = "uint64_t"
            elif prop.ty == "ptr":
                ty = "void*"
            else:
                raise Exception(f'Unknown state property type: "{prop.ty}"')

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
