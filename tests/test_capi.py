"""
Tests tools for writing C-API Wrappers
"""
from llparse import LLParse
import re

import pytest

DUMMY_HEADER = """#ifndef LLPARSE_CAPI_INCLUDE
#define LLPARSE_CAPI_INCLUDE
#ifdef __cplusplus
extern "C" {
#endif
#include <stddef.h>
#include <stdint.h>

#if defined(__wasm__)
#define LLPARSE_EXPORT __attribute__((visibility("default")))
#elif defined(_WIN32)
#define LLPARSE_EXPORT __declspec(dllexport)
#else
#define LLPARSE_EXPORT
#endif

typedef llparse_internal_t llparse_t;
typedef struct llparse_settings_s llparse_settings_t;
typedef int (*llparse_data_cb)(llparse_t*, const char* at, size_t length);
typedef int (*llparse_cb)(llparse_t*);

struct llparse_settings_s {
    /* Spans */
    llparse_data_cb      llparse_on_span;
    /* Callbacks */
    llparse_cb     llparse_on_test;
};

LLPARSE_EXPORT
void llparse_settings_init(llparse_settings_t* settings);

LLPARSE_EXPORT
int llparse_execute(llparse_t* parser, const char* data, size_t len);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* LLPARSE_CAPI_INCLUDE */
"""



@pytest.fixture()
def llparse() -> LLParse:
    return LLParse("llparse_internal")

def test_collecting_spans(llparse:LLParse):
    lc = llparse.capi("llparse")
    span = llparse.span(llparse.code.span("span"))
    start = llparse.node("start")
    body = llparse.node("body")

    start.otherwise(span.start(body))

    body.skipTo(span.end(start))

    lc.use("span")
    result = lc.filter(start)
    assert result.use.spans, "No spans found"


def test_collecting_matches(llparse:LLParse):
    lc = llparse.capi("lc")
    span = llparse.span(llparse.code.span("llparse_on_span"))
    on_test = llparse.code.match("llparse_on_test")

    start = llparse.node("start")
    body = llparse.node("body")

    start.otherwise(
        span.start(body)
    )

    body.skipTo(
        span.end(
            llparse.invoke(on_test, {0:start}, llparse.error(-1, "error"))
        )
    )
    lc.use("llparse_")
    result = lc.filter(start)
    assert result.use.spans, "No spans found"
    assert result.use.matches, "No matches found"


def test_write_capi(llparse:LLParse):
    lc = llparse.capi("llparse")
    span = llparse.span(llparse.code.span("llparse_on_span"))
    on_test = llparse.code.match("llparse_on_test")

    start = llparse.node("start")
    body = llparse.node("body")

    start.otherwise(
        span.start(body)
    )

    body.skipTo(
        span.end(
            llparse.invoke(on_test, {0:start}, llparse.error(-1, "error"))
        )
    )

    lc.use("span")
    lc.use_regex(r"llparse_([^\s]+)")

    
    result = lc.build(start)
    assert result.header.strip() == DUMMY_HEADER.strip()




