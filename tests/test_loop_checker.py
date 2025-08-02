from llparse.pybuilder import LoopChecker, Builder
from llparse.errors import Error
import pytest

# based off llparse-builder/test/loop-checker.test.ts
# Time Taken: 7 hours if you count the hard amounts of debugging, I went through.


@pytest.fixture()
def loop_checker() -> tuple[LoopChecker, Builder]:
    return LoopChecker(), Builder()


def test_detect_shallow_loops(loop_checker: tuple[LoopChecker, Builder]) -> None:
    lc, b = loop_checker
    start = b.node("start")
    start.otherwise(start)
    with pytest.raises(Error, match=r'Detected loop in "start" through "start"'):
        lc.check(start)


def test_detect_loops(loop_checker: tuple[LoopChecker, Builder]) -> None:
    lc, b = loop_checker
    start = b.node("start")
    a = b.node("a")
    invoke = b.invoke(
        b.code.match("nop"),
        {
            0: start,
        },
        b.error(1, "error"),
    )

    start.peek("a", a).otherwise(b.error(1, "error"))

    a.otherwise(invoke)
    with pytest.raises(Error, match=r'Detected loop in "a".*"a" -> "invoke_nop"'):
        lc.check(start)


def test_detect_shallow_loops_2(loop_checker: tuple[LoopChecker, Builder]) -> None:
    lc, b = loop_checker
    start = b.node("start")
    loop = b.node("loop")

    start.peek("a", loop).otherwise(b.error(1, "error"))
    loop.match("a", loop).otherwise(loop)
    with pytest.raises(Error, match=r'Detected loop in "loop" through "loop"'):
        lc.check(loop)


def test_ignore_loops_through_peek_to_match(
    loop_checker: tuple[LoopChecker, Builder],
) -> None:
    lc, b = loop_checker
    start = b.node("start")
    a = b.node("a")
    invoke = b.invoke(
        b.code.match("nop"),
        {
            0: start,
        },
        b.error(1, "error"),
    )

    start.peek("a", a).otherwise(b.error(1, "error"))

    a.match("abc", invoke).otherwise(start)
    lc.check(start)


def test_ignore_irrelevant_peeks(loop_checker: tuple[LoopChecker, Builder]) -> None:
    lc, b = loop_checker
    start = b.node("start")
    a = b.node("a")

    start.peek("a", a).otherwise(b.error(1, "error"))

    a.peek("b", start).otherwise(b.error(1, "error"))
    lc.check(start)


def test_ignore_loops_with_multi_peek_match(
    loop_checker: tuple[LoopChecker, Builder],
) -> None:
    lc, b = loop_checker
    start = b.node("start")
    another = b.node("another")

    NUM: list[str] = [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
    ]

    ALPHA: list[str] = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
    ]
    start.match(ALPHA, start).peek(NUM, another).skipTo(start)

    another.match(NUM, another).otherwise(start)
    lc.check(start)
