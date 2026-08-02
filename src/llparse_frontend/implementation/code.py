from dataclasses import dataclass

from .. import code
from ..wrap import Wrap
from .typedefs import WrapCall


@dataclass(slots=True, frozen=True)
class CodeImplementation:
    And: WrapCall[code.And] = Wrap
    IsEqual: WrapCall[code.IsEqual] = Wrap
    Load: WrapCall[code.Load] = Wrap
    Match: WrapCall[code.Match] = Wrap
    MulAdd: WrapCall[code.MulAdd] = Wrap
    Or: WrapCall[code.Or] = Wrap
    Span: WrapCall[code.Span] = Wrap
    Store: WrapCall[code.Store] = Wrap
    Test: WrapCall[code.Test] = Wrap
    Update: WrapCall[code.Update] = Wrap
    Value: WrapCall[code.Value] = Wrap
