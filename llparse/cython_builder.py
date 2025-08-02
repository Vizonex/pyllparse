"""Used to build apis and more from llparse WARNING: This may or may not be stable yet!!!"""

from contextlib import contextmanager
from typing import Optional

from .frontend import IFrontendResult
from .pyfront.front import Match
from .pyfront.nodes import Invoke

# Inspired by Cython's Writer

# You will notice many simillarities
# because there's was no way to for me to optimize the
# originals further than what was given by Cython itself.
# This will be used to help me write my own custom
# Finite Machine Parts

VA_ARGS_CALLBACK = """#define CALLBACK_MAYBE(PARSER, NAME, ...)                                     \\
  do {                                                                        \\
    %s_settings_t* settings;                                              \\
    settings = (%s_settings_t*) (PARSER)->settings;                       \\
    if (settings == NULL || settings->NAME == NULL) {                         \\
      err = 0;                                                                \\
      break;                                                                  \\
    }                                                                         \\
    err = settings->NAME(__VA_ARGS__);                                        \\
  } while (0)"""


class LineWriter(object):
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.s = ""

    def put(self, s: str):
        self.s += s

    def newline(self):
        self.lines.append(self.s)
        self.s = ""

    def putline(self, s: str):
        self.s += s
        self.newline()


class CodeWriter:
    """Used as a baseplate for writing code..."""

    line_indent: str = "  "

    def __init__(self) -> None:
        self._indentures = 0
        self.lw = LineWriter()

    def __indent(self):
        self._indentures += 1

    def __dedent(self):
        self._indentures -= 1

    @contextmanager
    def indent(self):
        """Used to mirror/mimic programming with indentures and to make everything cleaner and easier to read"""
        self.__indent()
        yield
        self.__dedent()

    def startline(self, s: str):
        self.lw.put((self._indentures * self.line_indent) + s)

    def put(self, s: str):
        self.lw.put(s)

    def putline_with_format(self, s: str, *args):
        """Makes a cleaner format than what would've been used to workaround formmating with curly brackets `{}`"""
        self.lw.putline((self._indentures * self.line_indent) + s % args)

    def putline(self, s: str):
        self.lw.putline((self._indentures * self.line_indent) + s)

    def endline(self, s: str = ""):
        self.lw.putline(s)

    @property
    def lines(self) -> list[str]:
        return self.lw.lines

    @property
    def code(self) -> str:
        return "\n".join(self.lines)


class CythonWriter(CodeWriter):
    """Coming soon..."""

    line_indent = "    "


# TODO Vizonex Maybe see if Indutny would like to use a special codewriter to
# help with building llparse's c code in typescript It would be less prone to
# compile-time errors


class MainCompiler:
    """Used to Create APIS like those seen in llhttp"""

    def __init__(self, info: IFrontendResult) -> None:
        self.data_cb: set[str] = set()
        """Used to identify span related Callbacks"""
        self.cb: set[str] = set()
        """Used to identify match callbacks that are use-handled"""
        self.info = info

    def get_user_callbacks(self):
        for s in self.info.spans:
            self.data_cb.update(cb.ref.name for cb in s.callbacks)
        for s in self.info.resumptionTargets:
            for slot in s.ref.buildSlots():
                if isinstance(slot.node.ref, Invoke) and isinstance(
                    slot.node.ref.code.ref, Match
                ):
                    self.cb.add(slot.node.ref.code.ref.name)
                # Some nodes like to hide themselves inside other nodes so this is my only simple solution which is to do it a second time...
                for _slot in slot.node.ref.getSlots():
                    if isinstance(_slot.node.ref, Invoke) and isinstance(
                        _slot.node.ref.code.ref, Match
                    ):
                        self.cb.add(_slot.node.ref.code.ref.name)


class ApiCompiler(MainCompiler):
    """Builds external api assuming that our prefix is an internal one"""

    def __init__(
        self, new_preifx: str, info: IFrontendResult, header_name: Optional[str] = None
    ) -> None:
        self.new_prefix = new_preifx
        super().__init__(info)
        self.get_user_callbacks()
        self.header_name = header_name

    def build_C(self):
        # I find using codewriters to be more elegant so we will be using that instead - Vizonex
        prefix = self.info.prefix
        writer = CodeWriter()
        writer.putline(
            f'#include <stdlib.h>\n#include <stdio.h>\n#include <string.h>\n#include "{self.header_name or self.new_prefix}.h"'
        )
        writer.endline()
        writer.putline("/* Inspired by llhttp */")
        writer.endline()
        writer.putline_with_format(VA_ARGS_CALLBACK, self.new_prefix, self.new_prefix)
        writer.endline()
        writer.endline()
        writer.putline(f"void {self.new_prefix}_init({self.new_prefix}_t* parser,")
        with writer.indent():
            writer.putline(f"const {self.new_prefix}_settings_t* settings) " + "{")
            writer.putline(f"{prefix}_init(parser);")
            writer.putline("parser->settings = (void*) settings;")
        writer.endline("}")
        writer.putline("/* Callbacks */")

        # This is where everything comes together and makes sense
        for data in sorted(self.data_cb):
            writer.putline(
                f"int {data}({self.new_prefix}_t* s, const char* p, const char* endp) "
                + "{"
            )
            with writer.indent():
                writer.putline("int err;")
                writer.putline(
                    f"CALLBACK_MAYBE(s, {data.removeprefix(prefix).strip('_')}, s, p, endp - p);"
                )
                writer.putline("return err;")
            writer.putline("}")
            writer.endline()
            writer.endline()

        for data in sorted(self.cb):
            writer.putline(
                f"int {data}({self.new_prefix}_t* s, const char* p, const char* endp) "
                + "{"
            )
            with writer.indent():
                writer.putline("int err;")
                writer.putline(
                    f"CALLBACK_MAYBE(s, {data.removeprefix(prefix).strip('_')}, s);"
                )
                writer.putline("return err;")
            writer.putline("}")
            writer.endline()
            writer.endline()

        writer.putline(
            f"int {self.new_prefix}_execute({self.new_prefix}_t* parser, const char* data, size_t len) "
            + "{"
        )
        with writer.indent():
            writer.putline(f"return {prefix}_execute(parser, data, data + len);")
        writer.putline("}")

        # Reset Parser

        writer.putline(
            f"void {self.new_prefix}_settings_init({self.new_prefix}_settings_t* settings)"
            + " {"
        )
        writer.putline("\tmemset(settings, 0, sizeof(*settings));\n}")

        return writer.code

    def build_H(self, headerguard: Optional[str] = None):
        """Builds Headerfile api extensions..."""
        writer = CodeWriter()
        headerguard = self.new_prefix.upper() if not headerguard else headerguard
        writer.putline(f"\n#ifndef {headerguard}_API_H_")
        writer.putline(f"#define {headerguard}_API_H_")
        writer.endline()
        writer.putline_with_format(
            "typedef %s_t %s_t;", self.info.prefix, self.new_prefix
        )
        writer.putline(
            f"typedef struct {self.new_prefix}_settings_s {self.new_prefix}_settings_t;"
        )
        writer.endline()
        writer.putline(
            f"typedef int (*{self.new_prefix}_data_cb)({self.new_prefix}_t*, const char *at, size_t length);"
        )
        writer.putline(f"typedef int (*{self.new_prefix}_cb)({self.new_prefix}_t*);")
        writer.endline()
        writer.putline(f"struct {self.new_prefix}_settings_s " + "{")
        with writer.indent():
            for data in self.data_cb:
                writer.putline(
                    f"{self.new_prefix}_data_cb {data.removeprefix(self.info.prefix).strip('_')};"
                )
            for data in self.cb:
                writer.putline(
                    f"{self.new_prefix}_cb {data.removeprefix(self.info.prefix).strip('_')};"
                )
        writer.putline("};")
        writer.endline()
        writer.putline(
            f"int {self.new_prefix}_execute({self.new_prefix}_t* parser, const char* data, size_t len);"
        )
        writer.putline(f"void {self.new_prefix}_init({self.new_prefix}_t* parser,")
        with writer.indent():
            writer.putline(f"const {self.new_prefix}_settings_t* settings);")
        writer.putline(
            f"void {self.new_prefix}_settings_init({self.new_prefix}_settings_t* settings);"
        )
        writer.putline(f"#endif /* {headerguard}_API_H_ */")
        return writer.code

    def build_pxd(self):
        writer = CythonWriter()

        writer.putline("#cython: language_level = 3")
        writer.endline()
        writer.putline("from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t")
        writer.endline()
        writer.putline("# Automatically generated in pyparse a parody of llparse")
        writer.putline(f'cdef extern from "{self.header_name or self.new_prefix}.h":')
        with writer.indent():
            writer.putline(f"struct {self.new_prefix}_t:")
            with writer.indent():
                ty = ""

                for prop in self.info.properties():
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
                    writer.putline("%s %s" % (ty, prop.name))
                writer.putline("void* data")

            writer.endline()
            writer.putline(
                f"ctypedef int (*{self.new_prefix}_data_cb)({self.new_prefix}_t*, const char *at, size_t length)"
            )
            writer.putline(
                f"ctypedef int (*{self.new_prefix}_cb)({self.new_prefix}_t*)"
            )
            writer.endline()
            writer.putline(f"struct {self.new_prefix}_settings_t:")
            with writer.indent():
                for data in sorted(self.data_cb):
                    writer.putline(
                        f"{self.new_prefix}_data_cb {data.removeprefix(self.info.prefix).strip('_')}"
                    )
                for data in sorted(self.cb):
                    writer.putline(
                        f"{self.new_prefix}_cb {data.removeprefix(self.info.prefix).strip('_')}"
                    )
            writer.endline()
            writer.putline(
                f"int {self.new_prefix}_execute({self.new_prefix}_t* parser, const char* data, size_t len)"
            )
            writer.putline(
                f"void {self.new_prefix}_init({self.new_prefix}_t* parser, const {self.new_prefix}_settings_t* settings)"
            )
        writer.endline()
        return writer.code
