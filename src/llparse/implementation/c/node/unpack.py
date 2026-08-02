from llparse_frontend import node as frontend

from .base import Node


class Unpack(Node[frontend.Unpack]):
    @property
    def offset(self) -> int:
        return self.ref.byte_offset

    @property
    def pair(self):
        return self.compilation, self.compilation.state_field(self.ref.field)

    def read_int8(self, out: list[str]) -> None:
        ctx, index = self.pair
        out.append(f"{index} = ((*{ctx.pos_arg()}) & 0x80);")

    def read_uint8(self, out: list[str]) -> None:
        ctx, index = self.pair
        out.append(f"{index} = (*{ctx.pos_arg()});")

    # LITTLE ENDIAN

    def read_int16LE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        else:
            # Since BE Belongs to performing << aka left shifts we do >> right shifts
            out.append(f"{index} = ({index} >> 8) | ((*{ctx.pos_arg()}) & 0x80);")

    def read_uint16LE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        else:
            out.append(f"{index} = ({index} >> 8) | (*{ctx.pos_arg()});")

    def read_int24LE(self, out: list[str]) -> None:
        ctx, index = self.pair
        match self.offset:
            case 0:
                out.append(f"{index} = (*{ctx.pos_arg()});")
            case 1:
                out.append(f"{index} = ({index} >> 8) | (*{ctx.pos_arg()});")
            case _:
                out.append(f"{index} = ({index} >> 8) | ((*{ctx.pos_arg()}) & 0x80);")

    def read_uint24LE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        else:
            out.append(f"{index} = ({index} >> 8) | (*{ctx.pos_arg()});")

    def read_int32LE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        elif self.offset in (1, 2):
            out.append(f"{index} = ({index} >> 8) | (*{ctx.pos_arg()});")
        else:
            out.append(f"{index} = ({index} >> 8) | ((*{ctx.pos_arg()}) & 0x80);")

    def read_uint32LE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        else:
            out.append(f"{index} = ({index} >> 8) | (*{ctx.pos_arg()});")

    # BIG ENDIAN

    def read_int16BE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        else:
            # Since LE Belongs to >> we do "<<" instead
            out.append(f"{index} = ({index} << 8) | ((*{ctx.pos_arg()}) & 0x80);")

    def read_uint16BE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        else:
            out.append(f"{index} = ({index} << 8) | (*{ctx.pos_arg()});")

    def read_int24BE(self, out: list[str]) -> None:
        ctx, index = self.pair
        match self.offset:
            case 0:
                out.append(f"{index} = (*{ctx.pos_arg()});")
            case 1:
                out.append(f"{index} = ({index} << 8) | (*{ctx.pos_arg()});")
            case _:
                out.append(f"{index} = ({index} << 8) | ((*{ctx.pos_arg()}) & 0x80);")

    def read_uint24BE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        else:
            out.append(f"{index} = ({index} << 8) | (*{ctx.pos_arg()});")

    def read_int32BE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        elif self.offset in (1, 2):
            out.append(f"{index} = ({index} << 8) | (*{ctx.pos_arg()});")
        else:
            out.append(f"{index} = ({index} << 8) | ((*{ctx.pos_arg()}) & 0x80);")

    def read_uint32BE(self, out: list[str]) -> None:
        ctx, index = self.pair
        if self.offset == 0:
            out.append(f"{index} = (*{ctx.pos_arg()});")
        else:
            out.append(f"{index} = ({index} << 8) | (*{ctx.pos_arg()});")

    def do_build(self, out: list[str]):
        self.prologue(out)

        if self.compilation.getFieldType(self.ref.field) == "ptr":
            raise ValueError(
                f'property {self.ref.field} should not use pointers but it was given "ptr"'
            )
        match self.ref.bits:
            case 1:
                self.read_int8(out) if self.ref.signed else self.read_uint8(out)
            case 2:
                if self.ref.little_endian:
                    self.read_int16LE(out) if self.ref.signed else self.read_uint16LE(
                        out
                    )
                else:
                    self.read_int16BE(out) if self.ref.signed else self.read_uint16BE(
                        out
                    )
            case 3:
                if self.ref.little_endian:
                    self.read_int24LE(out) if self.ref.signed else self.read_uint24LE(
                        out
                    )
                else:
                    self.read_int24BE(out) if self.ref.signed else self.read_uint24BE(
                        out
                    )
            case _:
                if self.ref.little_endian:
                    self.read_int32LE(out) if self.ref.signed else self.read_uint32LE(
                        out
                    )
                else:
                    self.read_int32BE(out) if self.ref.signed else self.read_uint32BE(
                        out
                    )

        self.tail_to(out, self.ref.otherwise.node, self.ref.otherwise.noAdvance, None)
