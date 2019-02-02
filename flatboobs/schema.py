# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

import collections
import typing
from types import MappingProxyType

import attr

MetadataMember = collections.namedtuple('MetadataMember', ('name', 'value'))
EnumMember = collections.namedtuple('EnumMember', ('name', 'value'))


@attr.s(auto_attribs=True, frozen=True, slots=True)
class DeclarationWithMetadata:
    metadata: typing.Sequence[MetadataMember] = tuple()
    metadata_map: typing.Mapping[str, MetadataMember] = attr.ib(
        attr.Factory(
            lambda self: MappingProxyType(dict(self.metadata)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class TypeDeclaration(DeclarationWithMetadata):
    namespace: str = ''
    name: str = ''
    is_root: bool = False
    file_identifier: typing.Optional[str] = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class _BaseEnum(TypeDeclaration):
    type: str = 'byte'
    members: typing.Sequence[EnumMember] = tuple()
    members_map: typing.Mapping[str, EnumMember] = attr.ib(
        attr.Factory(
            lambda self: MappingProxyType(dict(self.members)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Enum(_BaseEnum):
    default: typing.Optional[int] = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Union(_BaseEnum):
    pass


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Field(DeclarationWithMetadata):
    name: str = ''
    type: str = 'void'
    is_vector: bool = False
    default: typing.Any = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class _TableLike(TypeDeclaration, typing.Mapping[str, Field]):
    fields: typing.Sequence[Field] = tuple()
    field_map: typing.Mapping[str, Field] = attr.ib(
        attr.Factory(
            lambda self: MappingProxyType({f.name: f
                                           for f in self.fields}),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )

    # pylint: disable=unsubscriptable-object,

    def __getitem__(self: '_TableLike', key: str) -> Field:
        return self.field_map[key]

    def __iter__(self: '_TableLike') -> typing.Iterator[str]:
        return iter(self.field_map)

    def __len__(self: '_TableLike') -> int:
        return len(self.field_map)


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Struct(_TableLike):
    pass


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Table(_TableLike):
    pass


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Schema(typing.Mapping[str, TypeDeclaration]):

    schema_file: typing.Optional[str] = None
    includes: typing.FrozenSet[str] = frozenset()
    namespace: str = ''
    attributes: typing.FrozenSet[str] = frozenset()
    types: typing.FrozenSet[TypeDeclaration] = frozenset()
    file_extension: typing.Optional[str] = None
    file_identifier: typing.Optional[str] = None
    root_type: typing.Optional[str] = None

    type_map: typing.Mapping[str, TypeDeclaration] = attr.ib(
        attr.Factory(
            lambda self: MappingProxyType({
                x.name: x for x in self.types
            }),
            takes_self=True
        ),
        hash=False, init=False, repr=False, cmp=False
    )

    # pylint: disable=unsubscriptable-object,

    def __getitem__(self: 'Schema', key: str) -> TypeDeclaration:
        return self.type_map[key]

    def __iter__(self: 'Schema') -> typing.Iterator[str]:
        return iter(self.type_map)

    def __len__(self: 'Schema') -> int:
        return len(self.type_map)
