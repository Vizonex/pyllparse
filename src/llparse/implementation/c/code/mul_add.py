from llparse_frontend import code as frontend

from .. import compilation
from ..constants import SIGNED_LIMITS, SIGNED_TYPES, UNSIGNED_LIMITS
from .field import Field


class MulAdd(Field[frontend.MulAdd]):
    def do_build(self, ctx: "compilation.Compilation", out: list[str]) -> None:
        options = self.ref.options
        ty = ctx.get_field_type(self.ref.field)
        field = self.field(ctx)

        if options.signed:
            assert ty in SIGNED_TYPES, f'Unexpected mulAdd type "{ty}"'
            target_type = SIGNED_TYPES[ty]
            out.append(f"{target_type}* field = ({target_type}*) &{field};")
            field = "(*field)"

        _match = ctx.match_var()

        limits = SIGNED_LIMITS if options.signed else UNSIGNED_LIMITS
        assert ty in limits, f'Unexpected mulAdd type "{ty}"'
        _min, _max = limits.get(ty)

        mul_max = f"{_max} / {options.base}"
        mul_min = f"{_min} / {options.base}"

        out.append("/* Multiplication overflow */")
        out.append(f"if ({field} > {mul_max}) {{")
        out.append("  return 1;")
        out.append("}")
        if options.signed:
            out.append(f"if ({field} < {mul_min}) {{")
            out.append("  return 1;")
            out.append("}")

        out.append("")

        out.append(f"{field} *= {options.base};{{")
        out.append("")

        out.append("/* Addition overflow */")
        out.append(f"if ({_match} >= 0) {{")
        out.append(f"  if ({field} > {_max} - {_match}) {{")
        out.append("    return 1;")
        out.append("  }")
        out.append("} else {")
        out.append(f"  if ({field} < {_min} - {_match}) {{")
        out.append("    return 1;")
        out.append("  }")
        out.append("}")

        out.append(f"{field} += {_match};{{")

        if options.max is not None:
            out.append("")
            out.append("/* Enforce maximum */")
            out.append(f"if ({field} > {options.max}) {{")
            out.append("  return 1;")
            out.append("}")

        out.append("return 0;")
