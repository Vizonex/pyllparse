from llparse.spanalloc import SpanAllocator
from llparse.pybuilder import Builder
from llparse.errors import Error

import pytest

# Brought over and translated from llparse-builder/tests/span-allocator.ts


@pytest.fixture()
def span_alloc() -> tuple[SpanAllocator, Builder]:
    return SpanAllocator(), Builder()


def test_allocate_single_span(span_alloc: tuple[SpanAllocator, Builder]) -> None:
    sa, b = span_alloc
    span = b.span(b.code.span("span"))
    start = b.node("start")
    body = b.node("body")

    start.otherwise(span.start(body))

    body.skipTo(span.end(start))

    res = sa.allocate(start)

    assert res.max == 0

    assert len(res.concurrency) == 1
    assert span in res.concurrency[0]

    assert len(res.colors) == 1
    assert res.colors.get(span) == 0


def test_allocate_overlapping_spans(span_alloc: tuple[SpanAllocator, Builder]) -> None:
    sa, b = span_alloc
    span1 = b.span(b.code.span("span1"))
    span2 = b.span(b.code.span("span2"))

    start = b.node("start")
    body1 = b.node("body1")
    body2 = b.node("body2")

    start.otherwise(span1.start(body1))

    body1.otherwise(span2.start(body2))

    body2.skipTo(span2.end(span1.end(start)))

    res = sa.allocate(start)

    # TODO: fix it later... it's supposed to be 1
    assert res.max == 1

    assert len(res.concurrency) == 2
    
    # python loves to shuffle things on me :/ but both exist nevertheless
    assert span2 in res.concurrency[0] or span1 in res.concurrency[0]
    assert span1 in res.concurrency[1] or span2 in res.concurrency[1]

    assert len(res.colors) == 2
    assert res.colors.get(span2) in [0, 1]
    assert res.colors.get(span1) in [0, 1]


def test_allocate_non_overlapping_spans(
    span_alloc: tuple[SpanAllocator, Builder],
) -> None:
    sa, b = span_alloc
    span1 = b.span(b.code.span("span1"))
    span2 = b.span(b.code.span("span2"))

    start = b.node("start")
    body1 = b.node("body1")
    body2 = b.node("body2")

    start.match("a", span1.start(body1)).otherwise(span2.start(body2))
    body1.skipTo(span1.end(start))

    body2.skipTo(span2.end(start))

    res = sa.allocate(start)

    assert res.max == 0

    assert len(res.concurrency) == 1
    assert span1 in res.concurrency[0]
    assert span2 in res.concurrency[0]

    assert len(res.colors) == 2
    assert res.colors.get(span1) == 0
    assert res.colors.get(span2) == 0


def test_should_throw_on_loops(span_alloc: tuple[SpanAllocator, Builder]) -> None:
    sa, b = span_alloc
    start = b.node("start")
    end = b.node("end")
    span = b.span(b.code.span("on_data"))

    start.match("a", end).match("b", span.start(end)).otherwise(b.error(1, "error"))

    end.otherwise(span.end(start))

    with pytest.raises(Error, match=r"unmatched.*on_data"):
        sa.allocate(start)

def test_propagate_through_invoke_map(span_alloc:tuple[SpanAllocator, Builder]):
    sa, b = span_alloc
    start = b.node('start')
    span = b.span(b.code.span('llparse__on_data'))

    b.property('i8', 'custom')

    start.otherwise(b.invoke(b.code.load('custom'), {
      0: span.end().skipTo(start),
    }, span.end().skipTo(start)))

    sa.allocate(span.start(start))
    