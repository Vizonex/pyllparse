from llparse_frontend.frontend import FrontendResult

from .compilation import Compilation, CompilationOptions
from .constants import *


class CCompiler:
    """The Final HeadPeice where the Main C-Code gets compiled to..."""

    def __init__(self, header: str | None = None, debug: str | None = None) -> None:
        # NOTE Unlike in typescript llparse Containers are not Required since I'm using a different methoad to translate those parts...
        self.options = CompilationOptions(debug, header)

    def compile(self, info: FrontendResult):
        compilation = Compilation(
            info.prefix,
            info.properties,
            list(info.resumption_targets),
            options=self.options,
        )

        out: list[str] = []

        out.append("#include <stdlib.h>")
        out.append("#include <stdint.h>")
        out.append("#include <string.h>")
        out.append("")
        # Seems LLParse was updated from /* UNREACHABLE */ abort(); to a Macro, Intresting...
        out.append("#ifdef __SSE4_2__")
        out.append(" #ifdef _MSC_VER")
        out.append("  #include <nmmintrin.h>")
        out.append(" #else  /* !_MSC_VER */")
        out.append("  #include <x86intrin.h>")
        out.append(" #endif  /* _MSC_VER */")
        out.append("#endif  /* __SSE4_2__ */")
        out.append("")

        out.append("#ifdef __ARM_NEON__")
        out.append(" #include <arm_neon.h>")
        out.append("#endif  /* __ARM_NEON__ */")
        out.append("")

        out.append("#ifdef __wasm__")
        out.append(" #include <wasm_simd128.h>")
        out.append("#endif  /* __wasm__ */")
        out.append("")

        out.append("#ifdef _MSC_VER")
        out.append(" #define ALIGN(n) _declspec(align(n))")
        out.append(" #define UNREACHABLE __assume(0)")
        out.append("#else  /* !_MSC_VER */")
        out.append(" #define ALIGN(n) __attribute__((aligned(n)))")
        out.append(" #define UNREACHABLE __builtin_unreachable()")
        out.append("#endif  /* _MSC_VER */")

        out.append("")
        out.append(
            f'#include "{self.options.header if self.options.header else info.prefix}.h"'
        )
        out.append("")
        out.append(f"typedef int (*{info.prefix}__span_cb)(")
        out.append(f"             {info.prefix}_t*, const char*, const char*);")
        out.append("")

        # Start Queuing span callbacks
        # otherwise we will have nothing
        # but mess which is not what we want - Vizonex
        compilation.reserve_spans(info.spans)

        rootState = compilation.unwrap_node(info.root)
        rootName = rootState.build(compilation)
        # Bring in the rest of the variables...
        compilation.build_globals(out)
        out.append("")

        out.append(f"int {info.prefix}_init({info.prefix}_t* {ARG_STATE}) " + "{")
        out.append(f"  memset({ARG_STATE}, 0, sizeof(*{ARG_STATE}));")
        out.append(f"  {ARG_STATE}->_current = (void*) (intptr_t) {rootName};")
        out.append("  return 0;")
        out.append("}")
        out.append("")

        # TODO (Vizonex) Make llparse_state_t's Name Optional and alterable incase mixed with
        # llhttp or another parser
        out.append(f"static llparse_state_t {info.prefix}__run(")
        out.append(f"    {info.prefix}_t* {ARG_STATE},")
        out.append(f"    const unsigned char* {ARG_POS},")
        out.append(f"    const unsigned char* {ARG_ENDPOS}) " + "{")
        out.append(f"  int {VAR_MATCH};")
        out.append(
            "  switch ((llparse_state_t) (intptr_t) "
            + f"{compilation.current_field()}) "
            + "{"
        )

        # Now build resumption states... These are states what will have a 'case block' next to them...
        # However I'm not refering to the characters those will be handles in thier inner switches,
        # I'm talking about the major states...
        tmp = []
        compilation.build_resumption_states(tmp)
        compilation.indent(out, tmp, "    ")

        # Final Resumption State... Very important!
        out.append("    default:")
        out.append("      UNREACHABLE;")
        out.append("  }")

        tmp = []
        compilation.build_internal_states(tmp)
        compilation.indent(out, tmp, "  ")

        out.append("}")
        out.append("")

        out.append(
            f"int {info.prefix}_execute({info.prefix}_t* {ARG_STATE}, "
            + f"const char* {ARG_POS}, const char* {ARG_ENDPOS}) "
            + "{"
        )
        out.append("  llparse_state_t next;")
        out.append("")

        out.append("  /* check lingering errors */")
        out.append(f"  if ({compilation.error_field()} != 0) " + "{")
        out.append(f"    return {compilation.error_field()};")
        out.append("  }")
        out.append("")

        tmp = []
        self.restart_spans(compilation, info, tmp)
        compilation.indent(out, tmp, "  ")
        args = [
            compilation.state_arg(),
            f"(const unsigned char*) {compilation.pos_arg()}",
            f"(const unsigned char*) {compilation.end_pos_arg()}",
        ]
        out.append(f"  next = {info.prefix}__run({(', ').join(args)});")
        out.append(f"  if (next == {STATE_ERROR}) " + "{")
        out.append(f"    return {compilation.error_field()};")
        out.append("  }")
        out.append(f"  {compilation.current_field()} = (void*) (intptr_t) next;")
        out.append("")

        tmp = []
        self.execute_spans(compilation, info, tmp)
        compilation.indent(out, tmp, "  ")

        out.append("  return 0;")
        out.append("}")

        # JOIN ALL OF THEM!
        return "\n".join(out)

    def restart_spans(self, ctx: Compilation, info: FrontendResult, out: list[str]):
        if not info.spans:
            return

        out.append("/* restart spans */")
        for span in info.spans:
            pos_field = ctx.span_pos_field(span.index)

            out.append(f"if ({pos_field} != NULL) " + "{")
            out.append(f"  {pos_field} = (void*) {ctx.pos_arg()};")
            out.append("}")
        out.append("")

    def execute_spans(self, ctx: Compilation, info: FrontendResult, out: list[str]):
        if not info.spans:
            return

        out.append("/* execute spans */")
        for span in info.spans:
            pos_field = ctx.span_pos_field(span.index)

            if len(span.callbacks) == 1:
                callback = ctx.build_code(ctx.unwrap_code(span.callbacks[0]))

            else:
                callback = (
                    f"(({info.prefix}__span_cb)" + ctx.span_cb_field(span.index) + ")"
                )

            args = [ctx.state_arg(), pos_field, f"(const char*) {ctx.end_pos_arg()}"]

            out.append(f"if ({pos_field} != NULL) " + "{")
            out.append("  int error;")
            out.append("")
            out.append(f"  error = {callback}({', '.join(args)});")

            out.append("  if (error != 0) {")
            out.append(f"    {ctx.error_field()} = error;")
            out.append(f"    {ctx.error_pos_field()} = {ctx.end_pos_arg()};")
            out.append("    return error;")
            out.append("  }")
            out.append("}")
        out.append("")
