from llparse import LLParse
from llparse.pybuilder.main_code import Operator

import pytest


@pytest.fixture(params=[">", "<", ">=", "<="])
def op(request: pytest.FixtureRequest) -> str:
    return request.param


def test_build_tables():
    # There was a bug with 1.2 of our version that doesn't affect the node-js one where
    # it wouldn't building tables, this attempts to simulate the problem Currenlty this
    # bug is patched now :)
    p = LLParse("lltable")
    start = p.node("start")
    loop = p.node("loop")
    loop.skipTo(start)
    start.match(
        [
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            97,
            98,
            99,
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            118,
            119,
            120,
            121,
            122,
            65,
            66,
            67,
            68,
            69,
            70,
            71,
            72,
            73,
            74,
            75,
            76,
            77,
            78,
            79,
            80,
            81,
            82,
            83,
            84,
            85,
            86,
            87,
            88,
            89,
            90,
            33,
            34,
            35,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            91,
            92,
            93,
            94,
            95,
            96,
            123,
            124,
            125,
            126,
            32,
            9,
            10,
            13,
            11,
            12,
        ],
        loop,
    ).otherwise(p.error(0, "im a little teapot"))

    # If there is not a lookup_table this then it has failed me ;-;
    assert "lookup_table" in p.build(start).c


def test_pausing():
    # Ensure frotentend LoopChecker does not mark off against Pausing
    p = LLParse("lltest")
    s = p.node("start")
    s2 = p.node("start2")
    s.match("p", p.pause(1, "parser was asked to pause").otherwise(s2)).skipTo(s)
    s2.match("p", p.pause(2, "parser was asked to pause again").otherwise(s)).skipTo(s2)
    p.build(s)


def test_operators(op: str):
    test = LLParse("test")

    test.property("i16", "a")

    node = test.node("node_1")
    # WARNING: Don't try and do this normally need operator exposed for making fixtures a bit easier.
    node.match(
        "1",
        test.invoke(
            Operator(op, "a", 10), {1: node}, test.error(1, "a is not greater than 10")
        ),
    ).otherwise(test.error(2, "lol"))

    t = test.build(node)
    code = t.c.splitlines(keepends=False)
    assert f"  return state->a {op} 10;" in code
    if op == ">":
        assert "int test__c_gt_a_10 (" in code
    elif op == "<":
        assert "int test__c_lt_a_10 (" in code
    elif op == ">=":
        assert "int test__c_ge_a_10 (" in code
    elif op == "<=":
        assert "int test__c_le_a_10 (" in code
