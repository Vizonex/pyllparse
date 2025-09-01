""""""

from dataclasses import dataclass
from typing import Optional

from .C_compiler import CCompiler
from .frontend import (
    DEFAULT_MAX_TABLE_WIDTH,
    DEFAULT_MIN_TABLE_SIZE,
    Frontend,
    IImplementation,
    source,
)
from .header import HeaderBuilder


@dataclass
class CompilerResult:
    c: str
    """Textual C code"""
    header: str
    """Textual C header file"""

    # NOTE Coming soon... I will making a settings compiler which is attached to CompilerResult to Compile your own
    # settings structures and be able to concate it to the existing header file like in llhttp
    # I'm also in the works of adding a Cython .pxd import as well...


class Compiler:
    """Used to Compile C code together"""

    def __init__(
        self,
        prefix: str,
        headerGuard: Optional[str] = None,
        debug: Optional[str] = None,
        maxTableElemWidth: Optional[int] = None,
        minTableSize: Optional[int] = None,
    ):
        self.prefix = prefix
        self.headerGuard = headerGuard
        self.debug = debug
        self.maxTableElemWidth = maxTableElemWidth
        self.minTableSize = minTableSize

    def to_frontend(
        self,
        root: source.code.Node,
        properties: list[source.Property],
        Impl: Optional[IImplementation] = IImplementation(),
    ):
        """compiles up the frontend and brings you back the frontend's results.
        I added documentation to this function so that you can do creative things
        with the library beyond C..."""
        return Frontend(
            self.prefix,
            Impl,
            options={
                "maxTableElemWidth": self.maxTableElemWidth,
                "minTableSize": self.minTableSize,
            },
        ).compile(root, properties)

    def compile(
        self,
        root: source.code.Node,
        properties: list[source.Property],
        header_name: Optional[str] = None,
        Impl: Optional[IImplementation] = IImplementation(),
        override_llparse_name: bool = False
    ):
        """Creates the C and header file..."""
        info = self.to_frontend(root, properties, Impl)
        hb = HeaderBuilder(self.prefix, self.headerGuard, properties, info.spans)
        cdata =  CCompiler(header_name, self.debug).compile(info)
        if override_llparse_name:
            # sometimes users want to combine parsers together when compiling with C
            # to make up for conflicts with other parsers example: llhttp
            # there should be a fair way of compiling everything.
            cdata = cdata.replace('llparse', self.prefix)

        return CompilerResult(
           cdata , hb.build()
        )


class LLParse(source.Builder):
    """

    The prefix controls the names of methods and state struct in generated
    public C headers:

    ```c
    // state struct
    struct PREFIX_t {
      ...
    }

    int PREFIX_init(PREFIX_t* state);
    int PREFIX_execute(PREFIX_t* state, const char p, const char endp);
    ```

    `prefix`  Prefix to be used when generating public API.
    """

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        super().__init__()

    def get_compiler(
        self,
        headerGuard: Optional[str] = None,
        debug: Optional[str] = None,
        maxTableElemWidth: Optional[int] = None,
        minTableSize: Optional[int] = None,
    ):
        return Compiler(
            self.prefix,
            headerGuard,
            debug,
            maxTableElemWidth if maxTableElemWidth else DEFAULT_MAX_TABLE_WIDTH,
            minTableSize if minTableSize else DEFAULT_MIN_TABLE_SIZE,
        )

    def build(
        self,
        root: source.code.Node,
        headerGuard: Optional[str] = None,
        debug: Optional[str] = None,
        maxTableElemWidth: Optional[int] = None,
        minTableSize: Optional[int] = None,
        header_name: Optional[str] = None,
        override_llparse_name:bool = False
    ):
        """Builds Graph and then compiles the data into C code , returns with the header and C file inside of a Dataclass"""

        compiler = Compiler(
            self.prefix,
            headerGuard,
            debug,
            maxTableElemWidth if maxTableElemWidth else DEFAULT_MAX_TABLE_WIDTH,
            minTableSize if minTableSize else DEFAULT_MIN_TABLE_SIZE,
        )

        return compiler.compile(root, self.properties(), header_name=header_name, override_llparse_name=override_llparse_name)
    

    def to_frontend(
        self,
        root: source.code.Node,
        headerGuard: Optional[str] = None,
        debug: Optional[str] = None,
        maxTableElemWidth: Optional[int] = None,
        minTableSize: Optional[int] = None,
    ):
        """Used as an external hack to get access to the frontend of llparse and extract
        it's contents to compile the libraries you make other things like cython, This is not in llparse
        specifically (Yet...)"""
        return Compiler(
            self.prefix,
            headerGuard,
            debug,
            maxTableElemWidth if maxTableElemWidth else DEFAULT_MAX_TABLE_WIDTH,
            minTableSize if minTableSize else DEFAULT_MIN_TABLE_SIZE,
        ).to_frontend(root, self.properties)
