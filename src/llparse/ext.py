from collections.abc import Generator
from contextlib import contextmanager
from io import StringIO


# Modified from Cython's version with a much smoother system to utilize.
class LinesResult:
    __slots__ = ("io",)

    def __init__(self, io: StringIO | None = None):
        self.io = io or StringIO()

    def put(self, s: str) -> None:
        self.io.write(s)

    def newline(self) -> None:
        self.io.write("\n")

    def putline(self, s: str) -> None:
        self.io.write(s)
        self.io.write("\n")

    def __str__(self):
        return self.io.getvalue()


# Based off Cython's CodeWriter module in the DeclarationWriter class
class Writer:
    """A Simplistic Code Writer tool for outputting
    and writing clean code. It also allows users to cutomize
    how big the indent size of the output should be."""

    __slots__ = ("_indent_size", "_indent_str", "_numindents", "_result")

    def __init__(self, indent_size: int = 2, result: LinesResult | None = None):
        if indent_size < 1:
            raise ValueError("Indent size requires a number at least greater than 1.")
        self._indent_size = indent_size
        self._result = result if result is not None else LinesResult()
        self._numindents = 0
        self._indent_str = " " * indent_size

    def indent(self) -> None:
        self._numindents += 1

    def dedent(self) -> None:
        if self._numindents < 0:
            raise RuntimeError("number of indents is out of bounds.")
        self._numindents -= 1

    def startline(self, s: str = "") -> None:
        self._result.put(self._indent_str * self._numindents + s)

    def put(self, s: str) -> None:
        self._result.put(s)

    def putline(self, s: str) -> None:
        self._result.putline(self._indent_str * self._numindents + s)

    def putline_indented(self, s: str) -> None:
        with self.tab():
            self.putline(s)

    def endline(self, s: str = "") -> None:
        self._result.putline(s)

    def line(self, s: str) -> None:
        self.startline(s)
        self.endline()

    @contextmanager
    def tab(self) -> Generator[None, None, None]:
        """Indents and later dedents the number of indents
        used on each given line as a context manager."""
        self.indent()
        yield
        self.dedent()

    def skipline(self) -> None:
        self.endline()

    def skiplines(self, amount: int = 2):
        if amount < 1:
            raise RuntimeError("skiplines amount must be greater or equal to 1")
        for _ in range(amount):
            self.skipline()

    def result(self) -> str:
        """Obtains the written data from the writer"""
        return self._result.io.getvalue()
