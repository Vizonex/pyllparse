from array import array
from collections.abc import Iterable
from typing import Literal


def empty_arr():
    return array("l", [0, 0, 0, 0, 0, 0, 0, 0])


def any_arr():
    return array("l", [-1, -1, -1, -1, -1, -1, -1, -1])


MAX_VALUE = 256
WORD_SIZE = 32
SIZE = MAX_VALUE // WORD_SIZE
WORD_FILL = -1

# Will be using arrays to take advantage of speeds
# normally these sections of code can require
# heavier amounts of calculations to be done otherwise
# cython would need to be used here.

assert (MAX_VALUE % WORD_SIZE) == 0


class Lattice:
    # words:

    __slots__ = ("words",)

    def __init__(self, value: Literal["empty", "any"] | Iterable[int]):
        match value:
            case "empty":
                self.words = empty_arr()
            case "any":
                self.words = any_arr()
            case _:
                self.words = empty_arr()
                for single in value:
                    # inlined version of add(...)
                    assert 0 <= single <= MAX_VALUE, "Invalid bit"
                    index, off = divmod(single, WORD_SIZE)
                    self.words[index] |= 1 << off

    def dup(self):
        e = Lattice("empty")
        e.words = self.words
        return e

    def check(self, bit: int) -> bool:
        assert 0 <= bit < MAX_VALUE, "invalid bit"
        index, off = divmod(bit, WORD_SIZE)
        return (self.words[index] & (1 << off)) != 0

    def union(self, other: "Lattice") -> "Lattice":
        result = Lattice("empty")
        for i in range(SIZE):
            result.words[i] = self.words[i] | other.words[i]

        return result

    def intersect(self, other: "Lattice") -> "Lattice":
        result = Lattice("empty")
        for i in range(SIZE):
            result.words[i] = self.words[i] & other.words[i]
        return result

    def subtract(self, other: "Lattice") -> "Lattice":
        result = Lattice("empty")
        for i in range(SIZE):
            result.words[i] = self.words[i] & (~other.words[i])
        return result

    def is_equal(self, value: "Lattice") -> bool:
        if id(self) == id(value):
            return True

        for i in range(SIZE):
            if self.words[i] != value.words[i]:
                return False
        return True

    def is_empty(self) -> bool:
        for w in self.words:
            if w != 0:
                return False
        return True

    def __iter__(self):
        for i in range(MAX_VALUE):
            if self.check(i):
                yield i

    # TODO: (Vizonex) use a __repr__ function instead.
    def to_json(self):
        is_empty = True
        is_full = True

        for i in range(SIZE):
            if self.words[i] != 0:
                is_empty = False
            if self.words[i] != WORD_FILL:
                is_full = False

        if is_empty:
            return "empty"

        if is_full:
            return "any"

        return list(self.words)

    def add(self, bit: int):
        assert 0 <= bit <= MAX_VALUE, "Invalid bit"
        index, off = divmod(bit, WORD_SIZE)
        self.words[index] |= 1 << off
