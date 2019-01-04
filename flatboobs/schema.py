# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import attr
from frozendict import frozendict


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Attribute:
    name: str = ''


@attr.s(auto_attribs=True, frozen=True, slots=True)
class TypeDef:
    name: str = ''
    metadata: Dict[str, Any] = frozendict()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Enum(TypeDef):
    type: Optional[str] = None
    members: Sequence[Tuple[str, Optional[int]]] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Union(TypeDef):
    type: Optional[str] = None
    members: Sequence[Tuple[str, Optional[int]]] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Field:
    name: str = ''
    type: Optional[str] = None
    is_vector: bool = False
    default: Any = None
    metadata: Dict[str, Any] = frozendict()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Struct(TypeDef):
    type: Optional[str] = None
    fields: Sequence[Tuple[str, Field]] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Table(TypeDef):
    fields: Sequence[Tuple[str, Field]] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Schema:

    file_path: Optional[Path] = None
    includes: Sequence[str] = tuple()
    namespace: Optional[Sequence[str]] = None
    declarations: Sequence[Any] = tuple()
    file_extension: Optional[str] = None
    file_identifier: Optional[str] = None
    root_type: Optional[str] = None
