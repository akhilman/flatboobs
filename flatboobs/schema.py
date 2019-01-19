# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

import collections
from pathlib import Path
from typing import Any, Optional, Sequence

import attr

MetadataMember = collections.namedtuple('MetadataMember', ('name', 'value'))
EnumMember = collections.namedtuple('EnumMember', ('name', 'value'))
UnionMember = collections.namedtuple('UnionMember', ('type', 'value'))


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Attribute:
    namespace: Optional[Sequence[str]] = None
    name: str = ''


@attr.s(auto_attribs=True, frozen=True, slots=True)
class DefWithMetadata:
    metadata: Sequence[MetadataMember] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class TypeDef(DefWithMetadata):
    namespace: Optional[Sequence[str]] = None
    name: str = ''
    is_root: bool = False
    identifier: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Enum(TypeDef):
    type: Optional[str] = None
    members: Sequence[EnumMember] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Union(TypeDef):
    type: Optional[str] = None
    members: Sequence[UnionMember] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Field(DefWithMetadata):
    name: str = ''
    type: Optional[str] = None
    is_vector: bool = False
    default: Any = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Struct(TypeDef):
    type: Optional[str] = None
    fields: Sequence[Field] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Table(TypeDef):
    fields: Sequence[Field] = tuple()


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Schema:

    file_path: Optional[Path] = None
    includes: Sequence[str] = tuple()
    namespace: Optional[Sequence[str]] = None
    declarations: Sequence[Any] = tuple()
    file_extension: Optional[str] = None
    file_identifier: Optional[str] = None
    root_type: Optional[str] = None
