from typing import cast

import pytest

from llparse_builder import builder as source
from llparse_frontend import node
from llparse_frontend.frontend import Frontend

from .fixtures import implementation
from .fixtures.implementation.node.base import Node


@pytest.fixture
def f() -> Frontend:
    return Frontend("llparse", implementation)


def check_nodes(f: Frontend, root: source.node.Node, expected: list[str]):
    f_root = cast(Node[node.Node], f.compile(root, []).root)
    out = []

    f_root.build(out)

    # XXX: we don't expect the python parody to lay these
    # out exactly as typescript does we just care about
    # the functionality and how it works. Ordering is not a concern.

    for line in out:
        print(line)
        assert line in expected


def check_resumption_targets(f: Frontend, expected: list[str]):
    targets = [t.ref.id.name for t in f.resumption_targets]

    for line in targets:
        assert line in expected


def test_node_implementation_translation(f: Frontend, b: source.Builder) -> None:
    root = b.node("root")

    root.match("ab", root)
    root.match("acd", root)
    root.match("efg", root)
    root.otherwise(b.error(123, "hello"))

    check_nodes(
        f,
        root,
        [
            "<Single name=llparse__n_root k101=llparse__n_root k97=llparse__n_root otherwise=-no_advllparse__n_error/>",
            "<Single name=llparse__n_root k102=llparse__n_root otherwise=-no_advllparse__n_error/>",
            "<Single name=llparse__n_root k103=llparse__n_root otherwise=-no_advllparse__n_error/>",
            "<ErrorNode name=llparse__n_error />",
            "<Single name=llparse__n_root k98=llparse__n_root k99=llparse__n_root otherwise=-no_advllparse__n_error/>",
            "<Single name=llparse__n_root k100=llparse__n_root otherwise=-no_advllparse__n_error/>",
        ],
    )

    check_resumption_targets(
        f,
        # any order can be done as long as all of them are here...
        [
            "llparse__n_root",
            "llparse__n_root_1",
            "llparse__n_root_2",
            "llparse__n_root_3",
        ],
    )


def test_peephole_optimization(f: Frontend, b: source.Builder) -> None:
    root = b.node("root")
    root1 = b.node("a")
    root2 = b.node("b")
    node1 = b.node("c")
    node2 = b.node("d")

    root.otherwise(root1)
    root1.otherwise(root2)
    root2.skip_to(node1)
    node1.otherwise(node2)
    node2.otherwise(root)

    check_nodes(
        f,
        root,
        [
            "<Empty name=llparse__n_b  otherwise=llparse__n_b/>",
        ],
    )

    check_resumption_targets(
        f,
        [
            "llparse__n_b",
        ],
    )


def test_resumption_targets(b: source.Builder, f: Frontend):
    b.property("i64", "counter")
    root = b.node("root")
    end = b.node("end")
    store = b.invoke(b.code.store("counter"))

    root.select({"a": 1, "b": 2}, store)
    root.otherwise(b.error(1, "okay"))

    store.otherwise(end)

    end.match("ohai", root)
    end.match(
        "paus", b.pause(1, "paused").otherwise(b.pause(2, "paused").otherwise(root))
    )
    end.otherwise(b.error(2, "ohai"))

    check_nodes(
        f,
        root,
        [
            "<Single name=llparse__n_root k98=llparse__n_invoke_store_counter:2 k97=llparse__n_invoke_store_counter:1 otherwise=-no_advllparse__n_error/>",
            "<Invoke name=llparse__n_invoke_store_counter  otherwise=-no_advllparse__n_end/>",
            "<Single name=llparse__n_end k112=llparse__n_end k111=llparse__n_end otherwise=-no_advllparse__n_error/>",
            '<Sequence name=llparse__n_end select="617573" edge="llparse__n_pause" otherwise=-no_advllparse__n_error/>',
            "<Pause name=llparse__n_pause  otherwise=-no_advllparse__n_pause/>",
            "<ErrorNode name=llparse__n_error />",
            '<Sequence name=llparse__n_end select="686169" edge="llparse__n_root" otherwise=-no_advllparse__n_error/>',
        ],
    )

    check_resumption_targets(
        f,
        [
            "llparse__n_root",
            "llparse__n_end",
            "llparse__n_end_1",
            "llparse__n_end_2",
            "llparse__n_pause_1",
        ],
    )
