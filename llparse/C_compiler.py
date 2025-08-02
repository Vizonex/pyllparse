from typing import Optional

from .compilator import Compilation, ICompilerOptions, Node
from .constants import *
from .frontend import IFrontendResult


class CCompiler:
    """The Final HeadPeice where the Main C-Code gets compiled to..."""

    def __init__(
        self, header: Optional[str] = None, debug: Optional[str] = None
    ) -> None:
        # NOTE Unlike in typescript llparse Containers are not Required since I'm using a different methoad to translate those parts...
        self.options = ICompilerOptions(debug, header)

    def compile(self, info: IFrontendResult):
        compilation = Compilation(
            info.prefix,
            info.properties,
            list(info.resumptionTargets),
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
        compilation.reserveSpans(info.spans)

        rootState: Node = compilation.unwrapNode(info.root)
        rootName = rootState.build(compilation)
        # Bring in the rest of the variables...
        compilation.buildGlobals(out)
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
            + f"{compilation.currentField()}) "
            + "{"
        )

        # Now build resumption states... These are states what will have a 'case block' next to them...
        # However I'm not refering to the characters those will be handles in thier inner switches,
        # I'm talking about the major states...
        tmp = []
        compilation.buildResumptionStates(tmp)
        compilation.indent(out, tmp, "    ")

        # Final Resumption State... Very important!
        out.append("    default:")
        out.append("      UNREACHABLE;")
        out.append("  }")

        tmp = []
        compilation.buildInternalStates(tmp)
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
        out.append(f"  if ({compilation.errorField()} != 0) " + "{")
        out.append(f"    return {compilation.errorField()};")
        out.append("  }")
        out.append("")

        tmp = []
        self.restartSpans(compilation, info, tmp)
        compilation.indent(out, tmp, "  ")
        args = [
            compilation.stateArg(),
            f"(const unsigned char*) {compilation.posArg()}",
            f"(const unsigned char*) {compilation.endPosArg()}",
        ]
        out.append(f"  next = {info.prefix}__run({(', ').join(args)});")
        out.append(f"  if (next == {STATE_ERROR}) " + "{")
        out.append(f"    return {compilation.errorField()};")
        out.append("  }")
        out.append(f"  {compilation.currentField()} = (void*) (intptr_t) next;")
        out.append("")

        tmp = []
        self.executeSpans(compilation, info, tmp)
        compilation.indent(out, tmp, "  ")

        out.append("  return 0;")
        out.append("}")

        # JOIN ALL OF THEM!
        return "\n".join(out)

    def restartSpans(self, ctx: Compilation, info: IFrontendResult, out: list[str]):
        if len(info.spans) == 0:
            return

        out.append("/* restart spans */")
        for span in info.spans:
            posField = ctx.spanPosField(span.index)

            out.append(f"if ({posField} != NULL) " + "{")
            out.append(f"  {posField} = (void*) {ctx.posArg()};")
            out.append("}")
        out.append("")

    def executeSpans(self, ctx: Compilation, info: IFrontendResult, out: list[str]):
        if not info.spans:
            return

        out.append("/* execute spans */")
        for span in info.spans:
            posField = ctx.spanPosField(span.index)

            if len(span.callbacks) == 1:
                cb = ctx.unwrapCode(span.callbacks[0], True)
                callback = ctx.buildCode(cb)

            else:
                # TODO (Vizonex) Merge lines 139 & 140 together in a future update
                callback = (
                    f"(({info.prefix}__span_cb)" + ctx.spanCbField(span.index) + f")"
                )

            args = [ctx.stateArg(), posField, f"(const char*) {ctx.endPosArg()}"]

            out.append(f"if ({posField} != NULL) " + "{")
            out.append("  int error;")
            out.append("")
            out.append(f"  error = {callback}({', '.join(args)});")

            # TODO (Vizonex): Deduplicate when indutny updates his side so we can all make our changes accordingly...
            out.append("  if (error != 0) {")
            out.append(f"    {ctx.errorField()} = error;")
            out.append(f"    {ctx.errorPosField()} = {ctx.endPosArg()};")
            out.append("    return error;")
            out.append("  }")
            out.append("}")
        out.append("")
