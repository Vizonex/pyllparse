from dataclasses import dataclass

from .. import transform
from ..wrap import Wrap
from .typedefs import WrapCall


@dataclass(frozen=True, slots=True)
class TransformImplementation:
    ID: WrapCall[transform.ID] = Wrap
    ToLower: WrapCall[transform.ToLower] = Wrap
    ToLowerUnsafe: WrapCall[transform.ToLowerUnsafe] = Wrap
