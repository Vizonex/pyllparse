"""Used to build apis and more from llparse WARNING:
This may or may not be stable yet!!!"""

from __future__ import annotations

import re  # inspired by rust's bindgen clang compiler
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum
from typing import (
    TYPE_CHECKING,
)  # TODO: retire any 3.9 code in a future update and drop it's support with a cherrypicker file.

from ._tempita import Template
from .pybuilder import main_code as builder
from .pybuilder.parsemap import traverse

if TYPE_CHECKING:
    from .llparse import LLParse

if sys.version_info < (3, 13, 3):
    from typing_extensions import deprecated
else:
    from warnings import deprecated

# Inspired by Cython's Writer

# You will notice many simillarities
# because there's was no way to for me to optimize the
# originals further than what was given by Cython itself.
# This will be used to help me write my own custom
# Finite Machine Parts

# VA_ARGS_CALLBACK = """#define CALLBACK_MAYBE(PARSER, NAME, ...)                                     \\
#   do {                                                                        \\
#     %s_settings_t* settings;                                              \\
#     settings = (%s_settings_t*) (PARSER)->settings;                       \\
#     if (settings == NULL || settings->NAME == NULL) {                         \\
#       err = 0;                                                                \\
#       break;                                                                  \\
#     }                                                                         \\
#     err = settings->NAME(__VA_ARGS__);                                        \\
#   } while (0)"""

API_C_CODE = Template("""
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "{{header}}"
 
/* Prevent Interfearing with other parsers (example: llhttp) */
#define {{upper}}_CALLBACK_MAYBE(PARSER, NAME)                                      \\
   do {                                                                        \\
     {{prefix}}_settings_t* settings;                                                  \\
     settings = ({{prefix}}_settings_t*) (PARSER)->settings;                           \\
     if (settings == NULL || settings->NAME == NULL) {                         \\
       err = 0;                                                                \\
       break;                                                                  \\
     }                                                                         \\
     err = settings->NAME((PARSER));                                        \\
   } while (0)

#define {{upper}}_SPAN_CALLBACK_MAYBE(PARSER, NAME, START, LEN)                         \
  do {                                                                        \\
    const {{prefix}}_settings_t* settings;                                        \\
    settings = (const {{prefix}}_settings_t*) (PARSER)->settings;                 \\
    if (settings == NULL || settings->NAME == NULL) {                         \\
      err = 0;                                                                \\
      break;                                                                  \\
    }                                                                         \\
    err = settings->NAME((PARSER), (START), (LEN));                           \\
  } while (0)

/* Custom Underrived from llhttp */
#define {{upper}}_VALUE_CALLBACK_MAYBE(PARSER, NAME, VALUE)                        \\
   do {                                                                        \\
     {{prefix}}_settings_t* settings;                                                  \\
     settings = ({{prefix}}_settings_t*) (PARSER)->settings;                           \\
     if (settings == NULL || settings->NAME == NULL) {                         \\
       err = 0;                                                                \\
       break;                                                                  \\
     }                                                                         \\
     err = settings->NAME((PARSER), (VALUE));                                        \\
   } while (0)


void {{prefix}}_set_error_reson({{prefix}}_t* parser, const char* reason){
    parser->reason = reason;
}

/* Spans */
{{for name, setting_name in spans}}
int {{name}}({{prefix}}_t* s, const char* p, const char* endp){
    int err;
    {{upper}}_SPAN_CALLBACK_MAYBE(s, {{setting_name}}, p, endp - p);
    return err;
}
{{endfor}}
/* Match */
{{for name, setting_name in matches}}                      
int {{name}}({{prefix}}_t* s, const char* p, const char* endp){
    int err;
    {{upper}}_CALLBACK_MAYBE(s, {{setting_name}});
    return err;
}
{{endfor}}

/* Values */
{{for name, setting_name in values}} 
int {{name}}({{prefix}}_t* s, const char* p, const char* endp, int value){
    int err;
    {{upper}}_VALUE_CALLBACK_MAYBE(s, {{setting_name}});
    return err;                      
}
{{endfor}}

                      
/* API */

void {{prefix}}_settings_init({{prefix}}_settings_t* settings) {
    memset(settings, 0, sizeof(*settings));
}

""")


API_C_HEADER = Template(
    """
#ifndef {{headerguard}}
#define {{headerguard}}
#ifdef __cplusplus
extern "C" {
#endif
#include <stddef.h>

#if defined(__wasm__)
#define {{export}} __attribute__((visibility("default")))
#elif defined(_WIN32)
#define {{export}} __declspec(dllexport)
#else
#define {{export}}
#endif

typedef {{prev_prefix}}_t {{prefix}}_t;
typedef struct {{prefix}}_settings_s {{prefix}}_settings_t;

{{if spans}}
typedef int (*{{prefix}}_data_cb)({{prefix}}_t*, const char* at, size_t length);
{{endif}}

{{if matches}}
typedef int (*{{prefix}}_cb)({{prefix}}_t*);
{{endif}}

{{if values}}
typedef int (*{{prefix}}_value_cb)({{prefix}}_t*, int value);
{{endif}}

struct {{prefix}}_settings_s {
    {{if spans}}
    /* Spans */
    {{for _, name in spans}}{{prefix}}_data_cb      {{name}};{{endfor}}
    
    {{endif}}
    {{if values}}
    /* Value Callbacks */
    {{for _, name in values}}{{prefix}}_value_cb      {{name}};{{endfor}}
    
    {{endif}}
    {{if matches}}
    /* Callbacks */
    {{for _, name in matches}}{{prefix}}_cb     {{name}};{{endfor}}
    {{endif}}
};

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* {{headerguard}} */
"""
)


# {{if matches}}
# {{for _, name in matches}}
# {{prefix}}_cb      {{name}};
# {{endfor}}
# {{endif}}
# {{if values}}
# {{for _, name in values}}
# {{prefix}}_value_cb     {{name}};
# {{endif}}

# Forked from Cython
class LineWriter:
    __slots__ = ("lines", "s")
    def __init__(self, lines: list[str] = []) -> None:
        self.lines = lines
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


class Filter:
    """A Filter to go off for match, value, and spans
    to help organize the output for an llhttp-like C
    Library"""

    __slots__ = ("_pattern", "_is_re", "_use")

    def __init__(self, pattern: str | re.Pattern[str], use: bool):
        if isinstance(pattern, re.Pattern):
            self._pattern = pattern
            if use and (not self._pattern.groups):
                raise ValueError(
                    "regex needs a group to derrive from for making the callback fields"
                )
            self._is_re = True
        elif isinstance(pattern, str):
            self._pattern = pattern
            self._is_re = False
        else:
            # Smarter error for saying b"llparse_" uses bytes which is invalid
            raise TypeError(
                f"expected a regex pattern or str type, {pattern} uses {type(pattern).__name__}"
            )
        self._use = use

    @property
    def ignore(self) -> bool:
        return not self._use

    @property
    def use(self) -> bool:
        return self._use

    def is_match(self, name: str) -> bool:
        """Determines if the source matches up"""
        if self._is_re:
            return re.search(self._pattern) is not None
        else:
            # it's most likely a prefix of ignorable callbacks...
            return name.startswith(self._pattern)

    def edit_name(self, name: str) -> str:
        """Ran when use is enabled"""
        assert self._use, "edit_name can only be used with use filters"
        if self._is_re:
            assert (result := self._pattern.search(name)), (
                f"use filter should've matched with {self._pattern} but wasn't"
            )
            return result.group()
        else:
            return name.removeprefix(self._pattern)

    # Make editable in a set...
    def __hash__(self):
        return hash(self._pattern)


class ResultType(IntEnum):
    SPAN = 0
    MATCH = 1
    VALUE = 2


@dataclass(slots=True)
class IgnoredResults:
    spans: list[str] = field(default_factory=list)
    """span callbacks"""
    matches: list[str] = field(default_factory=list)
    """match callbacks"""
    values: list[str] = field(default_factory=list)
    """value callbacks"""

    def add(self, name: str, ty: ResultType) -> None:
        if ty == ResultType.SPAN:
            self.spans.append(name)

        elif ty == ResultType.MATCH:
            self.matches.append(name)

        elif ty == ResultType.VALUE:
            self.values.append(name)
        # Rare case scenario where a new node is introduce but unimplemented...
        else:
            raise TypeError(f"unknown type for name:{name} type:{ty}")


@dataclass(slots=True)
class UsedResults:
    spans: list[tuple[str, str]] = field(default_factory=list)
    """span callbacks"""
    matches: list[tuple[str, str]] = field(default_factory=list)
    """match callbacks"""
    values: list[tuple[str, str]] = field(default_factory=list)
    """value callbacks"""

    def add(self, filt: Filter, name: str, ty: ResultType):
        pair = (name, filt.edit_name(name))
        if ty == ResultType.SPAN:
            self.spans.append(pair)
        elif ty == ResultType.MATCH:
            self.matches.append(pair)
        elif ty == ResultType.VALUE:
            self.values.append(pair)
        # Rare case scenario where a new node is introduce but unimplemented...
        else:
            raise TypeError(f"unknown type for name:{name} type:{ty}")


@dataclass
class Results:
    ignore: IgnoredResults = field(default_factory=IgnoredResults)
    """Seperates into a non-api file under a .c suffix these
    must be configured by the end user..."""

    use: UsedResults = field(default_factory=UsedResults)
    """Seperates into an api file under a .c suffix"""

    def add(self, filt: Filter, name: str, ty: ResultType):
        if filt.use:
            self.use.add(filt, name, ty)
        else:
            self.ignore.add(name, ty)


@dataclass
class CAPIResult:
    c: str
    header: str


class LibraryCompiler:
    """Used for writing in what callbacks to mark as wrappable or don't use
    this will help with the creation of a settings structure for making your
    parser into a real C Library"""

    __slots__ = ("_filters", "_dummy_ignore", "_prefix", "_previous_prefix")

    def __init__(self, prefix: str, llparse: LLParse):
        self._filters: set[Filter] = set()
        # Put all ignored spans, matches and values here...
        self._dummy_ignore = Filter("dummy", False)
        self._prefix = prefix
        self._previous_prefix = llparse.prefix

    def use_regex(self, *expr: str) -> None:
        """Use this regular expression for using this match, span or value
        it's an equivilent of `use(re.compile(expr))`"""
        return self.use(*map(re.compile, expr))

    def use(self, *expr: str | re.Pattern[str]) -> None:
        """Tells the compiler to use these expression or regexes if it matches
        :param expr: A single expr or multiple expressions to use when looking
        for settings to make into wrappable callbacks"""
        return self._filters.update(map(lambda x: Filter(x, use=True), expr))

    def ignore_regex(self, *expr: str) -> None:
        """Ignore this regular expression for using this match, span or value
        it's an equivilent of `ignore(re.compile(expr))`"""
        return self._filters.update(*map(re.compile, expr))

    def ignore(self, *expr: str | re.Pattern[str]) -> None:
        """Tells the compiler to ignore these expression or regexes if it matches
        :param expr: A single expr or multiple expressions to use when looking
        for settings to make into wrappable callbacks"""
        return self._filters.update(map(lambda x: Filter(x, use=False), expr))

    def filter_name(self, name: str):
        for f in self._filters:
            if f.is_match(name):
                return f, name
        return self._dummy_ignore, name

    def filter(self, root: builder.Node) -> Results:
        """Peforms node filtering for the real setup"""

        results = Results()
        for node in traverse(root):
            # Look for spans and invokes...
            if isinstance(node, builder.SpanStart):
                if pair := self.filter_name(node.real_name):
                    results.add(pair[0], pair[1], ResultType.SPAN)
            elif isinstance(node, builder.Invoke):
                # Added special shortcut value to identify Code Matches
                # and Value Code objects
                if node.code.is_independent:
                    if pair := self.filter_name(node.code.name):
                        results.add(
                            pair[0],
                            pair[1],
                            ResultType.MATCH
                            if node.code.signature == "match"
                            else ResultType.VALUE,
                        )
        return results

    @deprecated(
        "Use build(...) instead, compile_capi was too vauge. will be removed in 0.3.0"
    )
    def compile_capi(
        self,
        root: builder.Node,
        header: str | None = None,
        headerguard: str | None = None,
    ) -> CAPIResult:
        """
        Compile library's data and create a header file and other external for the library's c-api
        Warning: This function's name is deprecated use build(...) instead.

        :param root: the root node to recurse off from
        :type root: builder.Node
        :param header: The Name of the Header file
        :type header: str | None
        :param headerguard: The Macro's name for the Header guard
        :type headerguard: str | None
        :return: The CAPI Result containing extra files for the c-wrapper
        :rtype: CAPIResult

        """
        return self.build(root, header, headerguard)

    def build(
        self,
        root: builder.Node,
        header: str | None = None,
        headerguard: str | None = None,
    ) -> CAPIResult:
        """
        Compile library's data and create a header file and other external for the library's c-api

        :param root: the root node to recurse off from
        :type root: builder.Node
        :param header: The Name of the Header file
        :type header: str | None
        :param headerguard: The Macro's name for the Header guard
        :type headerguard: str | None
        :return: The CAPI Result containing extra files for the c-wrapper
        :rtype: CAPIResult

        """

        results = self.filter(root)
        used = results.use
        api_code = API_C_CODE.substitute(
            prefix=self._prefix,
            values=used.values,
            matches=used.matches,
            spans=used.spans,
            upper=self._prefix.upper(),
            header=header or (self._prefix + ".h"),
        )
        header_code = API_C_HEADER.substitute(
            prefix=self._prefix,
            values=used.values,
            matches=used.matches,
            spans=used.spans,
            upper=self._prefix.upper(),
            export=self._prefix.upper() + "_EXPORT",
            headerguard=headerguard or f"{self._prefix.upper()}_CAPI_INCLUDE",
            prev_prefix=self._previous_prefix,
        )
        return CAPIResult(api_code, header_code)
