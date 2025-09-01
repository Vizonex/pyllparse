from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from .constants import *
from .frontend import IWrap, WrappedNode, _frontend

# NOTE Unfortunately You cant Just import from different files as that would trigger a Circular import
# So this file a little bit bigger than what I hoped for but was my only solution - Vizonex


@dataclass
class Transform(ABC):
    ref: _frontend.transform.Transform

    @abstractmethod
    def build(self, ctx: "Compilation", value: str) -> None: ...


@dataclass
class ID(Transform):
    def build(self, ctx: "Compilation", value: str):
        return value


@dataclass
class ToLowerUnsafe(Transform):
    def build(self, ctx: "Compilation", value: str):
        return f"(({value})| 0x20)"


@dataclass
class ToLower(Transform):
    def build(self, ctx: "Compilation", value: str):
        return f"(({value}) >= 'A' && ({value}) <= 'Z' ? ({value} | 0x20) : ({value}))"


@dataclass
class MatchSequence:
    transform: Transform

    @staticmethod
    def buildGlobals(out: list[str]):
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

    def getName(self):
        return f"llparse_match_sequence_{self.transform.ref.name}"

    def build(self, ctx: "Compilation", out: list[str]):
        out.append(f"static llparse_match_t {self.getName()}(")
        out.append(f"    {ctx.prefix}_t* s, const unsigned char* p,")
        out.append("    const unsigned char* endp,")
        out.append("    const unsigned char* seq, uint32_t seq_len) {")

        # Vars
        out.append("  uint32_t index;")
        out.append("  llparse_match_t res;")
        out.append("")

        out.append("  index = s->_index;")
        out.append("  for (;p != endp; p++) {")
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
        out.append("       goto reset;")
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
        out.append("};")


T = TypeVar("T", _frontend.code.Code, _frontend.code.Field)


class Code(Generic[T]):
    def __init__(self, ref: T):
        self.ref = ref

    def build(self, ctx: "Compilation", out: list[str]):
        pass

    def __hash__(self):
        return hash(self.ref)


class External(Code[_frontend.code.External]):
    def build(self, ctx: "Compilation", out: list[str]):
        out.append(f"int {self.ref.name} (")
        out.append(f"    {ctx.prefix}_t* s, const unsigned char* p,")
        if self.ref.signature == "value":
            out.append("    const unsigned char* endp,")
            out.append("    int value);")
        else:
            out.append("    const unsigned char* endp);")


class Field(Code):
    def __init__(self, ref: _frontend.code.Field):
        self.ref = ref

    def build(self, ctx: "Compilation", out: list[str]):
        out.append(f"int {self.ref.name} (")
        out.append(f"  {ctx.prefix}_t* {ctx.stateArg()},")
        out.append(f"  const unsigned char* {ctx.posArg()},")
        if self.ref.signature == "value":
            out.append(f"    const unsigned char* {ctx.endPosArg()},")
            out.append(f"    int {ctx.matchVar()}) " + "{")
        else:
            out.append(f"    const unsigned char* {ctx.endPosArg()}) " + "{")

        tmp: list[str] = []

        self.doBuild(ctx, tmp)
        ctx.indent(out, tmp, "  ")
        out.append("}")

    def doBuild(self, ctx: "Compilation", out: list[str]):
        return

    def field(self, ctx: "Compilation"):
        return f"{ctx.stateArg()}->{self.ref.field}"


class And(Field):
    def __init__(self, ref: _frontend.code.And):
        self.ref = ref

    def doBuild(self, ctx: "Compilation", out: list[str]):
        out.append(f"{self.field(ctx)} &= {self.ref.value}")


class IsEqual(Field):
    def __init__(self, ref: _frontend.code.IsEqual):
        self.ref = ref

    def doBuild(self, ctx: "Compilation", out: list[str]):
        out.append(f"return {self.field(ctx)} == {self.ref.value};")


class Load(Field):
    def __init__(self, ref: _frontend.code.Load):
        super().__init__(ref)

    def doBuild(self, ctx: "Compilation", out: list[str]):
        out.append(f"return {self.field(ctx)};")


# BIG ONE


class MulAdd(Field):
    def __init__(self, ref: _frontend.code.MulAdd):
        self.ref = ref

    def doBuild(self, ctx: "Compilation", out: list[str]):
        options = self.ref.options
        ty = ctx.getFieldType(self.ref.field)

        field = self.field(ctx)

        if options.signed:
            if not SIGNED_TYPES.get(ty):
                raise AssertionError(f'Unexpected mulAdd type "{ty}"')

            targetTy = SIGNED_TYPES[ty]
            out.append(f"{targetTy}* field = ({targetTy}*) &{field}")
            field = "(*field)"

        _match = ctx.matchVar()

        limits = SIGNED_LIMITS if options.signed else UNSIGNED_LIMITS

        if not limits.get(ty):
            raise AssertionError(f'Unexpected mulAdd type "{ty}"')

        _min, _max = limits[ty]

        mulMax = f"{_max} / {options.base}"
        mulMin = f"{_min} / {options.base}"

        out.append("/* Multiplication overflow */")
        out.append(f"if ({field} > {mulMax}) " + "{")
        out.append("  return 1;")
        out.append("}")

        if options.signed:
            out.append(f"if ({field} < {mulMin}) " + "{")
            out.append("  return 1;")
            out.append("}")

        out.append("")

        out.append(f"{field} *= {options.base};")
        out.append("")

        out.append("/* Addition overflow */")
        out.append(f"if ({_match} >= 0) " + "{")
        out.append(f"  if ({field} > {_max} - {_match})")
        out.append("    return 1;")
        out.append("  }")
        # out.append('}')

        out.append(f"{field} += {_match};")

        if options.max:
            out.append("")
            out.append("/* Enforce maximum */")
            out.append(f"if ({field} > {options.max}) " + "{")
            out.append("  return 1;")
            out.append("}")

        out.append("return 0;")


class Or(Field):
    def __init__(self, ref: _frontend.code.Or):
        self.ref = ref

    def doBuild(self, ctx: "Compilation", out: list[str]):
        out.append(f"{self.field(ctx)} |= {self.ref.value};")
        out.append("return 0;")


class Store(Field):
    def __init__(self, ref: _frontend.code.Store):
        self.ref = ref

    def doBuild(self, ctx: "Compilation", out: list[str]):
        out.append(f"{self.field(ctx)} = {ctx.matchVar()};")
        out.append("return 0;")


class Test(Field):
    def __init__(self, ref: _frontend.code.Test):
        self.ref = ref

    def doBuild(self, ctx: "Compilation", out: list[str]):
        value = self.ref.value
        out.append(f"return ({self.field(ctx)} & {value}) == {value};")


class Update(Field):
    def __init__(self, ref: _frontend.code.Update):
        self.ref = ref

    def doBuild(self, ctx: "Compilation", out: list[str]):
        out.append(f"{self.field(ctx)} = {self.ref.value};")
        out.append("return 0;")


@dataclass
class INodeEdge:
    node: IWrap[_frontend.node.Node]
    noAdvance: bool
    value: Optional[int] = None


class Node:
    def __init__(self, ref: _frontend.node.Node) -> None:
        self.ref = ref
        self.cachedDecel: Optional[str] = None
        self.privCompilation: Optional["Compilation"] = None

    def build(self, compilation: "Compilation"):
        if self.cachedDecel:
            return self.cachedDecel

        res = STATE_PREFIX + self.ref.id.name
        # cached Decel Prevents Recursion errors....
        self.cachedDecel = res
        self.privCompilation = compilation

        out: list[str] = []
        # if "update_key" in res:
        #     print(res)
        #     print([*self.ref.Slots])
        compilation.debug(
            out,
            f'Entering node \\"{self.ref.id.originalName}\\" (\\"{self.ref.id.name}\\")',
        )

        self.doBuild(out)

        compilation.addState(res, out)

        return res

    @property
    def compilation(self):
        assert self.privCompilation
        return self.privCompilation

    def prologue(self, out: list[str]):
        ctx = self.compilation

        out.append(f"if ({ctx.posArg()} == {ctx.endPosArg()}) " + "{")

        tmp: list[str] = []
        self.pause(tmp)

        self.compilation.indent(out, tmp, "  ")
        out.append("}")

    def pause(self, out: list[str]):
        out.append(f"return {self.cachedDecel};")

    # The problem with the INode Implementation is that It is creating newer and newer values
    # that cannot be matched so Writing out all the arguments was a must to prevent a deadly recursion
    def tailTo(
        self,
        out: list[str],
        node: IWrap[_frontend.node.Node],
        noAdvance: bool,
        value: Optional[int],
    ):
        ctx = self.compilation
        target = ctx.unwrapNode(node).build(ctx)

        # IF we have already built our target do not continue to build more of them!
        # if not isinstance(t,str):
        # target = t.build(ctx)
        # else:
        # Since we have the target already built let us not forget to use the name once more...
        # target = t
        if not target.startswith(STATE_PREFIX):
            target = STATE_PREFIX + target

        if not noAdvance:
            out.append(f"{ctx.posArg()}++;")

        if isinstance(value, int):
            out.append(f"{ctx.matchVar()} = {value};")

        out.append(f"goto {LABEL_PREFIX}{target};")

    def doBuild(self, out: list[str]):
        raise NotImplementedError


class Consume(Node):
    def __init__(self, ref: _frontend.node.Consume) -> None:
        self.ref = ref
        super().__init__(ref)

    def doBuild(self, out: list[str]):
        ctx = self.compilation

        index = ctx.stateField(self.ref.field)
        ty = ctx.getFieldType(self.ref.field)

        if ty == "i64":
            pass
        elif ty == "i32":
            pass
        elif ty == "i16":
            pass
        elif ty == "i8":
            pass
        else:
            raise Exception(
                f"Unsupported type {ty} of field {self.ref.field} for consume node"
            )

        out.append("size_t avail;")
        out.append("size_t need;")
        out.append("")
        out.append(f"avail = {ctx.endPosArg()} - {ctx.posArg()};")
        out.append(f"need = {index};")
        out.append("if (avail >= need) {")
        out.append("  p += need;")
        out.append(f"  {index} = 0;")
        tmp = []
        otherwise = self.ref.otherwise
        assert otherwise
        self.tailTo(tmp, otherwise.node, otherwise.noAdvance, otherwise.value)
        ctx.indent(out, tmp, "  ")
        out.append("}")
        out.append("")

        out.append(f"{index} -= avail;")
        self.pause(out)


class Empty(Node):
    def __init__(self, ref: _frontend.node.Empty) -> None:
        self.ref = ref
        super().__init__(ref)

    def doBuild(self, out: list[str]):
        assert self.ref.otherwise
        otherwise = self.ref.otherwise
        if not otherwise.noAdvance:
            self.prologue(out)
        self.tailTo(out, otherwise.node, otherwise.noAdvance, otherwise.value)


class Error(Node):
    def __init__(self, ref: _frontend.node.Error) -> None:
        self.ref = ref
        super().__init__(ref)

    def storeError(self, out: list[str]):
        ctx = self.compilation

        if self.ref.code < 0:
            hexCode = "-" + hex(self.ref.code)
        else:
            hexCode = hex(self.ref.code)

        out.append(f"{ctx.errorField()} = {hexCode};")
        out.append(f"{ctx.reasonField()} = {ctx.cstring(self.ref.reason)};")
        out.append(f"{ctx.errorPosField()} = (const char*) {ctx.posArg()};")

    def doBuild(self, out: list[str]):
        self.storeError(out)
        out.append(
            f"{self.compilation.currentField()} = (void*)(intptr_t) {STATE_ERROR};"
        )
        out.append(f"return {STATE_ERROR};")


class Invoke(Node):
    def __init__(self, ref: _frontend.node.Invoke) -> None:
        self.ref = ref
        super().__init__(ref)

    def fixBadCalls(self):
        ctx = self.compilation
        if isinstance(self.ref.code.ref, _frontend.code.Store):
            if not self.ref.code.ref.name.startswith(ctx.prefix + "__c_"):
                self.ref.code.ref.name = ctx.prefix + "__c_" + self.ref.code.ref.name

    def doBuild(self, out: list[str]):
        ctx = self.compilation
        self.fixBadCalls()

        code = ctx.unwrapCode(self.ref.code)

        # IF we don't have code it means it has already been registered and we need to cut off
        if not code:
            return None

        codeDecl = ctx.buildCode(code)

        args = [ctx.stateArg(), ctx.posArg(), ctx.endPosArg()]

        signature = code.ref.signature

        if signature == "value":
            args.append(ctx.matchVar())

        out.append(f"switch ({codeDecl}({', '.join(args)})) " + "{")
        tmp: str

        for edge in self.ref.edges():
            out.append(f"  case {edge.code}:")
            tmp = []
            self.tailTo(tmp, node=edge.node, noAdvance=True, value=None)
            ctx.indent(out, tmp, "    ")
        out.append("  default:")
        tmp = []
        self.tailTo(tmp, self.ref.otherwise.node, self.ref.otherwise.noAdvance, None)
        ctx.indent(out, tmp, "    ")
        out.append("}")


class Pause(Error):
    def __init__(self, ref: _frontend.node.Pause) -> None:
        self.ref = ref
        super().__init__(ref)

    def doBuild(self, out: list[str]):
        ctx = self.compilation
        self.storeError(out)

        assert self.ref.otherwise
        otherwise = ctx.unwrapNode(self.ref.otherwise.node)
        out.append(f"{ctx.currentField()} = (void*) (intptr_t) {otherwise};")
        out.append(f"return {STATE_ERROR};")


class Sequence(Node):
    def __init__(self, ref: _frontend.node.Sequence) -> None:
        self.ref = ref
        super().__init__(ref)

    def doBuild(self, out: list[str]):
        ctx = self.compilation

        out.append("llparse_match_t match_seq;")
        out.append("")

        self.prologue(out)

        matchSequence = ctx.getMatchSequence(self.ref.transform)

        out.append(
            f"match_seq = {matchSequence}({ctx.stateArg()}, "
            + f"{ctx.posArg()},"
            + f"{ctx.endPosArg()}, {ctx.blob(self.ref.select.decode('utf-8')) if isinstance(self.ref.select, str) else ctx.blob(self.ref.select)}, "
            + f"{len(self.ref.select)});"
        )
        out.append("p = match_seq.current;")

        out.append("switch (match_seq.status) {")
        out.append(f"  case {SEQUENCE_COMPLETE}: " + "{")
        tmp = []
        self.tailTo(
            tmp, noAdvance=False, node=self.ref.Edge.node, value=self.ref.Edge.value
        )

        ctx.indent(out, tmp, "    ")
        out.append(" }")

        out.append(f"  case {SEQUENCE_PAUSE}: " + "{")
        tmp = []
        self.pause(tmp)
        ctx.indent(out, tmp, "    ")
        out.append("  }")
        out.append(f"  case {SEQUENCE_MISMATCH}: " + "{")
        tmp = []
        self.tailTo(tmp, **self.ref.otherwise.__dict__)
        ctx.indent(out, tmp, "    ")
        out.append("  }")
        out.append("}")


class Single(Node):
    def __init__(self, ref: _frontend.node.Single) -> None:
        self.ref = ref
        super().__init__(ref)

    def doBuild(self, out: list[str]):
        ctx = self.compilation
        otherwise = self.ref.otherwise
        assert otherwise

        self.prologue(out)
        transform = ctx.unwrapTransform(self.ref.transform)
        current = transform.build(ctx, f"*{ctx.posArg()}")
        out.append(f"switch ({current})" + "{")

        for e in self.ref.edges:
            if e.key < 0x20 or e.key > 0x7E or e.key == 0x27 or e.key == 0x5C:
                ch = e.key
            else:
                ch = f"'{chr(e.key)}'"

            out.append(f"  case {ch}: " + "{")
            tmp: list[str] = []

            # For now debug everything....

            self.tailTo(tmp, e.node, e.noAdvance, e.value)

            ctx.indent(out, tmp, "    ")
            out.append("  }")

        out.append("  default: {")

        tmp: list[str] = []
        self.tailTo(tmp, otherwise.node, otherwise.noAdvance, None)
        ctx.indent(out, tmp, "    ")
        out.append("  }")
        out.append("}")


class SpanStart(Node):
    def __init__(self, ref: _frontend.node.SpanStart) -> None:
        self.ref = ref

        self.cachedDecel: Optional[str] = None
        self.privCompilation: Optional["Compilation"] = None

    def doBuild(self, out: list[str]):
        self.prologue(out)

        ctx = self.compilation
        field = self.ref.field

        posField = ctx.spanPosField(field.index)
        out.append(f"{posField} = (void*) {ctx.posArg()};")

        if len(field.callbacks) > 1:
            cbField = ctx.spanCbField(field.index)
            callback = ctx.unwrapCode(self.ref.callback, True)
            out.append(f"{cbField} = {ctx.buildCode(callback)};")

        otherwise = self.ref.otherwise
        self.tailTo(out, otherwise.node, otherwise.noAdvance, otherwise.value)


class SpanEnd(Node):
    def __init__(self, ref: _frontend.node.SpanEnd) -> None:
        self.ref = ref
        super().__init__(ref)

    def doBuild(self, out: list[str]):
        out.append("const unsigned char* start;")
        out.append("int err;")
        out.append("")

        ctx = self.compilation
        field = self.ref.field
        posField = ctx.spanPosField(field.index)

        # Loast start position
        out.append(f"start = {posField};")

        # reset position
        out.append(f"{posField} = NULL;")

        # Invoke callback
        callback = ctx.buildCode(ctx.unwrapCode(self.ref.callback, True))

        out.append(f"err = {callback}({ctx.stateArg()}, start,{ctx.posArg()});")

        out.append("if (err != 0) {")
        tmp = []
        self.buildError(tmp, "err")
        ctx.indent(out, tmp, "  ")
        out.append("}")

        otherwise = self.ref.otherwise
        self.tailTo(out, otherwise.node, otherwise.noAdvance, None)

    def buildError(self, out: list[str], code: str):
        ctx = self.compilation

        out.append(f"{ctx.errorField()} = {code};")

        otherwise = self.ref.otherwise
        assert otherwise

        resumePos = ctx.posArg()

        if not otherwise.noAdvance:
            resumePos = f"({resumePos} +  1)"

        out.append(f"{ctx.errorPosField()} = (const char*) {resumePos};")

        rt = ctx.unwrapNode(otherwise.node)
        # check if the resumption target has already been built or not...
        resumptionTarget = rt.build(ctx)

        out.append(
            f"{ctx.currentField()} = "
            + f"(void*) (intptr_t) {STATE_PREFIX + resumptionTarget if not resumptionTarget.startswith(STATE_PREFIX) else resumptionTarget};"
        )
        out.append(f"return {STATE_ERROR};")


MAX_CHAR = 0xFF
TABLE_GROUP = 16

# _mm_cmpestri takes 8 ranges
SSE_RANGES_LEN = 16

# _mm_cmpestri takes 128bit input
SSE_RANGES_PAD = 16
MAX_SSE_CALLS = 2
SSE_ALIGNMENT = 16


@dataclass
class ITable:
    name: str
    declaration: list[str] = field(default_factory=list)


class TableLookup(Node):
    def __init__(self, ref: _frontend.node.TableLookup) -> None:
        self.ref = ref
        super().__init__(ref)

    def doBuild(self, out: list[str]):
        ctx = self.compilation

        table = self.buildTable()
        for line in table.declaration:
            out.append(line)

        self.prologue(out)

        transform = ctx.unwrapTransform(self.ref.transform)

        self.buildSSE(out)

        current = transform.build(ctx, f"*{ctx.posArg()}")

        out.append(f"switch ({table.name}[(uint8_t) {current}]) " + "{")
        tmp = []
        for index, edge in enumerate(self.ref.privEdges):
            out.append(f"  case {index + 1}: " + "{")
            edge = self.ref.privEdges[index]
            self.tailTo(tmp, noAdvance=edge.noAdvance, node=edge.node, value=None)
            ctx.indent(out, tmp, "    ")
            out.append("  }")
            tmp.clear()

        out.append("  default: {")
        self.tailTo(tmp, **self.ref.otherwise.__dict__)
        ctx.indent(out, tmp, "    ")
        out.append("  }")
        out.append("}")

    def buildSSE(self, out: list[str]):
        ctx = self.compilation

        if self.ref.transform and self.ref.transform.ref.name != "id":
            return False

        if len(self.ref.privEdges) != 1:
            return False

        edge = self.ref.privEdges[0]

        if edge.node.ref != self.ref:
            return False

        ranges: list[int] = []

        first: Optional[int] = None
        last: Optional[int] = None

        for key in edge.keys:
            if not first:
                first = key
            if not last:
                last = key

            if key - last > 1:
                ranges.extend([first, last])
                first = key
            last = key

        if first and last:
            ranges.extend([first, last])

        # Reduce Call load...
        if ranges > MAX_SSE_CALLS * SSE_RANGES_LEN:
            return False

        out.append("#ifdef __SSE4_2__")
        out.append(f"if ({ctx.endPosArg()}) - {ctx.posArg()} >= 16)" + "{")
        out.append("  __m128i ranges;")
        out.append("  __m128i input;")
        out.append("  int avail;")
        out.append("  int match_len;")
        out.append("")
        out.append("  /* Load input */")
        out.append(f"  input = _mm_loadu_si128((__m128i const*) {ctx.posArg()});")

        for off in range(0, len(ranges), SSE_RANGES_LEN):
            subRanges = ranges[off : off + SSE_RANGES_LEN]
            paddedRanges = subRanges[:]
            while len(paddedRanges) < SSE_RANGES_PAD:
                paddedRanges.append(0)

            blob = ctx.blob(bytes(paddedRanges), SSE_ALIGNMENT)

            out.append(f"  ranges = _mm_loadu_si128((__128i const*) {blob});")
            out.append("  /* Find first character that does not match 'ranges' */")
            out.append(f"  match_len = _mm_cmpestri(ranges, {len(subRanges)})")
            out.append("    input, 16,")
            out.append("    _SIDDUBYTE_OPS | _SIDD_CMP_RANGES |")
            out.append("      _SIDD_NEGATIVE_POLARITY);")
            out.append("")
            out.append("  if (match_len != 0) {")
            out.append(f"    {ctx.posArg()} += match_len;")

            tmp: list[str] = []
            assert not edge.noAdvance
            self.tailTo(tmp, edge.node, True, None)
            ctx.indent(out, tmp, "    ")
            out.append("  }")

        tmp: list[str] = []

        assert self.ref.otherwise
        self.tailTo(tmp, self.ref.otherwise)
        ctx.indent(out, tmp, "  ")
        out.append("}")
        out.append("#endif /* __SSE4_2__ */")

        return True

    def buildTable(self):
        table: list[int] = [0 for _ in range(MAX_CHAR + 1)]
        # assert self.ref.privEdges
        for index, edge in enumerate(self.ref.privEdges, 1):
            for key in edge.keys:
                assert table[key] == 0
                table[key] = index

        lines = ["static uint8_t lookup_table[] = {"]

        for i in range(0, len(table), TABLE_GROUP):
            # Turn all into string...
            ntable = ", ".join(map(lambda x: "%i" % x, table[i : i + TABLE_GROUP]))
            line = f"  {ntable}"
            if i + TABLE_GROUP < len(table):
                line += ","
            lines.append(line)

        lines.append("};")

        return ITable(name="lookup_table", declaration=lines)


BLOB_GROUP_SIZE = 11

from .pybuilder import Property


@dataclass
class ICompilerOptions:
    debug: Optional[str] = None
    header: Optional[str] = None


@dataclass
class IBlob:
    buffer: bytes
    name: str
    alignment: Optional[int] = None


class Compilation:
    def __init__(
        self,
        prefix: str,
        properites: list[Property],
        resumptionsTargets: list[WrappedNode],
        options: ICompilerOptions,
    ) -> None:
        self.prefix = prefix
        self.properties = properites
        self.options = options
        self.resumptionTargets: set[str] = set()

        # Containers are used to prevent recursions
        self.CodeContainer: dict[IWrap[_frontend.code.Code], Code] = {}
        self.NodeContainer: dict[IWrap[_frontend.node.Node], Node] = {}

        self.codeMap: dict[str, Code] = {}
        self.stateDict: dict[str, list[str]] = {}

        self.blobs: dict[bytes, IBlob] = {}

        self.matchSequence: dict[str, MatchSequence] = {}

        for node in resumptionsTargets:
            self.resumptionTargets.add(STATE_PREFIX + node.ref.id.name)

    def buildStateEnum(self, out: list[str]):
        # TODO (Vizonex) Give out other names that you could pass as an enum statename
        # this is incase multiple llparse_state_e states are given to compile
        # example would be mixing llhttp with some other source...
        out.append("enum llparse_state_e {")
        out.append(f"  {STATE_ERROR},")
        for stateName in self.stateDict.keys():
            # if stateName in self.resumptionTargets:
            # NOTE I think these are all resumption targets so this will do...
            out.append(f"  {stateName},")
        out.append("};")
        out.append("typedef enum llparse_state_e llparse_state_t;")

    def buildBlobs(self, out: list[str]):
        if len(self.blobs) == 0:
            return

        for blob in self.blobs.values():
            buffer = blob.buffer
            align = ""

            # NOTE in llparse there is a check of blob alignment twice
            # so to cut out some redundancy I'll join these two parts into one - Vizonex
            if blob.alignment:
                align = f" ALIGN({blob.alignment})"
                out.append("#ifdef __SSE4_2__")

            out.append(f"static const unsigned char {align} {blob.name}[] = " + "{")

            # large loop

            for i in range(0, len(buffer), BLOB_GROUP_SIZE):
                limit = min(len(buffer), i + BLOB_GROUP_SIZE)
                _hex: list[str] = []
                for j in range(i, limit):
                    value = buffer[j]

                    ch = chr(value)

                    if value in [0x27, 0x5C]:
                        _hex.append(f"'\\{ch}'")

                    elif value >= 0x20 and value <= 0x7E:
                        _hex.append(f"'{ch}'")

                    else:
                        _hex.append(f"{hex(value)}")

                line = " " + ", ".join(_hex)
                if limit != len(buffer):
                    line += ","

                out.append(line)

            out.append("};")

            if blob.alignment:
                out.append("#endif /* __SSE4_2__ */")

        out.append("")

    def buildMatchSequence(self, out: list[str]):
        if len(self.matchSequence) == 0:
            return
        MatchSequence.buildGlobals(out)

        for _match in self.matchSequence.values():
            _match.build(self, out)
            out.append("")

    def reserveSpans(self, spans: list[_frontend.node.SpanField]):
        for span in spans:
            for callback in span.callbacks:
                cb = self.unwrapCode(callback)
                if cb:
                    self.buildCode(cb)

    def debug(self, out: list[str], message: str):
        if not self.options.debug:
            return

        args = [
            self.stateArg(),
            f"(const char*) {self.posArg()}",
            f"(const char*) {self.endPosArg()}",
        ]

        out.append(f"{self.options.debug} ({', '.join(args)},")
        out.append(f"  {self.cstring(message)});")

    def buildGlobals(self, out: list[str]):
        if self.options.debug:
            out.append(f"void {self.options.debug}(")
            out.append(f"    {self.prefix}_t* s, const char* p, const char* endp,")
            out.append("    const char* msg);")

        self.buildBlobs(out)
        self.buildMatchSequence(out)
        self.buildStateEnum(out)

        fix_and_build(self, out)

    def buildResumptionStates(self, out: list[str]):
        for name, lines in self.stateDict.items():
            if name not in self.resumptionTargets:
                continue

            out.append(f"case {name}:")
            out.append(f"{LABEL_PREFIX}{name} : " + "{")
            for line in lines:
                out.append(f"  {line}")
            out.append("  UNREACHABLE;")
            out.append("}")

    def buildInternalStates(self, out: list[str]):
        for name, lines in self.stateDict.items():
            if name in self.resumptionTargets:
                continue

            out.append(f"{LABEL_PREFIX}{name}: " + "{")
            for line in lines:
                out.append(f"  {line}")
            out.append("  UNREACHABLE;")
            out.append("}")

    def addState(self, state: str, lines: list[str]):
        assert not self.stateDict.get(state)
        self.stateDict[state] = lines

    def buildCode(self, code: Code) -> str:
        if self.codeMap.get(code.ref.name):
            if self.codeMap[code.ref.name].__dict__ != code.__dict__:
                raise AssertionError(
                    f'Code name conflict for "{code.ref.name}"   {self.codeMap.get(code.ref.name).__dict__} != {code.__dict__}'
                )
            # return code.ref.name
        else:
            self.codeMap[code.ref.name] = code
        return code.ref.name

    def getFieldType(self, field: str):
        for property in self.properties:
            if property.name == field:
                return property.ty

        else:
            raise LookupError(f'Field "{field}" not found')

    # Helpers are different since in python we have duck typing - Vizonex
    def unwrapCode(
        self, code: IWrap[_frontend.code.Code], allow_continue: bool = False
    ):
        if self.CodeContainer.get(code):
            # Give some indication that the element has already been built...
            return self.CodeContainer[code]

        ref = code.ref

        # Check to see if we already have the element in the codemap first.
        # If we do, return that instead. This will prevent a recursion error...

        if isinstance(ref, _frontend.code.And):
            r = And(ref)
        elif isinstance(ref, _frontend.code.IsEqual):
            r = IsEqual(ref)
        elif isinstance(ref, _frontend.code.Load):
            r = Load(ref)
        elif isinstance(ref, _frontend.code.MulAdd):
            r = MulAdd(ref)
        elif isinstance(ref, _frontend.code.Or):
            r = Or(ref)
        elif isinstance(ref, _frontend.code.External):
            # TODO Fix Spans since Span Doesn't have an id with it...
            # UPDATE Maybe External could be the key to bypass this unethical error
            r = External(ref)
        elif isinstance(ref, _frontend.code.Store):
            r = Store(ref)
        elif isinstance(ref, _frontend.code.Test):
            r = Test(ref)
        elif isinstance(ref, _frontend.code.Update):
            r = Update(ref)
        else:
            raise Exception(
                f'refrence "{ref.name}" is an Invalid Code Type , TypeName:"{ref.__class__.__name__}"'
            )
        self.CodeContainer[code] = r

        return r

    def unwrapNode(self, node: IWrap[_frontend.node.Node]):
        if self.NodeContainer.get(node):
            return self.NodeContainer[node]

        ref = node.ref
        if isinstance(ref, _frontend.node.Consume):
            r = Consume(ref)
        elif isinstance(ref, _frontend.node.Empty):
            r = Empty(ref)
        elif isinstance(ref, _frontend.node.Error):
            r = Error(ref)
        elif isinstance(ref, _frontend.node.Invoke):
            r = Invoke(ref)
        elif isinstance(ref, _frontend.node.Pause):
            r = Pause(ref)

        elif isinstance(ref, _frontend.node.SpanStart):
            r = SpanStart(ref)

        elif isinstance(ref, _frontend.node.SpanEnd):
            r = SpanEnd(ref)

        elif isinstance(ref, _frontend.node.Single):
            r = Single(ref)
        elif isinstance(ref, _frontend.node.Sequence):
            r = Sequence(ref)
        elif isinstance(ref, _frontend.node.TableLookup):
            r = TableLookup(ref)
        else:
            raise TypeError(
                f'refrence "{ref}" is an Invalid Code Type , TypeName:"{ref.__class__.__name__}"'
            )

        self.NodeContainer[node] = r

        return r

    def unwrapTransform(self, node: IWrap[_frontend.transform.Transform]):
        ref = node.ref
        if isinstance(ref, _frontend.transform.ID):
            return ID(ref)
        elif isinstance(ref, _frontend.transform.ToLower):
            return ToLower(ref)
        elif isinstance(ref, _frontend.transform.ToLowerUnsafe):
            return ToLowerUnsafe(ref)

        raise TypeError(
            f'refrence "{ref.name}" is an Invalid Code Type , TypeName:"{ref.__class__.__name__}"'
        )

    def indent(self, out: list[str], lines: list[str], pad: str):
        for line in lines:
            out.append(f"{pad}{line}")

    def getMatchSequence(self, transform: IWrap[_frontend.transform.Transform]):
        wrap: Transform = self.unwrapTransform(transform)

        if self.matchSequence.get(wrap.ref.name):
            res = self.matchSequence[wrap.ref.name]
        else:
            res = MatchSequence(wrap)
            self.matchSequence[wrap.ref.name] = res
        return res.getName()

    def stateArg(self):
        return ARG_STATE

    def posArg(self):
        return ARG_POS

    def endPosArg(self):
        return ARG_ENDPOS

    def matchVar(self):
        return VAR_MATCH

    def indexField(self):
        return self.stateField("_index")

    def currentField(self):
        return self.stateField("_current")

    def errorField(self):
        return self.stateField("error")

    def reasonField(self):
        return self.stateField("reason")

    def errorPosField(self):
        return self.stateField("error_pos")

    def spanPosField(self, index: int):
        return self.stateField(f"_span_pos{index}")

    def spanCbField(self, index: int):
        return self.stateField(f"_span_cb{index}")

    def stateField(self, name: str):
        return f"{self.stateArg()}->{name}"

    # Globals

    def cstring(self, value: str):
        return f'"{value}"'

    def blob(self, value: bytes, alignment: Optional[int] = None):
        if self.blobs.get(value):
            return self.blobs[value].name

        res = BLOB_PREFIX + str(len(self.blobs))
        self.blobs[value] = IBlob(value, res, alignment)

        return res


def fix_and_build(ctx: Compilation, out: list[str]):
    """Helper function that ups with building globals out..."""
    for code in ctx.codeMap.values():
        out.append("")
        code.build(ctx, out)
