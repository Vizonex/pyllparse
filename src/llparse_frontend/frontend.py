from dataclasses import dataclass, field
from logging import getLogger
from typing import TypedDict

from llparse_builder import builder as source

from . import enumerator, peephole
from .errors import Error
from .implementation import Implementation
from .namespace import frontend
from .node.single import ReadonlySingleEdge
from .span_field import SpanField
from .trie import Trie, TrieEmpty, TrieNode, TrieSequence, TrieSingle, TrieSingleChild
from .utils import Identifier
from .wrap import Wrap

logger = getLogger(__name__)
debug = logger.debug

DEFAULT_MIN_TABLE_SIZE = 32
DEFAULT_MAX_TABLE_WIDTH = 4


class FrontendLazyOptions(TypedDict, total=False):
    max_table_elem_width: int | None = None
    min_table_size: int | None = None


@dataclass(slots=True, frozen=True)
class FrontendResult:
    prefix: str
    properties: list[source.Property]
    root: Wrap[frontend.node.Node]
    spans: list[SpanField]
    resumption_targets: list[Wrap[frontend.node.Node]]


@dataclass(slots=True)
class TableLookupTarget:
    trie: TrieEmpty
    no_advance: bool
    keys: list[int] = field(default_factory=list)


class Frontend:
    __slots__ = (
        "code_cache",
        "code_id",
        "id",
        "implementation",
        "map",
        "options",
        "prefix",
        "resumption_targets",
        "span_map",
    )

    def __init__(
        self,
        prefix: str,
        implementation: Implementation,
        max_table_elem_width: int | None = None,
        min_table_size: int | None = None,
    ) -> None:
        self.prefix = prefix
        self.id = Identifier(f"{prefix}__n_")
        self.code_id = Identifier(f"{prefix}__c_")
        self.implementation = implementation
        self.resumption_targets = set()
        self.code_cache = {}
        self.span_map = {}
        self.map = {}

        self.options: FrontendLazyOptions = {
            "max_table_elem_width": max_table_elem_width or DEFAULT_MAX_TABLE_WIDTH,
            "min_table_size": min_table_size or DEFAULT_MIN_TABLE_SIZE,
        }
        assert self.options["max_table_elem_width"] > 0, (
            "Invalid `max_table_elem_width`, must be positive"
        )

    def compile(
        self, root: source.node.Node, properties: list[source.Property]
    ) -> FrontendResult:
        debug("checking loops")
        lc = source.LoopChecker()
        lc.check(root)

        debug("allocating spans")
        span_allocator = source.SpanAllocator()
        source_spans = span_allocator.allocate(root)

        spans: list[SpanField] = []
        for index, concurrent in enumerate(source_spans.concurrency):
            span = SpanField(
                index, [self.translate_code(c.callback) for c in concurrent]
            )

            for sourceSpan in concurrent:
                self.span_map[sourceSpan] = span

            spans.append(span)

        debug("translating")
        out = self.translate(root)

        # Enumerate
        debug("enumerating")
        nodes = enumerator.get_all_nodes(out)
        # Peephole optimizations...
        debug("peephole optimization")
        out = peephole.optimize(out, nodes)

        # Re-Enumerate
        debug("re-enumerating")
        nodes = enumerator.get_all_nodes(out)

        debug("registering resumption targets")

        # DONT FORGET TO ADD "OUT" TO THE RESUMPTION TARGETS!!!
        self.resumption_targets.add(out)

        # Register resumption targets...
        for node in nodes:
            self.register_node(node)

        return FrontendResult(
            prefix=self.prefix,
            properties=properties,
            resumption_targets=self.resumption_targets,
            root=out,
            spans=spans,
        )

    def register_node(self, node: Wrap[frontend.node.Node]) -> None:
        if isinstance(
            node.ref,
            (
                frontend.node.Unpack,
                frontend.node.Consume,
                frontend.node.Empty,
                frontend.node.Sequence,
                frontend.node.Single,
                frontend.node.TableLookup,
                frontend.node.SpanStart,
            ),
        ):
            self.resumption_targets.add(node)
        elif isinstance(node.ref, (frontend.node.Pause, frontend.node.SpanEnd)):
            self.resumption_targets.add(node.ref.otherwise.node)

    def translate_match(
        self, node: source.node.Match
    ) -> list[Wrap[frontend.node.Node]]:
        trie = Trie(node.name)
        assert node.get_otherwise_edge()
        trieNode = trie.build(list(node))

        if not trieNode:
            return self.implementation.node.Empty(
                frontend.node.Empty(self.id.id(node.name))
            )

        children: list = []

        self.translate_trie(node, trieNode, children)
        assert children

        return children

    def translate(self, node: source.node.Node) -> Wrap[frontend.node.Node]:
        if node in self.map:
            return self.map[node]

        def id():
            return self.id.id(node.name)

        node_impl = self.implementation.node

        result = None
        if isinstance(node, source.node.Error):
            result = node_impl.Error(frontend.node.Error(id(), node.code, node.reason))

        elif isinstance(node, source.node.Pause):
            result = node_impl.Pause(frontend.node.Pause(id(), node.code, node.reason))

        elif isinstance(node, source.node.Consume):
            result = node_impl.Consume(frontend.node.Consume(id(), node.field))

        elif isinstance(node, source.node.SpanStart):
            result = node_impl.SpanStart(
                frontend.node.SpanStart(
                    id(),
                    self.span_map[node.span],
                    self.translate_span_code(node.span.callback),
                )
            )

        elif isinstance(node, source.node.SpanEnd):
            result = node_impl.SpanEnd(
                frontend.node.SpanEnd(
                    id(),
                    self.span_map[node.span],
                    self.translate_span_code(node.span.callback),
                )
            )

        elif isinstance(node, source.node.Invoke):
            assert node.code.signature in ["match", "value"], (
                "Passing `span` callback to `invoke` is not allowed"
            )
            result = node_impl.Invoke(
                frontend.node.Invoke(id(), self.translate_code(node.code))
            )

        elif isinstance(node, source.node.Match):
            result = self.translate_match(node)

        elif isinstance(node, source.node.Unpack):
            result = self.translate_unpack(node)

        else:
            raise Error(f'Unknown Node Type for :"{node.name}" {type(node)}')

        otherwise = node.get_otherwise_edge()

        if isinstance(result, list):
            # result:list[WrappedNode]

            assert isinstance(node, (source.node.Match, source.node.Unpack))
            _match = node

            assert otherwise, f'Node "{node.name}" has no ".otherwise()"'

            if isinstance(node, source.node.Match):
                for child in result:
                    if not child.ref.otherwise:
                        child.ref.set_otherwise(
                            self.translate(otherwise.node), otherwise.no_advance
                        )
                transform = self.translate_transform(_match.get_transform())
                for child in result:
                    # TODO Vizonex : This might break , be sure to make a workaround function here...
                    child.ref.set_transform(transform)

            else:
                result[-1].ref.set_otherwise(
                    self.translate(otherwise.node), otherwise.no_advance
                )
            assert len(result) >= 1
            return result[0]

        else:
            single = result

            assert isinstance(single.ref, frontend.node.Node)

            self.map[node] = single

            if otherwise is not None:
                single.ref.set_otherwise(
                    self.translate(otherwise.node), otherwise.no_advance
                )

            else:
                assert isinstance(node, source.node.Error), (
                    f'Node "{node.name}" has no `.otherwise()'
                )

            if isinstance(single.ref, frontend.node.Invoke):
                for edge in node:
                    single.ref.add_edge(
                        ord(edge.key) if isinstance(edge.key, str) else edge.key,
                        self.translate(edge.node),
                    )
            else:
                assert node

            return single

    def translate_unpack(
        self, node: source.node.Unpack
    ) -> list[Wrap[frontend.node.Unpack]]:
        inner = frontend.node.Unpack(
            self.Id.id(node.name),
            node.field,
            node.bits,
            node.signed,
            node.little_endian,
            0,
        )
        result = [self.implementation.node.Unpack(inner)]
        # front is to avoid overlapping with python's functions (aka next)
        front = self.map[node] = result[0]

        for offset in range(1, node.bits):
            unique_name = self.id.id(f"{node.name}_byte{offset + 1}")
            inner = frontend.node.Unpack(
                unique_name,
                node.field,
                node.bits,
                node.signed,
                node.little_endian,
                offset,
            )
            outer = self.implementation.node.Unpack(inner)
            result.append(outer)
            # unpack will advance since we are unpacking values...
            front.ref.set_otherwise(outer, False)
            front = result[-1]
        return result

    def maybe_table_lookup(
        self,
        node: source.code.Match,
        trie: TrieSingle,
        children: list[Wrap[frontend.node.Node]],
    ):
        if len(trie.children) < self.options["min_table_size"]:
            return None

        targets: dict[source.code.Node, TableLookupTarget] = {}

        def check_child(child: TrieSingleChild):
            nonlocal targets
            if not isinstance(child.node, TrieEmpty):
                debug(f'non-leaf trie child of "{node.name}" prevents table allocation')
                return False
            empty = child.node
            if empty.value is not None:
                debug(
                    f'value passing trie leaf of "{node.name}" prevents table allocation'
                )
                return False

            target = empty.node
            if target not in targets:
                targets[target] = TableLookupTarget(
                    keys=[child.key], no_advance=child.no_advance, trie=empty
                )
                return True

            existing = targets[target]
            if existing.no_advance != child.no_advance:
                debug(
                    f'no_advance mismatch in a trie leaf of "{node.name}" prevents '
                    "table allocation"
                )
                return False
            existing.keys.append(child.key)
            return True

        if not all(check_child(child) for child in trie.children):
            return

        # Weave width limit for optimization...
        if len(targets) >= (1 << self.options["max_table_elem_width"]):
            debug(
                f'too many different trie targets of "{node.name}" for a table allocation'
            )
            return

        table = self.implementation.node.TableLookup(
            frontend.node.TableLookup(self.id.id(node.name))
        )
        children.append(table)

        # Break Loop
        if not self.map.get(node):
            self.map[node] = table

        for target in targets.values():
            _next = self.translate_trie(node, target.trie, children)
            table.ref.add_edge(
                frontend.node.ReadonlyTableEdge(
                    keys=target.keys, no_advance=target.no_advance, node=_next
                )
            )

        # print('optimized "%s" to a table lookup node' % node.name)
        # Node Has been Optimized to a table Lookup , Now return...
        return table

    def translate_sequence(
        self,
        node: source.node.Match,
        trie: TrieSequence,
        children: list[Wrap[frontend.node.Node]],
    ) -> Wrap[frontend.node.Match]:
        sequence = self.implementation.node.Sequence(
            frontend.node.Sequence(self.id.id(node.name), trie.select)
        )

        children.append(sequence)

        if not self.map.get(node):
            self.map[node] = sequence

        child_node = self.translate_trie(node, trie.child, children)

        value = trie.child.value if isinstance(trie.child, TrieEmpty) else None

        sequence.ref.set_edge(child_node, value)

        return sequence

    def translate_trie(
        self,
        node: source.code.Match,
        trie: TrieNode,
        children: list[Wrap[frontend.node.Node]],
    ):
        if isinstance(trie, TrieEmpty):
            assert self.map.get(node)
            return self.translate(trie.node)
        elif isinstance(trie, TrieSingle):
            return self.translate_single(node, trie, children)
        elif isinstance(trie, TrieSequence):
            return self.translate_sequence(node, trie, children)
        else:
            raise Error("Unknown trie node")

    def translate_single(
        self,
        node: source.code.Match,
        trie: TrieSingle,
        children: list[Wrap[frontend.node.Node]],
    ):
        # Check if Tablelookup could be a valid option to Optimze our code up...
        if maybeTable := self.maybe_table_lookup(node, trie, children):
            return maybeTable

        single = self.implementation.node.Single(
            frontend.node.Single(self.id.id(node.name))
        )
        children.append(single)

        # Break loop...
        if node not in self.map:
            self.map[node] = single

        for child in trie.children:
            child_node = self.translate_trie(node, child.node, children)

            single.ref.add_edge(
                ReadonlySingleEdge(
                    key=child.key,
                    no_advance=child.no_advance,
                    node=child_node,
                    value=child.node.value
                    if isinstance(child.node, TrieEmpty)
                    else None,
                )
            )

        if otherwise := trie.otherwise:
            single.ref.set_otherwise(
                self.translate_trie(node, otherwise, children), True, otherwise.value
            )
        return single

    def translate_span_code(self, code: source.code.Span):
        return self.translate_code(code)

    def translate_code(self, code: source.code.Code):
        """Translates Builder Classes to Frontend Classes..."""

        prefixed = self.code_id.id(code.name).name
        code_impl = self.implementation.code

        # res : WrappedCode
        if isinstance(code, source.code.IsEqual):
            res = code_impl.IsEqual(
                frontend.code.IsEqual(prefixed, code.field, code.value)
            )

        elif isinstance(code, source.code.Load):
            res = code_impl.Load(frontend.code.Load(prefixed, code.field))

        elif isinstance(code, source.code.MulAdd):
            m = frontend.code.MulAdd(
                prefixed,
                code.field,
                frontend.code.MulAddOptions(
                    code.options.base, code.options.max, code.options.signed
                ),
            )
            res = code_impl.MulAdd(m)

        elif isinstance(code, source.code.And):
            # NOTE (Vizonex) I did see the frontend on the Typescript Version Using "Or" instead of "And"
            # line 460 of llparse-frontend/src/frontend.ts
            # So I'm wondering if that was an accident or by design. Might need to Open A Github issue about it...
            res = code_impl.And(frontend.code.And(prefixed, code.field, code.value))
        elif isinstance(code, source.code.Or):
            res = code_impl.Or(frontend.code.Or(prefixed, code.field, code.value))

        elif isinstance(code, source.code.Store):
            res = code_impl.Store(frontend.code.Store(code.name, code.field))

        elif isinstance(code, source.code.Test):
            res = code_impl.Test(frontend.code.Test(prefixed, code.field, code.value))

        elif isinstance(code, source.code.Update):
            res = code_impl.Update(
                frontend.code.Update(prefixed, code.field, code.value)
            )

        # External Callbacks...

        elif isinstance(code, source.code.Span):
            res = code_impl.External(frontend.code.Span(code.name))

        elif isinstance(code, source.code.Match):
            res = code_impl.External(frontend.code.Match(code.name))
        
        elif isinstance(code, source.code.Value):
            res = code_impl.External(frontend.code.Value(code.name))

        else:
            raise Error(f'Un-supported code:"{code.name}" type: "{type(code)}"')

        cache_key = res.ref.cache_key
        if _res := self.code_cache.get(cache_key):
            return _res
        self.code_cache[cache_key] = res
        return res

    def translate_transform(
        self, transform: source.transform.Transform | None
    ) -> Wrap[
        frontend.transform.Transform
        | frontend.transform.ID
        | frontend.transform.ToLower
        | frontend.transform.ToLowerUnsafe
    ]:
        transform_impl = self.implementation.transform
        if not transform or transform.name == "id":
            return transform_impl.ID(frontend.transform.ID())

        match transform.name:
            case "to_lower":
                return transform_impl.ToLower(frontend.transform.ToLower())
            case "to_lower_unsafe":
                return transform_impl.ToLowerUnsafe(frontend.transform.ToLowerUnsafe())
            case _:
                raise Error(f"Unexpected transform name named {transform.name!r}")
