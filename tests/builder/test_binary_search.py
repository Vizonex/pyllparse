import pytest

from llparse_builder.binary_search import binary_search

arr = [1, 2, 2, 2, 3, 5, 9]


# based off test/binary-search.test.ts
def cmp(a: float, b: float, idx, seq) -> float:
    return a - b


def test_not_a_sequence():
    with pytest.raises(TypeError):
        binary_search(None, 3, cmp)


def test_invalid_input():
    with pytest.raises(TypeError):
        binary_search(arr, 3, None)


def test_returning_index_of_sorted_array():
    assert binary_search(arr, 3, cmp)


def test_index_of_item_plus_one_or_negate():
    assert binary_search(arr, 4, cmp) == -6


def test_index_if_item_exists_multiple_times():
    assert binary_search(arr, 2, cmp) == 3


def test_with_empty_arrays():
    assert binary_search([], 42, cmp) == -1


def test_arrays_of_floats():
    assert binary_search([0.0, 0.1, 0.2, 0.3, 0.4], 0.25, cmp) == -4


def test_index_and_array_comparator():
    indexes = []

    def index_cmp(a: int, b: int, i: int | None, array: list[int]):
        assert array == arr
        indexes.append(i)
        return cmp(a, b, None, None)

    binary_search(arr, 3, index_cmp)
    assert indexes == [3, 5, 4]
