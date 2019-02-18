# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

import enum
import operator as op
import typing
from types import MappingProxyType

import attr
import toolz.functoolz as ft
import toolz.itertoolz as it


class MetadataMember(typing.NamedTuple):
    name: str
    value: typing.Any


class EnumMember(typing.NamedTuple):
    name: str
    value: int


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

    def asenum(
            self: 'Enum'
    ) -> typing.Type[typing.Union[enum.IntEnum, enum.IntFlag]]:

        # pylint: disable=invalid-name
        EnumMeta: typing.Union[typing.Type[enum.IntEnum],
                               typing.Type[enum.IntFlag]]

        # pylint: disable=unsupported-membership-test
        # pylint: disable=no-value-for-parameter
        if self.metadata_map.get('bit_flags', False):
            EnumMeta = enum.IntFlag
            members = ft.compose(
                ft.partial(sorted, key=op.itemgetter(0)),
                ft.partial(ft.flip(it.concatv), [
                    ('NONE', 0),
                    ('ALL', sum(map(op.attrgetter('value'), self.members)))
                ]),
            )(self.members)
        else:
            EnumMeta = enum.IntEnum
            members = self.members

        return EnumMeta(self.name, members)  # type: ignore


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Union(_BaseEnum):

    def asenum(
            self: 'Union'
    ) -> typing.Type[typing.Union[enum.IntEnum, enum.IntFlag]]:

        # pylint: disable=no-value-for-parameter
        members = ft.compose(
            ft.partial(sorted, key=op.itemgetter(0)),
            ft.partial(ft.flip(it.concatv), [('NONE', 0)]),
        )(self.members)

        return enum.IntEnum(self.name, members)  # type: ignore


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
