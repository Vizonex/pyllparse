from dataclasses import dataclass, field
from typing import Literal, Optional, Union

from .enumerator import Enumerator
from .pybuilder import LoopChecker
from .pybuilder import builder as source

# from pyfront.namespace import code, node , transform
from .pyfront import namespace as _frontend
from .pyfront.front import Identifier, IWrap, SpanField
from .pyfront.implementation import IImplementation
from .pyfront.nodes import ITableEdge
from .pyfront.peephole import Peephole
from .spanalloc import SpanAllocator
from .trie import Trie, TrieEmpty, TrieNode, TrieSequence, TrieSingle, ITrieSingleChild

DEFAULT_MIN_TABLE_SIZE = 32
DEFAULT_MAX_TABLE_WIDTH = 4

from logging import getLogger

log = getLogger("llparse.frontend")


WrappedNode = IWrap[_frontend.node.Node]
WrappedCode = IWrap[_frontend.code.Code]


@dataclass
class ITableLookupTarget:
    trie: TrieEmpty
    noAdvance: bool
    keys: list[int] = field(default_factory=list)


# TODO (Vizonex) Enable logging to diagnose bigger issues whenever logging is enabled by the User

# For those who care...
# The Original Build Time: 5 - 7 Hours (Including tanslation of typescript libraries)
# about 15 testruns so far...
# FrontEnd Code Time : 2 Days with several 4 - 5 Hour Sessions...

# Hardest Part: Figuring out my otherwise block all the way inside of the builder was the problem:
# Causing me to bak and forth for 8 hours until I found the problem in the builder itself. :(

# Second Hardest Part: Implementing Span allocator due to anonymous
# allocate Function being difficult to implemement
# due to "=>" key

# Most Intresting Part "so far" - for me (Vizonex) translating llparse's builder module and this frontend
# I think the C compiler will be alot more intresting than this somewhat...

# I Think I could use the frontend to help gather span api calls
# and other callbacks To Then make a compilable Settings
# API like in llhttp but instead
# having api.h be compilable with all the little marco Span
# Callbacks as well , Cython .pxd Compiler could be called
# afterwards to handle all properties and settings

# Allow me to leave you with this Quote by me

# "If You want to accomplish something, do it yourself" - Vizonex


# TODO (Vizonex) Make a Mini python enum to C enum Compiler as a Cool Demo...

# (WARNING!) I Plan to Drop 3.9 Support Later this Summer (2023)....
# I will work on a numeric conv Vulnerability Str to int cap Bypass When I upgrade...


@dataclass
class IFrontendResult:
    prefix: str
    root: IWrap[_frontend.node.Node]
    properties: list[source.Property] = field(default_factory=list)
    spans: list[_frontend.node.SpanField] = field(default_factory=list)
    resumptionTargets: set[IWrap[_frontend.node.Node]] = field(default_factory=set)


@dataclass
class IFrontendOptions:
    maxTableWidth: int
    minTableSize: int


MatchChildren = list[WrappedNode]
MatchResult = Union[WrappedNode, list[WrappedNode]]


class Frontend:
    def __init__(
        self,
        prefix: str,
        implementation: IImplementation = IImplementation(),
        options: dict[Literal["maxTableElemWidth", "minTableSize"], int] = dict(),
    ) -> None:
        self.prefix = prefix
        self.Id = Identifier(self.prefix + "__n_")
        self.codeId = Identifier(self.prefix + "__c_")
        self.Map: dict[source.code.Node, IWrap[_frontend.node.Node]] = {}
        self.spanMap: dict[source.code.Span, SpanField] = {}
        self.codeCache: dict[str, WrappedCode] = {}
        self.resumptionTargets: set[WrappedNode] = set()
        self.implementation = implementation
        self.prefix = prefix
        self.options: dict[Literal["maxTableElemWidth", "minTableSize"], int] = {
            "maxTableElemWidth": options.get(
                "maxTableElemWidth", DEFAULT_MAX_TABLE_WIDTH
            ),
            "minTableSize": options.get("minTableSize", DEFAULT_MIN_TABLE_SIZE),
        }

        if 0 > self.options["maxTableElemWidth"]:
            raise AssertionError(
                "Invalid `options.maxTableElemWidth`, must be positive"
            )

    def compile(self, root: source.code.Node, properties: list[source.Property] = []):
        lc = LoopChecker()
        lc.check(root)

        spanAllocator = SpanAllocator()
        sourceSpans = spanAllocator.allocate(root)

        spans: list[SpanField] = []
        for index, concurrent in enumerate(sourceSpans.concurrency):
            span = SpanField(
                index, [self.translateCode(c.callback) for c in concurrent]
            )

            for sourceSpan in concurrent:
                self.spanMap[sourceSpan] = span

            spans.append(span)

        # from .debug import Debugger
        # o = Debugger.getAllNodes(root)
        # print("debug",o)
        # Translate Code
        out = self.translate(root)

        # Enumerate
        enumerator = Enumerator()
        nodes = enumerator.getAllNodes(out)
        # Peephole optimizations...
        peephole = Peephole()
        out = peephole.optimize(out, nodes)

        # Re-Enumerate
        nodes = enumerator.getAllNodes(out)

        # DONT FORGET TO ADD "OUT" TO THE RESUMPTION TARGETS!!!
        self.resumptionTargets.add(out)

        # Register resumption targets...
        for node in nodes:
            self.registerNode(node)

        return IFrontendResult(
            prefix=self.prefix,
            properties=properties,
            resumptionTargets=self.resumptionTargets,
            root=out,
            spans=spans,
        )

    def translateMatch(self, node: source.code.Match) -> list[WrappedNode]:
        trie = Trie(node.name)
        assert node.getOtherwiseEdge()
        trieNode = trie.build(list(node))

        if not trieNode:
            log.debug("TrieNode was nonexistant")
            return self.implementation.node.Empty(
                _frontend.node.Empty(self.Id.id(node.name))
            )

        children: MatchChildren = []

        self.translateTrie(node, trieNode, children)
        assert children

        return children

    def registerNode(self, node: WrappedNode) -> None:
        # NOTE NO Implementations required here since this is python!
        if isinstance(
            node.ref,
            (
                _frontend.node.Consume,
                _frontend.node.Empty,
                _frontend.node.Sequence,
                _frontend.node.Single,
                _frontend.node.TableLookup,
            ),
        ):
            self.resumptionTargets.add(node)
        elif isinstance(node.ref, (_frontend.node.Pause, _frontend.node.SpanEnd)):
            self.resumptionTargets.add(node.ref.otherwise.node)

    def translate(self, node: source.code.Node):
        if self.Map.get(node) is not None:
            return self.Map[node]

        def ID():
            return self.Id.id(node.name)

        nodeImpl = self.implementation.node

        if isinstance(node, source.code.Error):
            result = nodeImpl.Error(_frontend.node.Error(ID(), node.code, node.reason))

        elif isinstance(node, source.code.Pause):
            result = nodeImpl.Pause(_frontend.node.Error(ID(), node.code, node.reason))

        elif isinstance(node, source.code.Comsume):
            result = nodeImpl.Consume(_frontend.node.Consume(ID(), node.field))

        elif isinstance(node, source.code.SpanStart):
            result = nodeImpl.SpanStart(
                _frontend.node.SpanStart(
                    ID(),
                    self.spanMap[node.span],
                    self.translateSpanCode(node.span.callback),
                )
            )

        elif isinstance(node, source.code.SpanEnd):
            result = nodeImpl.SpanEnd(
                _frontend.node.SpanEnd(
                    ID(),
                    self.spanMap[node.span],
                    self.translateSpanCode(node.span.callback),
                )
            )

        elif isinstance(node, source.code.Invoke):
            assert node.code.signature in ["match", "value"], (
                "Passing `span` callback to `invoke` is not allowed"
            )
            result = nodeImpl.Invoke(
                _frontend.node.Invoke(ID(), self.translateCode(node.code))
            )

        elif isinstance(node, source.code.Match):
            result = self.translateMatch(node)
        else:
            raise Exception(f'Unknown Node Type for :"{node.name}" {type(node)}')

        otherwise = node.getOtherwiseEdge()

        if isinstance(result, list):
            # result:list[WrappedNode]
            assert isinstance(node, source.code.Match)
            _match = node

            if not otherwise:
                raise Exception(f'Node "{node.name}" has no ".otherwise()"')

            else:
                for child in result:
                    if not child.ref.otherwise:
                        child.ref.setOtherwise(
                            self.translate(otherwise.node), otherwise.noAdvance
                        )

            transform = self.translateTransform(_match.getTransform())
            for child in result:
                # TODO Vizonex : This might break , be sure to make a workaround function here...
                child.ref.setTransform(transform)

            assert len(result) >= 1
            return result[0]

        else:
            single: WrappedNode = result

            assert isinstance(single.ref, _frontend.node.Node)

            self.Map[node] = single

            if otherwise is not None:
                single.ref.setOtherwise(
                    self.translate(otherwise.node), otherwise.noAdvance
                )

            else:
                assert isinstance(node, source.code.Error), (
                    f'Node "{node.name}" has no `.otherwise()'
                )

            if isinstance(single.ref, _frontend.node.Invoke):
                for edge in node:
                    single.ref.addEdge(
                        ord(edge.key) if isinstance(edge.key, str) else edge.key,
                        self.translate(edge.node),
                    )
            else:
                assert len(list(node)) == 0

            return single

    def maybeTableLookup(
        self, node: source.code.Match, trie: TrieSingle, children: MatchChildren
    ):
        if len(trie.children) < self.options["minTableSize"]:
            return None

        targets: dict[source.code.Node, ITableLookupTarget] = {}

        def check_child(child: ITrieSingleChild):
            nonlocal targets
            if not isinstance(child.node, TrieEmpty):
                log.debug(
                    'non-leaf trie child of "%s" prevents table allocation' % node.name
                )
                return False
            empty = child.node
            if empty.value is not None:
                log.debug(
                    'value passing trie leaf of "%s" prevents table allocation'
                    % node.name
                )
                return False

            target = empty.node
            if target not in targets:
                targets[target] = ITableLookupTarget(
                    keys=[child.key], noAdvance=child.noAdvance, trie=empty
                )
                return True

            existing = targets[target]
            if existing.noAdvance != child.noAdvance:
                log.debug(
                    f'noAdvance mismatch in a trie leaf of "{node.name}" prevents '
                    "table allocation"
                )
                return False
            existing.keys.append(child.key)
            return True

        if not all([check_child(child) for child in trie.children]):
            return

        # Weave width limit for optimization...
        if len(targets) >= (1 << self.options["maxTableElemWidth"]):
            log.debug(
                'too many different trie targets of "%s" for a table allocation'
                % node.name
            )
            return

        table = self.implementation.node.TableLookup(
            _frontend.node.TableLookup(self.Id.id(node.name))
        )
        children.append(table)

        # Break Loop
        if not self.Map.get(node):
            self.Map[node] = table

        for target in targets.values():
            _next = self.translateTrie(node, target.trie, children)
            table.ref.addEdge(
                ITableEdge(keys=target.keys, noAdvance=target.noAdvance, node=_next)
            )

        # print('optimized "%s" to a table lookup node' % node.name)
        # Node Has been Optimized to a table Lookup , Now return...
        return table

    def translateSequence(
        self, node: source.code.Match, trie: TrieSequence, children: MatchChildren
    ) -> IWrap[_frontend.node.Match]:
        sequence = self.implementation.node.Sequence(
            _frontend.node.Sequence(self.Id.id(node.name), trie.select)
        )

        children.append(sequence)

        if not self.Map.get(node):
            self.Map[node] = sequence

        childNode = self.translateTrie(node, trie.child, children)

        value = trie.child.value if isinstance(trie.child, TrieEmpty) else None

        sequence.ref.setEdge(childNode, value)

        return sequence

    def translateTrie(
        self, node: source.code.Match, trie: TrieNode, children: MatchChildren
    ):
        if isinstance(trie, TrieEmpty):
            assert self.Map.get(node)
            return self.translate(trie.node)
        elif isinstance(trie, TrieSingle):
            return self.translateSingle(node, trie, children)
        elif isinstance(trie, TrieSequence):
            return self.translateSequence(node, trie, children)
        else:
            raise TypeError("Unknown trie node")

    def translateSingle(
        self, node: source.code.Match, trie: TrieSingle, children: MatchChildren
    ):
        # Check if Tablelookup could be a valid option to Optimze our code up...
        if maybeTable := self.maybeTableLookup(node, trie, children):
            return maybeTable

        single = self.implementation.node.Single(
            _frontend.node.Single(self.Id.id(node.name))
        )
        children.append(single)

        # Break loop...
        if not self.Map.get(node):
            self.Map[node] = single

        for child in trie.children:
            childNode = self.translateTrie(node, child.node, children)

            single.ref.addEdge(
                key=child.key,
                noAdvance=child.noAdvance,
                node=childNode,
                value=child.node.value if isinstance(child.node, TrieEmpty) else None,
            )

        if otherwise := trie.otherwise:
            single.ref.setOtherwise(
                self.translateTrie(node, otherwise, children), True, otherwise.value
            )
        return single

    def translateSpanCode(self, code: source.code._Span):
        return self.translateCode(code)

    def translateCode(
        self, code: source.code.Code
    ):
        """Translates Builder Classes to Frontend Classes..."""

        prefixed = self.codeId.id(code.name).name
        codeImpl = self.implementation.code

        # res : WrappedCode
        if isinstance(code, source.code.IsEqual):
            res = codeImpl.IsEqual(
                _frontend.code.IsEqual(prefixed, code.field, code.value)
            )

        elif isinstance(code, source.code.Load):
            res = codeImpl.Load(_frontend.code.Load(prefixed, code.field))

        elif isinstance(code, source.code.MulAdd):
            m = _frontend.code.MulAdd(
                prefixed,
                code.field,
                _frontend.code.IMulAddOptions(
                    code.options.base, code.options.max, code.options.signed
                ),
            )
            res = codeImpl.MulAdd(m)

        elif isinstance(code, source.code.And):
            # NOTE (Vizonex) I did see the frontend on the Typescript Version Using "Or" instead of "And"
            # line 460 of llparse-frontend/src/frontend.ts
            # So I'm wondering if that was an accident or by design. Might need to Open A Github issue about it...
            res = codeImpl.And(_frontend.code.And(prefixed, code.field, code.value))
        elif isinstance(code, source.code.Or):
            res = codeImpl.Or(_frontend.code.Or(prefixed, code.field, code.value))

        elif isinstance(code, source.code.Store):
            res = codeImpl.Store(_frontend.code.Store(code.name, code.field))

        elif isinstance(code, source.code.Test):
            res = codeImpl.Test(_frontend.code.Test(prefixed, code.field, code.value))

        elif isinstance(code, source.code.Update):
            res = codeImpl.Update(
                _frontend.code.Update(prefixed, code.field, code.value)
            )

        # External Callbacks...

        elif isinstance(code, source.code._Span):
            res = codeImpl.Span(_frontend.code.Span(code.name))
        elif isinstance(code, source.code._Match):
            res = codeImpl.Match(_frontend.code.Match(code.name))
        elif isinstance(code, source.code.Value):
            res = codeImpl.Value(_frontend.code.Value(code.name))

        else:
            raise Exception(f'UnSupported code:"{code.name}" type: "{type(code)}"')

        if _res := self.codeCache.get(res.ref.cacheKey):
            return _res
        self.codeCache[res.ref.cacheKey] = res
        return res

    def translateTransform(
        self, transform: Optional[source.code.Transform]
    ) -> IWrap[
        Union[
            _frontend.transform.Transform,
            _frontend.transform.ID,
            _frontend.transform.ToLower,
            _frontend.transform.ToLowerUnsafe,
        ]
    ]:
        transformImpl = self.implementation.transform
        if not transform or transform.name == "id":
            return transformImpl.ID(_frontend.transform.ID())
        elif transform.name == "to_lower":
            return transformImpl.ToLower(_frontend.transform.ToLower())

        elif transform.name == "to_lower_unsafe":
            return transformImpl.ToLowerUnsafe(_frontend.transform.ToLowerUnsafe())
