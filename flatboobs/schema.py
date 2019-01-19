# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

import collections
import types
from typing import Any, Mapping, Optional, Sequence

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
    metadata_map: Mapping[str, MetadataMember] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType(dict(self.metadata)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


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
    members_map: Mapping[str, EnumMember] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType(dict(self.members)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Union(Enum):
    type: Optional[str] = None
    members: Sequence[UnionMember] = tuple()
    members_map: Mapping[str, UnionMember] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType(dict(self.members)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Field(DefWithMetadata):
    name: str = ''
    type: Optional[str] = None
    is_vector: bool = False
    default: Any = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Struct(TypeDef):
    fields: Sequence[Field] = tuple()
    fields_map: Mapping[str, Field] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType({f.name: f
                                                 for f in self.fields}),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Table(TypeDef):
    fields: Sequence[Field] = tuple()
    fields_map: Mapping[str, Field] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType({f.name: f
                                                 for f in self.fields}),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Schema:

    file_path: Optional[str] = None
    includes: Sequence[str] = tuple()
    namespace: Optional[Sequence[str]] = None
    declarations: Sequence[Any] = tuple()
    file_extension: Optional[str] = None
    file_identifier: Optional[str] = None
    root_type: Optional[str] = None
