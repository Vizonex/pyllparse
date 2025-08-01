from ..pyfront import front as code
from ..pyfront import nodes as node
from ..pyfront import transform
from ..pyfront.front import IWrap


class INodeImplementation:
    def __init__(self) -> None:
        return

    def Consume(self, n: node.Consume):
        return IWrap(n)

    def Empty(self, n: node.Empty):
        return IWrap(n)

    def Error(self, n: node.Error):
        return IWrap(n)

    def Pause(self, n: node.Pause):
        return IWrap(n)

    def Invoke(self, n: node.Invoke):
        return IWrap(n)

    def Sequence(self, n: node.Sequence):
        return IWrap(n)

    def Single(self, n: node.Single):
        return IWrap(n)

    def SpanEnd(self, n: node.SpanEnd):
        return IWrap(n)

    def SpanStart(self, n: node.SpanStart):
        return IWrap(n)

    def TableLookup(self, n: node.TableLookup):
        return IWrap(n)


class ITransformImplementation:
    def __init__(self) -> None:
        return

    def ID(self, t: transform.ID):
        return IWrap(t)

    def ToLower(self, t: transform.ToLower):
        return IWrap(t)

    def ToLowerUnsafe(self, t: transform.ToLowerUnsafe):
        return IWrap(t)


class ICodeImplementation:
    def __init__(self) -> None:
        return

    def And(self, c: code.And):
        return IWrap(c)

    def Load(self, c: code.Load):
        return IWrap(c)

    def IsEqual(self, c: code.IsEqual):
        return IWrap(c)

    def Match(self, c: code.Match):
        return IWrap(c)

    def MulAdd(self, c: code.MulAdd):
        return IWrap(c)

    def Or(self, c: code.Or):
        return IWrap(c)

    def Span(self, c: code.Span):
        return IWrap(c)

    def Store(self, c: code.Store):
        return IWrap(c)

    def Test(self, c: code.Test):
        return IWrap(c)

    def Update(self, c: code.Update):
        return IWrap(c)

    def Value(self, c: code.Value):
        return IWrap(c)


class IImplementation:
    def __init__(self) -> None:
        self.code = ICodeImplementation()
        self.node = INodeImplementation()
        self.transform = ITransformImplementation()
