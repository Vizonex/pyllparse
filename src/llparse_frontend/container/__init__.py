from collections.abc import Callable
from functools import partial

from ..implementation import (
    CodeImplementation,
    Implementation,
    NodeImplementation,
    TransformImplementation,
)
from ..wrap import T, Wrap
from .wrap import ContainerWrap


class Container:
    __slots__ = ("map",)

    def __init__(self) -> None:
        self.map: dict[str, Implementation] = {}

    def add(self, key: str, impl: Implementation) -> None:
        assert key not in self.map, f'Duplicate implementation key: "{key}"'
        self.map[key] = impl

    def build(self) -> Implementation:
        return Implementation(
            self.build_code(), self.build_node(), self.build_transform()
        )

    def build_code(self):
        return CodeImplementation(
            And=self.combine(lambda impl: impl.code.And),
            IsEqual=self.combine(lambda impl: impl.code.IsEqual),
            Load=self.combine(lambda impl: impl.code.Load),
            Match=self.combine(lambda impl: impl.code.Match),
            MulAdd=self.combine(lambda impl: impl.code.MulAdd),
            Or=self.combine(lambda impl: impl.code.Or),
            Span=self.combine(lambda impl: impl.code.Span),
            Store=self.combine(lambda impl: impl.code.Store),
            Test=self.combine(lambda impl: impl.code.Test),
            Update=self.combine(lambda impl: impl.code.Update),
            Value=self.combine(lambda impl: impl.code.Value),
        )

    def build_node(self):
        return NodeImplementation(
            Consume=self.combine(lambda impl: impl.node.Consume),
            Empty=self.combine(lambda impl: impl.node.Empty),
            Error=self.combine(lambda impl: impl.node.Error),
            Invoke=self.combine(lambda impl: impl.node.Invoke),
            Pause=self.combine(lambda impl: impl.node.Pause),
            Sequence=self.combine(lambda impl: impl.node.Sequence),
            Single=self.combine(lambda impl: impl.node.Single),
            SpanEnd=self.combine(lambda impl: impl.node.SpanEnd),
            SpanStart=self.combine(lambda impl: impl.node.SpanStart),
            TableLookup=self.combine(lambda impl: impl.node.TableLookup),
            Unpack=self.combine(lambda impl: impl.node.Unpack),
        )

    def build_transform(self) -> TransformImplementation:
        return TransformImplementation(
            ID=self.combine(lambda impl: impl.transform.ID),
            ToLower=self.combine(lambda impl: impl.transform.ToLower),
            ToLowerUnsafe=self.combine(lambda impl: impl.transform.ToLowerUnsafe),
        )

    def combine(
        self, gather: Callable[[Implementation], Callable[[T], Wrap[T]]]
    ) -> Callable[[T], ContainerWrap[T, Wrap[T]]]:
        return partial(
            ContainerWrap, map={key: gather(impl) for key, impl in self.map.items()}
        )
