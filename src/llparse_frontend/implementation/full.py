from dataclasses import dataclass, field

from .code import CodeImplementation
from .node import NodeImplementation
from .transform import TransformImplementation


@dataclass(slots=True, frozen=True)
class Implementation:
    code: CodeImplementation = field(default_factory=CodeImplementation)
    node: NodeImplementation = field(default_factory=NodeImplementation)
    transform: TransformImplementation = field(default_factory=TransformImplementation)
