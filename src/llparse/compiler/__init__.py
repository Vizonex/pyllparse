from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

from llparse_builder import builder as source
from llparse_frontend.frontend import Frontend

from ..implementation import c
from .header_builder import HeaderBuilder

logger = getLogger()

debug = logger.debug


@dataclass(slots=True)
class CompilerResult:
    c: str
    """Textual C code"""
    header: str
    """Textual C header file"""

    def write(self, c: Path | str, header: Path | str) -> None:
        """
        Writes the output to the chosen file locations

        :param c: Output for where to write the C File
        :type c: Path | str
        :param header: Output for where to write the Header File
        :type header: Path | str
        """
        Path(c).write_text(self.c)
        Path(header).write_text(self.header)


@dataclass
class Compiler:
    prefix: str
    header_guard: str | None = None
    debug: str | None = None
    max_table_elem_width: int | None = None
    min_table_size: int | None = None

    def to_frontend(
        self,
        root: source.node.Node,
        properties: list[source.Property],
        impl=c,
    ):
        """compiles up the frontend and brings you back the frontend's results.
        I added documentation to this function so that you can do creative things
        with the library beyond C..."""
        return Frontend(
            self.prefix,
            impl,
            max_table_elem_width=self.max_table_elem_width,
            min_table_size=self.min_table_size,
        ).compile(root, properties)

    def compile(
        self,
        root: source.node.Node,
        properties: list[source.Property],
        header_name: str | None = None,
        impl=c,
        override_llparse_name: bool = False,
    ) -> CompilerResult:
        """Creates the C and header file..."""
        info = self.to_frontend(root, properties, impl)
        hb = HeaderBuilder(self.prefix, self.header_guard, properties, info.spans)
        cdata = c.CCompiler(header_name, self.debug).compile(info)
        if override_llparse_name:
            # sometimes users want to combine parsers together when compiling with C
            # to make up for conflicts with other parsers example: llhttp
            # there should be a fair way of compiling everything.
            cdata = cdata.replace("llparse", self.prefix)

        return CompilerResult(cdata, hb.build())
