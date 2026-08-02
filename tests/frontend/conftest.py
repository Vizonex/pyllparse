import pytest

from llparse_builder import Builder


@pytest.fixture
def b() -> Builder:
    return Builder()
