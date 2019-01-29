# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

import collections
import enum
import operator as op
import pathlib
import typing
from types import MappingProxyType

import attr
from toolz import functoolz as ft
from toolz import itertoolz as it

from flatboobs import logging
from flatboobs.constants import STRING_TO_TYPE_MAP, PYTYPE_MAP, BasicType

MetadataMember = collections.namedtuple('MetadataMember', ('name', 'value'))
EnumMember = collections.namedtuple('EnumMember', ('name', 'value'))

logger = logging.getLogger('flatboobs')


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


def load_from_string(
        source: str,
        schema_file: typing.Optional[str] = None,
) -> Schema:

    import flatboobs.parser

    schema = flatboobs.parser.parse(source, schema_file=schema_file)
    return schema


def _load_with_includes(
        join_path: typing.Callable[[typing.Any, str], str],
        read: typing.Callable[[typing.Any, str], str],
        visited: typing.FrozenSet[str],
        package: typing.Any,
        resource: str,

) -> typing.Optional[Schema]:

    schema_path = join_path(package, resource)
    if schema_path in visited:
        return None
    visited = visited | {schema_path}

    source = read(package, resource)
    schema = load_from_string(source, schema_file=schema_path)

    included_schema = ft.compose(
        tuple,
        ft.curry(filter)(
            ft.compose(ft.curry(op.eq)(schema.namespace),
                       op.attrgetter('namespace'))
        ),
        ft.curry(filter)(None),
        ft.curry(map)(
            ft.partial(_load_with_includes,
                       join_path, read, visited, package)
        ),
    )(schema.includes)

    attributes = ft.compose(
        frozenset,
        it.concat,
        ft.curry(map)(op.attrgetter('attributes')),
        ft.curry(it.cons)(schema),
    )(included_schema)

    # pylint: disable=no-value-for-parameter
    types: typing.FrozenSet[TypeDeclaration]
    types = ft.compose(
        frozenset,
        it.unique,
        it.concat,
        ft.curry(map)(op.attrgetter('types')),
        ft.curry(it.cons)(schema),
    )(included_schema)

    schema = attr.evolve(
        schema,
        includes=frozenset(),
        attributes=attributes,
        types=types
    )

    return schema


def load_from_file(
        fpath: typing.Union[pathlib.Path, str],
) -> Schema:

    if not isinstance(fpath, pathlib.Path):
        fpath = pathlib.Path(fpath)

    logger.debug('Loading schema from %s', fpath)

    schema = _load_with_includes(
        lambda p, r: str(p / r),
        lambda p, r: (p / r).read_text(),
        frozenset(),
        fpath.parent,
        fpath.name,
    )

    assert schema

    return schema


def load_from_directory(
        path: typing.Union[pathlib.Path, str],
        suffix: str = '.fbs'
) -> typing.Iterator[Schema]:

    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    return map(
        load_from_file,
        path.glob(f'*{suffix}')
    )


def load_from_package(
        package: str,
        suffix: str = '.fbs'
) -> typing.Iterator[Schema]:
    raise NotImplementedError


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


TD = typing.TypeVar('TD', Table, Struct, Enum, Union)


def resolve_type_references(
        known_types: typing.Union[typing.Mapping[str, TypeDeclaration],
                                  typing.Sequence[TypeDeclaration]],
        type_decl: TD,
        max_depth: int = 2,
) -> TD:

    if max_depth <= 0:
        return type_decl

    if isinstance(type_decl, BasicType):
        return type_decl

    # TODO convert default values for enums and unions
    # TODO unions and enums

    if isinstance(known_types, collections.abc.Mapping):
        type_map = {k: v for k, v in known_types.items()
                    if v.namespace == type_decl.namespace}
    else:
        type_map = {v.name: v for v in known_types
                    if v.namespace == type_decl.namespace}

    def resolve_field(field_decl, max_depth):
        if isinstance(field_decl.type, (TypeDeclaration, BasicType)):
            return field_decl
        field_type = type_by_name(type_map, field_decl.type)
        field_type = resolve_type_references(type_map, field_type,
                                             max_depth=max_depth)
        pytype = PYTYPE_MAP.get(field_type, None)
        default = (pytype and field_decl.default is not None
                   and pytype(field_decl.default) or field_decl.default)
        return attr.evolve(
            field_decl,
            type=field_type,
            default=default
        )

    def resolve_union_member(member_decl, max_depth):
        if isinstance(member_decl.type, (TypeDeclaration, BasicType)):
            return member_decl
        member_type = type_by_name(type_map, member_decl.type)
        member_type = resolve_type_references(type_map, member_type,
                                              max_depth=max_depth)
        return attr.evolve(
            member_decl,
            type=member_type
        )

    if isinstance(type_decl, (Table, Struct)):
        type_decl = attr.evolve(
            type_decl,
            fields=tuple(map(
                ft.partial(resolve_field, max_depth=max_depth-1),
                type_decl.fields
            ))
        )
    # elif isinstance(type_decl, Enum):
    #   pass
    # elif isinstance(type_decl, Union):
    #     type_decl = attr.evolve(
    #         type_decl,
    #         members=tuple(map(
    #             ft.partial(resolve_union_member, max_depth=max_depth-1),
    #             type_decl.members
    #         ))
    #     )

    return type_decl
