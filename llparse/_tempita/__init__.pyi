from __future__ import annotations as _annotations

import sys
from typing import Any, Literal, TypedDict, TypeVar
from collections.abc import Callable, MutableMapping

from _typeshed import FileDescriptorOrPath, Incomplete

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

K = TypeVar("K")
V = TypeVar("V")

class _TemplateNamespace(TypedDict, total=False):
    start_braces: str
    end_braces: str
    looper: type

class _HTMLTemplateNamspace(_TemplateNamespace):
    html: html
    attr: Callable[..., html]
    url: Callable[[Any], str]
    html_quote: Callable[[Any, bool], Any | bytes | Literal[""]]

_TemplateT = TypeVar("_TemplateT", bound="Template")
_TemplateNamespaceT = TypeVar("_TemplateNamespaceT", bound=_TemplateNamespace)

__all__ = [
    "TemplateError",
    "Template",
    "sub",
    "HTMLTemplate",
    "sub_html",
    "html",
    "bunch",
]

class TemplateError(Exception):
    position: str | int
    name: str | None
    def __init__(
        self, message: str, position: str | int, name: str | None = None
    ) -> None: ...

def get_file_template(
    name: FileDescriptorOrPath, from_template: type[_TemplateT]
) -> _TemplateT: ...

class _TemplateContinue(Exception): ...
class _TemplateBreak(Exception): ...

class Template:
    default_namespace: _TemplateNamespace
    default_encoding: str
    default_inherit: Any | None
    content: bytes | str
    delimiters: tuple[bytes | str, ...]
    name: str | None
    namespace: _TemplateNamespace
    get_template: Callable[[FileDescriptorOrPath, type[_TemplateT]], _TemplateT]
    def __init__(
        self,
        content: bytes | str,
        name: str | None = None,
        namespace: _TemplateNamespace | None = None,
        stacklevel: Incomplete | None = None,
        get_template: Incomplete | None = None,
        default_inherit: Incomplete | None = None,
        line_offset: int = 0,
        delimiters: tuple[str | bytes, ...] | None = None,
    ) -> None: ...
    @classmethod
    def from_filename(
        cls,
        filename: FileDescriptorOrPath,
        namespace: _TemplateNamespace | None = None,
        encoding: Incomplete | None = None,
        default_inherit: Incomplete | None = None,
        get_template=Callable[[str, type[_TemplateT], _TemplateT]],
    ) -> Self: ...
    from_filename: FileDescriptorOrPath
    def substitute(self, *args, **kw) -> str: ...

def sub(content, delimiters: tuple[bytes | str] | None = None, **kw): ...

class bunch(MutableMapping[K, V]):
    def __init__(self, **kw) -> None: ...
    def __setattr__(self, name: str, value: V) -> None: ...
    def __getattr__(self, name: str) -> V: ...
    def __getitem__(self, key: K) -> V: ...

class html:
    value: str
    def __init__(self, value: str) -> None: ...
    def __html__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class HTMLTemplate(Template):
    default_namespace: _HTMLTemplateNamspace
    @classmethod
    def from_filename(
        cls,
        filename: FileDescriptorOrPath,
        namespace: _HTMLTemplateNamspace | None = None,
        encoding: Incomplete | None = None,
        default_inherit: Incomplete | None = None,
        get_template=Callable[[str, type[_TemplateT], _TemplateT]],
    ) -> Self: ...

def sub_html(content: str | bytes, **kw): ...

class TemplateDef:
    def __init__(
        self,
        template,
        func_name,
        func_signature,
        body,
        ns,
        pos,
        bound_self: Incomplete | None = None,
    ) -> None: ...
    def __call__(self, *args, **kw) -> str: ...
    def __get__(self, obj, type: Any | None = None): ...

class TemplateObject:
    get: TemplateObjectGetter
    def __init__(self, name: str) -> None: ...

class TemplateObjectGetter:
    def __init__(self, template_obj: TemplateObject) -> None: ...
    def __getattr__(self, attr): ...

class _Empty:
    def __call__(self, *args, **kw) -> Self: ...
    def __unicode__(self) -> Literal[""]: ...
    def __iter__(self): ...
    def __bool__(self) -> bool: ...
    def __repr__(self) -> Literal["Empty"]: ...
    if sys.version < "3":
        __nonzero__ = __bool__

def fill_command(args=None) -> None: ...
