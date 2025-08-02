"""
Compiles a settings module to use alongside llparse

This is mostly a concept idea for llparse inspired by llhttp to include a settings
module in the future to make Writing the span callbacks and other important things
less painful to edit and write entirely.

NOTE: That The objects being passed would come directly from llparse-builder

"""

from dataclasses import dataclass, field
from typing import Optional, Union

from .llparse import LLParse
from .pybuilder import main_code as source

# MACRO Names , These can be renamed to
# prevent mixing with llhttp or other parsers
# allow for mulitple different parsers to be
# used at the same time...

CALLBACK_MAYBE = "CALLBACK_MAYBE"
SPAN_CALLBACK_MAYBE = "SPAN_CALLBACK_MAYBE"
MID_POSTFIX = "_settings"


@dataclass
class ApiResult:
    header: str
    c: str


@dataclass
class Settings:
    name: str
    """The property name to take from the settings module..."""
    prefix: str
    """The Prefix of your parser"""
    postfix: Optional[str] = None
    """The postfix of your parser"""
    callbacks: dict[str, bool] = field(default_factory=dict)
    """These are callbacks to be later edited out into thier appropreate places"""
    files: dict[str, dict[str, str]] = field(default_factory=dict)
    """Used to sort out functions if they are to be moved to different places these
    files will not affect the main api and can be ignored if chosen to be..."""

    external_execute_func: str = field(default_factory=str, init=False)
    """Allows the use of an external function and it's prefix to be called
        ```c
        
        int POSTFIX_execute(PREFIX_t* parser, const char* data, size_t len) {
          return PREFIX_execute(parser, data, data + len);
        }
        
        ```
        WARNIG! THIS SHOULD ONLY BE USED IF A POSTFIX HAS BEEN ADDED!"""

    # It can be annoying to have to recall something over and over again so I added the ability to use
    # Nodes and Code.Match classes to make up for this annoyance...
    def move_cb(
        self,
        callback: Union[str, source._Match, source.Node, source.Invoke],
        new_location: str,
        code: Optional[str] = None,
    ):
        """Moves the callback chosen to another file instead of the name of your api
        this can help you add things like custom C code, to non-api or user-interacted parts...
        """

        # Grab real name if the callback is a Node or Match otherwise get the string for it...

        name = (
            callback.name
            if isinstance(callback, (source.Code, source.Node))
            else callback
        )
        # If not added make a new dictioray / Map if your on typescript...
        if not self.files.get(new_location):
            self.files[new_location] = {}

        self.files[new_location][name] = code

        # Remove from default callbacks to be moved to another file in C...
        # If index fails (IndexError) the callback name doesn't exist...
        self.callbacks.pop(name)
        return self

    def add_external_execute(self, postfix_as_struct: bool = False):
        """Adds an external execute function as long as a postfix variable exists otherwise
        using this function this is not nessesary!
        ```c
        int POSTFIX_execute(PREFIX_t* parser, const char* data, size_t len) {
          return PREFIX_execute(parser, data, data + len);
        }
        ```
        Parameters
        ---
        `postfix_as_struct` use postfix struct instead of inside of POSTFIX_execute's function...
        """
        if self.postfix:
            self.external_execute_func += (
                f"int {self.postfix}_execute({self.postfix if postfix_as_struct else self.prefix}_t* parser, const char* data, size_t len) "
                + "{"
            )
            self.external_execute_func += (
                f"\nreturn {self.prefix}_execute(parser, data, data + len);\n" + "}"
            )

        return self

    def build_functions(self, out: list[str]):
        # Added newline to this one to reamin consistant with llhttp if the library devs decided to
        # implement my idea into thier projects
        out.append("/* CALLBACKS */\n")
        out.append("")
        # TODO Vizonex allow custom enum names to be passed as well in the next concept...
        for cb, is_span in self.callbacks.items():
            out.append(
                f"int {cb}({self.prefix}_t * s, const char* p, const char* endp) " + "{"
            )
            out.append("  int err;")
            if is_span:
                out.append(f"  {SPAN_CALLBACK_MAYBE}(s, {cb} ,p, endp - p);")
            else:
                out.append(f"  {CALLBACK_MAYBE}(s, {cb});")
            out.append("  return err;")
            # Close function and give some room for the next one to be placed into...
            out.append("}")
            out.append("")
        return

    def buildMacros(
        self,
        out: list[str],
        callback: str = CALLBACK_MAYBE,
        span_callback: str = SPAN_CALLBACK_MAYBE,
    ):
        """Builds Global Macro Callbacks"""
        # Inspired by llhttp
        out.append(
            f"#define {callback}(PARSER, NAME)                                          \\"
        )
        out.append(
            "do {                                                                        \\"
        )
        out.append(
            f"  const {self.prefix}{self.name}_t* settings;                               \\"
        )
        out.append(
            f"  settings = (const {self.prefix}{self.name}_t*) (PARSER)->{self.name};      \\"
        )
        out.append(
            "  if (settings == NULL || settings->NAME == NULL) {                         \\"
        )
        out.append(
            "    err = 0;                                                                \\"
        )
        out.append(
            "    break;                                                                  \\"
        )
        out.append(
            "  }                                                                         \\"
        )
        out.append(
            "  err = settings->NAME((PARSER));                                           \\"
        )
        out.append("} while (0)")
        out.append("")

        out.append(
            f"#define {span_callback}(PARSER, NAME, START, LEN)                         \\"
        )
        out.append(
            "  do {                                                                        \\"
        )
        out.append(
            f"  const {self.prefix}{self.name}_t* settings;                               \\"
        )
        out.append(
            f"  settings = (const {self.prefix}{self.name}_t*) (PARSER)->{self.name};      \\"
        )
        out.append(
            "    if (settings == NULL || settings->NAME == NULL) {                         \\"
        )
        out.append(
            "      err = 0;                                                                \\"
        )
        out.append(
            "      break;                                                                  \\"
        )
        out.append(
            "    }                                                                         \\"
        )
        out.append(
            "    err = settings->NAME((PARSER), (START), (LEN));                           \\"
        )
        # TODO: maybe allow for custom error functions to be raised right here
        # or from or with both of them optionally? --
        out.append("  } while (0)")
        out.append("\n\n\n")

    def build_C(self, cb: str, span_cb: str):
        out = []
        out.append("#include <stdlib.h>")
        out.append("#include <stdio.h>")
        out.append("#include <string.h>")
        out.append("")
        out.append(f'#include "{self.prefix}.h"')
        out.append("")
        self.buildMacros(out, cb, span_cb)
        self.build_functions(out)
        return "\n".join(out)

    def build_H(self):
        out = []

        fix = self.postfix if self.postfix else self.prefix

        out.append(f"typedef struct {fix}{self.name}_s {fix}{self.name}_t;")
        out.append(
            f"typedef int (*{fix}_data_cb)({fix}_t*, const char *at, size_t length);"
        )
        out.append(f"typedef int (*{fix}_cb)({fix}_t*);")

        out.append(f"struct {self.prefix}{self.name}_s " + "{")
        for cb, is_span in self.callbacks.items():
            if is_span:
                out.append(f"  {fix}_data_cb {cb};")
            else:
                out.append(f"  {fix}_cb {cb};")
        out.append("};")


class Disassembler:
    """Takes apart LLParse's calls and sorts the data out to help make
    different things such as a settings api moudle, Cython pxd file
    and a Typescript Writer, and a Json model of what's going on...
    """

    def __init__(self, builder: LLParse) -> None:
        self.invokes: set[source.Invoke] = set()
        self.nodes: dict[str, source.Node] = {}
        """Used to create a small dictionary of all avalible nodes to thier corresponding names.
        this also includes it's edges used and seen to create a json file if chosen."""
        self.empty_apis: dict[str, bool] = {}
        """Carries some of the main api calls to make in a settings module...
        These carry thier own boolean to see weather or not the callback is a `Span` (True) , 
        `Match` (False)..."""
        self.prefix = builder.prefix
        self.properties = builder.privProperties
        """Carries important property values"""

    def disassemble(self, root: source.Node):
        """Takes root apart and enumerates through all the major parts
        returns itself as a convenience measure..."""
        reach = source.Reachability()
        roots = reach.build(root)
        # Get all span's names and objects themselves...
        # Turn span_names into a set
        self.nodes = {n.name: n for n in roots}
        # print(self.nodes)
        span_names = list(
            sorted(
                {
                    n.span.callback.name
                    for n in roots
                    if isinstance(n, (source.SpanStart, source.SpanEnd))
                }
            )
        )
        # span_starts = {n.span.callback.name:n for n in roots if isinstance(n,source.SpanStart)}

        self.empty_apis.update({sn: True for sn in span_names})

        invokes = [n for n in roots if isinstance(n, source.Invoke)]

        for i in invokes:
            # I have Match Underscored because in my version of the library there's two of them in the same file.
            # The one with the underscore is for use with Invoke...
            if isinstance(i.code, source._Match):
                self.empty_apis[i.code.name] = False

        return self
