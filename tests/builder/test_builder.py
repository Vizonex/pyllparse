import pytest

from llparse_builder import Builder


def test_primitive_graph(b: Builder):
    start = b.node("start")
    end = b.node("end")

    start.peek("e", end).match("a", start).otherwise(b.error(1, "error"))
    end.skip_to(start)
    edges = start.priv_edges
    assert len(edges) == 2
    assert not edges[0].no_advance
    assert edges[0].node == start
    assert edges[1].no_advance
    assert edges[1].node == end


def test_disallowing_duplicate_edges(b: Builder):
    start = b.node("start")
    start.peek("e", start)

    with pytest.raises(AssertionError):
        start.peek("e", start)


def test_disallowing_select_to_match_invoke(b: Builder):
    start = b.node("start")
    invoke = b.invoke(b.code.match("something"))

    with pytest.raises(AssertionError):
        start.select("a", 1, invoke)


def test_disallow_peek_to_value_invoke(b: Builder):
    start = b.node("start")
    invoke = b.invoke(b.code.value("something"))
    with pytest.raises(AssertionError):
        start.peek("a", invoke)


def test_allow_select_to_value_invoke(b: Builder):
    start = b.node("start")
    invoke = b.invoke(b.code.value("something"))
    start.select("a", 1, invoke)


def test_allow_create_edges_for_invoke(b: Builder):
    start = b.node("start")
    invoke = b.invoke(
        b.code.value("something"),
        {
            -1: start,
            1: start,
            10: start,
        },
    )
    edges = {e.key for e in invoke.priv_edges}
    assert edges == {-1, 1, 10}
