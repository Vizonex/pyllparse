from .error import ErrorNode


class Pause(ErrorNode):
    def do_build(self, out: list[str]) -> None:
        out.append(self.format(""))
