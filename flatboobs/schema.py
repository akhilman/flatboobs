# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

import collections
import enum
import operator as op
import typing
from types import MappingProxyType

import attr
from toolz import functoolz as ft

from flatboobs.constants import STRING_TO_TYPE_MAP, BasicType

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
class Enum(TypeDeclaration):
    type: str = 'byte'
    members: typing.Sequence[EnumMember] = tuple()
    members_map: typing.Mapping[str, EnumMember] = attr.ib(
        attr.Factory(
            lambda self: MappingProxyType(dict(self.members)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )
    default: typing.Optional[int] = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Union(Enum):
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


def type_by_name(
        known_types: typing.Union[typing.Mapping[str, TypeDeclaration],
                                  typing.Iterable[TypeDeclaration]],
        name: str
) -> typing.Union[TypeDeclaration, BasicType]:

    type_map: typing.Mapping[str, TypeDeclaration]
    type_decl: typing.Union[TypeDeclaration, BasicType]

    if isinstance(known_types, collections.abc.Mapping):
        type_map = known_types
    else:
        type_map = {x.name: x for x in known_types}

    try:
        type_decl = STRING_TO_TYPE_MAP[name]
    except KeyError:
        try:
            type_decl = type_map[name]
        except KeyError:
            raise NameError(f'Can not resolve type {name}')

    return type_decl


# pylint plays bad with currying
@ft.memoize(  # pylint: disable=no-value-for-parameter
    key=lambda args, kwargs: '.'.join([args[0].namespace, args[0].name]))
def make_enum(type_decl: Enum) -> typing.Union[enum.IntEnum, enum.IntFlag]:

    # pylint: disable=invalid-name
    EnumMeta: typing.Union[typing.Type[enum.IntEnum],
                           typing.Type[enum.IntFlag]]

    members = [(x.name, x.value) for x in type_decl.members]

    if 'bit_flags' in type_decl.metadata_map:
        EnumMeta = enum.IntFlag
        members = [('None', 0)] + members + [
            ('All', sum(map(op.attrgetter('value'), type_decl.members)))]
    else:
        EnumMeta = enum.IntEnum

    return EnumMeta(type_decl.name, members)  # type: ignore
