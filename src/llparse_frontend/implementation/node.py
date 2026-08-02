from dataclasses import dataclass

from .. import node
from ..wrap import Wrap
from .typedefs import WrapCall


@dataclass(slots=True, frozen=True)
class NodeImplementation:
    Consume: WrapCall[node.Consume] = Wrap
    Empty: WrapCall[node.Empty] = Wrap
    Error: WrapCall[node.Error] = Wrap
    Invoke: WrapCall[node.Invoke] = Wrap
    Pause: WrapCall[node.Pause] = Wrap
    Sequence: WrapCall[node.Sequence] = Wrap
    Single: WrapCall[node.Single] = Wrap
    SpanEnd: WrapCall[node.SpanEnd] = Wrap
    SpanStart: WrapCall[node.SpanStart] = Wrap
    TableLookup: WrapCall[node.TableLookup] = Wrap
    Unpack: WrapCall[node.Unpack] = Wrap
