from dataclasses import dataclass

from llparse_frontend.namespace import frontend

from .. import compilation  # prevent looped imports
from ..constants import SEQUENCE_COMPLETE, SEQUENCE_MISMATCH, SEQUENCE_PAUSE
from ..transform import Transform


@dataclass(slots=True)
class MatchSequence:
    transform: Transform[frontend.transform.Transform]

    @staticmethod
    def build_globals(out: list[str]) -> None:
        out.append("enum llparse_match_status_e {")
        out.append(f"  {SEQUENCE_COMPLETE},")
        out.append(f"  {SEQUENCE_PAUSE},")
        out.append(f"  {SEQUENCE_MISMATCH}")
        out.append("};")
        out.append("typedef enum llparse_match_status_e llparse_match_status_t;")
        out.append("")
        out.append("struct llparse_match_s {")
        out.append("  llparse_match_status_t status;")
        out.append("  const unsigned char* current;")
        out.append("};")
        out.append("typedef struct llparse_match_s llparse_match_t;")

    def get_name(self) -> str:
        return f"llparse__match_sequence_{self.transform.ref.name}"

    def build(self, ctx: "compilation.Compilation", out: list[str]):
        out.append(f"static llparse_match_t {self.get_name()}(")
        out.append(f"    {ctx.prefix}_t* s, const unsigned char* p,")
        out.append("    const unsigned char* endp,")
        out.append("    const unsigned char* seq, uint32_t seq_len) {")

        # Vars
        out.append("  uint32_t index;")
        out.append("  llparse_match_t res;")
        out.append("")

        out.append("  index = s->_index;")
        out.append("  for (; p != endp; p++) {")
        out.append("    unsigned char current;")
        out.append("")

        out.append(f"    current = {self.transform.build(ctx, '*p')};")
        out.append("    if (current == seq[index]) {")
        out.append("      if (++index == seq_len) {")
        out.append(f"        res.status = {SEQUENCE_COMPLETE};")
        out.append("        goto reset;")
        out.append("      }")
        out.append("    } else {")
        out.append(f"      res.status = {SEQUENCE_MISMATCH};")
        out.append("      goto reset;")
        out.append("    }")
        out.append("  }")

        out.append("  s->_index = index;")
        out.append(f"  res.status = {SEQUENCE_PAUSE};")
        out.append("  res.current = p;")
        out.append("  return res;")

        out.append("reset:")
        out.append("  s->_index = 0;")
        out.append("  res.current = p;")
        out.append("  return res;")
        out.append("}")
