# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

import collections
import dataclasses
from pathlib import Path
from typing import Any, Optional, Sequence, Tuple

MetadataMember = collections.namedtuple('MetadataMember', ('key', 'value'))
EnumMember = collections.namedtuple('EnumMember', ('key', 'value'))
UnionMember = collections.namedtuple('UnionMember', ('key', 'type'))


@dataclasses.dataclass(frozen=True)
class Attribute:
    name: str = ''


@dataclasses.dataclass(frozen=True)
class DefWithMetadata:
    metadata: Sequence[MetadataMember] = tuple()


@dataclasses.dataclass(frozen=True)
class TypeDef(DefWithMetadata):
    name: str = ''


@dataclasses.dataclass(frozen=True)
class Enum(TypeDef):
    type: Optional[str] = None
    members: Sequence[EnumMember] = tuple()


@dataclasses.dataclass(frozen=True)
class Union(TypeDef):
    type: Optional[str] = None
    members: Sequence[Tuple[str, Optional[int]]] = tuple()


@dataclasses.dataclass(frozen=True)
class Field(DefWithMetadata):
    name: str = ''
    type: Optional[str] = None
    is_vector: bool = False
    default: Any = None


@dataclasses.dataclass(frozen=True)
class Struct(TypeDef):
    type: Optional[str] = None
    fields: Sequence[Tuple[str, Field]] = tuple()


@dataclasses.dataclass(frozen=True)
class Table(TypeDef):
    fields: Sequence[Tuple[str, Field]] = tuple()


@dataclasses.dataclass(frozen=True)
class Schema:

    file_path: Optional[Path] = None
    includes: Sequence[str] = tuple()
    namespace: Optional[Sequence[str]] = None
    declarations: Sequence[Any] = tuple()
    file_extension: Optional[str] = None
    file_identifier: Optional[str] = None
    root_type: Optional[str] = None
