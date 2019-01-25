# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring  # TODO add docstrings

import collections
import operator as op
import pathlib
import types
import typing

import attr
from toolz import functoolz as ft
from toolz import itertoolz as it

import flatboobs.parser
from flatboobs import logging

MetadataMember = collections.namedtuple('MetadataMember', ('name', 'value'))
EnumMember = collections.namedtuple('EnumMember', ('name', 'value'))
UnionMember = collections.namedtuple('UnionMember', ('type', 'value'))

logger = logging.getLogger('flatboobs')


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Attribute:
    namespace: str = ''
    name: str = ''


@attr.s(auto_attribs=True, frozen=True, slots=True)
class DeclarationWithMetadata:
    metadata: typing.Sequence[MetadataMember] = tuple()
    metadata_map: typing.Mapping[str, MetadataMember] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType(dict(self.metadata)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class TypeDeclaration(DeclarationWithMetadata):
    namespace: str = ''
    name: str = ''
    is_root: bool = False
    identifier: typing.Optional[str] = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Enum(TypeDeclaration):
    type: typing.Optional[str] = None
    members: typing.Sequence[EnumMember] = tuple()
    members_map: typing.Mapping[str, EnumMember] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType(dict(self.members)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Union(TypeDeclaration):
    type: typing.Optional[str] = None
    members: typing.Sequence[UnionMember] = tuple()
    members_map: typing.Mapping[str, UnionMember] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType(dict(self.members)),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Field(DeclarationWithMetadata):
    name: str = ''
    type: typing.Optional[str] = None
    is_vector: bool = False
    default: typing.Any = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Struct(TypeDeclaration):
    fields: typing.Sequence[Field] = tuple()
    fields_map: typing.Mapping[str, Field] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType({f.name: f
                                                 for f in self.fields}),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Table(TypeDeclaration):
    fields: typing.Sequence[Field] = tuple()
    fields_map: typing.Mapping[str, Field] = attr.ib(
        attr.Factory(
            lambda self: types.MappingProxyType({f.name: f
                                                 for f in self.fields}),
            takes_self=True
        ),
        hash=False, init=False, repr=False
    )


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Schema:

    schema_file: typing.Optional[str] = None
    includes: typing.Sequence[str] = tuple()
    namespace: str = ''
    declarations: typing.Sequence[typing.Any] = tuple()
    file_extension: typing.Optional[str] = None
    file_identifier: typing.Optional[str] = None
    root_type: typing.Optional[str] = None


def extract_types(schema: Schema) -> typing.Iterator[TypeDeclaration]:
    return filter(
        lambda x: isinstance(x, TypeDeclaration),
        schema.declarations
    )


def load_from_string(
        source: str,
        schema_file: typing.Optional[str] = None,
) -> Schema:

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

    # pylint: disable=no-value-for-parameter
    declarations: typing.Sequence[typing.Union[TypeDeclaration, Attribute]]
    declarations = ft.compose(
        tuple,
        it.unique,
        it.concat,
        ft.curry(map)(op.attrgetter('declarations')),
        ft.curry(it.cons)(schema),
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

    schema = attr.evolve(
        schema,
        declarations=declarations
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
