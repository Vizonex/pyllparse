from llparse_builder import builder as source
from llparse_frontend import frontend

from .compiler import Compiler, CompilerResult


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
    """

    def __init__(self, prefix: str = "llparse") -> None:
        """
        :param prefix: Prefix to be used when generating public API default is "llparse".
        """
        self.prefix = prefix
        super().__init__()

    def get_compiler(
        self,
        headerGuard: str | None = None,
        debug: str | None = None,
        max_table_elem_width: int | None = None,
        min_table_size: int | None = None,
    ) -> Compiler:
        return Compiler(
            self.prefix,
            headerGuard,
            debug,
            max_table_elem_width
            if max_table_elem_width
            else frontend.DEFAULT_MAX_TABLE_WIDTH,
            min_table_size if min_table_size else frontend.DEFAULT_MIN_TABLE_SIZE,
        )

    def build(
        self,
        root: source.node.Node,
        headerGuard: str | None = None,
        debug: str | None = None,
        max_table_elem_width: int | None = None,
        min_table_size: int | None = None,
        header_name: str | None = None,
        override_llparse_name: bool = False,
    ) -> CompilerResult:
        """Builds Graph and then compiles the data into C code , returns with the header and C file inside of a Dataclass"""

        compiler = Compiler(
            self.prefix,
            headerGuard,
            debug,
            max_table_elem_width
            if max_table_elem_width
            else frontend.DEFAULT_MAX_TABLE_WIDTH,
            min_table_size if min_table_size else frontend.DEFAULT_MIN_TABLE_SIZE,
        )

        return compiler.compile(
            root,
            self.properties(),
            header_name=header_name,
            override_llparse_name=override_llparse_name,
        )

    def to_frontend(
        self,
        root: source.node.Node,
        headerGuard: str | None = None,
        debug: str | None = None,
        max_table_elem_width: int | None = None,
        min_table_size: int | None = None,
    ) -> Compiler:
        """Used as an external hack to get access to the frontend of llparse and extract
        it's contents to compile the libraries you make other things like cython, This is not in llparse
        specifically (Yet...)"""
        return Compiler(
            self.prefix,
            headerGuard,
            debug,
            max_table_elem_width
            if max_table_elem_width
            else frontend.DEFAULT_MAX_TABLE_WIDTH,
            min_table_size if min_table_size else frontend.DEFAULT_MIN_TABLE_SIZE,
        ).to_frontend(root, self.properties)

    # capi will return soon...
