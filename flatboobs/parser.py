# pylint: disable=missing-docstring  # TODO write docstrings

import importlib.resources
import operator as op
import pathlib
from typing import Any, Callable, FrozenSet, Iterator, Optional, Union

import attr
from parsy import ParseError, line_info_at, regex, seq, string, success
from toolz import dicttoolz as dt
from toolz import functoolz as ft
from toolz import itertoolz as it

import flatboobs.schema as s
from flatboobs import logging
from flatboobs.constants import FILE_IDENTIFIER_LENGTH
from flatboobs.utils import applykw

WHITESPACE = regex(r'\s*')
COMMENT = regex(r'\s*//.*\s*').many()

logger = logging.getLogger('flatboobs')


def lexeme(parser):
    return parser << WHITESPACE << COMMENT

# TODO implement flatbuffer objects
# OBJECT = (
#     LBRACE
#     >> seq(
#         IDENT
#         << COLON,
#         VALUE
#     )
# )


EQ = lexeme(string("="))
LBRACE = lexeme(string('{'))
RBRACE = lexeme(string('}'))
LBRACK = lexeme(string('['))
RBRACK = lexeme(string(']'))
LPAR = lexeme(string('('))
RPAR = lexeme(string(')'))
COLON = lexeme(string(':'))
COMMA = lexeme(string(','))
PERIOD = lexeme(string('.'))
SEMICOLON = lexeme(string(';'))
IDENT = lexeme(regex(r'[a-zA-Z_]\w*'))
INTEGER_CONST = lexeme(regex(r'-?[0-9]+')).map(int)
BOOL_CONST = lexeme(
    string('true') >> success(True)
    | string('false') >> success(False)
)
FLOAT_CONST = lexeme(
    regex(
        r'-?(0|[1-9][0-9]*)'
        r'('
        r'([.][0-9]+)?([eE][+-]?[0-9]+)'
        r')|('
        r'([.][0-9]+)([eE][+-]?[0-9]+)?'
        r')'
    )
).map(float)
STRING_PART = regex(r'[^"\\]+')
STRING_ESC = string('\\') >> (
    string('\\')
    | string('/')
    | string('"')
    | string('b').result('\b')
    | string('f').result('\f')
    | string('n').result('\n')
    | string('r').result('\r')
    | string('t').result('\t')
    | regex(r'u[0-9a-fA-F]{4}').map(lambda s: chr(int(s[1:], 16)))
)
STRING_CONSTANT = (
    lexeme(
        string('"')
        >> (STRING_PART | STRING_ESC).many().concat()
        << string('"')
    )
)
SINGLE_VALUE = (
    FLOAT_CONST
    | INTEGER_CONST
    | BOOL_CONST
    | STRING_CONSTANT
    | IDENT
)
# VALUE = (
#     SINGLE_VALUE
#     | OBJECT  # TODO add object tag
#     | (
#         LBRACK
#         >> VALUE.sep_by(COMMA)  # TODO add value list recursion
#         << RBRACK
#     )
#
# )
TYPE = (
    seq(
        IDENT.tag('type'),
        success(False).tag('is_vector')
    )
    | seq(
        LBRACK
        >> IDENT.tag('type')
        << RBRACK,
        success(True).tag('is_vector')
    )
).map(dict)

INCLUDE = (
    lexeme(string('include'))
    >> STRING_CONSTANT
    << SEMICOLON
)
NAMESPACE_DECL = (
    lexeme(string('namespace'))
    >> IDENT.sep_by(PERIOD, min=1)
    << SEMICOLON
).tag('namespace')
ATTRIBUTE_DECL = (
    lexeme(string('attribute'))
    >> STRING_CONSTANT
    << SEMICOLON
).tag('attribute')
METADATA = (
    (
        LPAR >> seq(
            IDENT.tag('name'),
            ((COLON >> SINGLE_VALUE) | success(True)).tag('value')
        ).map(dict).sep_by(COMMA)
        << RPAR
    )
    | success(list())
).tag('metadata')
FIELD_DECL = seq(
    IDENT.tag('name'),
    COLON
    >> TYPE.tag('type'),
    (EQ >> SINGLE_VALUE).optional().tag('default'),
    METADATA
    << SEMICOLON
).map(dict).map(
    lambda v: {
        **dt.dissoc(v, 'type'),
        **v['type']
    }
)
TABLE_LIKE_DECL = seq(
    lexeme(
        string('struct')
        | string('table')
    ),
    seq(
        IDENT.tag('name'),
        METADATA,
        LBRACE
        >> FIELD_DECL.at_least(1).tag('fields')
        << RBRACE
    ).map(dict)
)
ENUM_MEMBER_DECL = (
    LBRACE
    >> seq(
        IDENT.tag('name'),
        (EQ >> (INTEGER_CONST | IDENT)).optional().tag('value')
    ).map(dict).sep_by(COMMA)
    << RBRACE
)
ENUM_DECL = seq(
    lexeme(string('enum'))
    >> IDENT.tag('name'),
    (
        COLON
        >> IDENT
    ).tag('type'),
    METADATA,
    ENUM_MEMBER_DECL.tag('members')
).map(dict).tag('enum')
UNION_DECL = seq(
    lexeme(string('union'))
    >> IDENT.tag('name'),
    METADATA,
    ENUM_MEMBER_DECL.tag('members')
).map(dict).tag('union')
ROOT_DECL = (
    lexeme(string('root_type'))
    >> IDENT
    << SEMICOLON
).tag('root_type')
FILE_EXTENSION_DECL = (
    lexeme(string('file_extension'))
    >> STRING_CONSTANT
    << SEMICOLON
).tag('file_extension')
FILE_IDENTIFIER_DECL = (
    lexeme(string('file_identifier'))
    >> STRING_CONSTANT
    << SEMICOLON
).tag('file_identifier')


SCHEMA = (
    WHITESPACE
    >> COMMENT
    >> seq(
        (
            INCLUDE
        ).many().tag('includes'),
        (
            NAMESPACE_DECL
            | ATTRIBUTE_DECL
            | TABLE_LIKE_DECL
            | ENUM_DECL
            | UNION_DECL
            | ROOT_DECL
            | FILE_EXTENSION_DECL
            | FILE_IDENTIFIER_DECL
            # | RPC_DECL  # TODO add rpc tag
            # | OBJECT  # TODO add object tag
        ).many().tag('declarations')
    ).map(dict)
)


def make_metadata(kwargs):
    return dt.assoc(
        kwargs, 'metadata', tuple(
            map(ft.curry(applykw)(s.MetadataMember), kwargs['metadata'])
        )
    )


def make_enum_members(members, start_value, bit_flags):
    next_value = start_value
    for member in members:
        if member['value'] is None:
            value = next_value
        else:
            value = member['value']
        if value < next_value:
            raise ValueError(
                "Enum values must be specified in ascending order.")
        next_value = value + 1
        if bit_flags:
            value = 1 << value
        yield dt.assoc(member, 'value', value)


def make_enum(kwargs, union=False):
    bit_flags = any(m['name'] == 'bit_flags' and m['value']
                    for m in kwargs['metadata'])
    start_value = 1 if union else 0
    kwargs = dt.assoc(kwargs, 'type', kwargs.get('type', 'byte'))
    return dt.assoc(
        kwargs, 'members', tuple(
            map(ft.curry(applykw)(s.EnumMember),
                make_enum_members(kwargs['members'], start_value, bit_flags))
        )
    )


def make_union(kwargs):
    return make_enum(kwargs, union=True)


def make_fields(kwargs):
    return dt.assoc(
        kwargs, 'fields', tuple(
            map(
                ft.compose(
                    ft.curry(applykw)(s.Field),
                    make_metadata
                ),
                kwargs['fields']
            )
        )
    )


def make_types(types_gen):
    return map(
        lambda x: {
            'enum': ft.compose(
                ft.curry(applykw)(s.Enum), make_metadata, make_enum),
            'union': ft.compose(
                ft.curry(applykw)(s.Union), make_metadata, make_union),
            'struct': ft.compose(
                ft.curry(applykw)(s.Struct), make_metadata, make_fields),
            'table': ft.compose(
                ft.curry(applykw)(s.Table), make_metadata, make_fields)
        }[x[0]](x[1]),
        types_gen
    )


def get_last_decl(declarations, key, default=None):
    # pylint: disable=no-value-for-parameter
    return ft.compose(
        it.first,
        it.partial(ft.flip(it.concatv), [default]),
        ft.curry(map)(ft.partial(it.get, 1)),
        ft.curry(filter)(lambda x: x[0] == key),
        reversed,
    )(declarations)


def log_parse_error(
        exc: ParseError,
        schema_file: Optional[str] = None
) -> None:
    line_n, char_n = line_info_at(exc.stream, exc.index)
    lines = exc.stream.split('\n')
    error_msg = [f'Can not parse schema from "{schema_file}"']
    error_msg.extend(lines[max(0, line_n-4):line_n+1])
    error_msg.append(' ' * char_n + '^')
    error_msg.append(str(exc))
    logger.error('\n'.join(error_msg))


def parse(source: str, schema_file: Optional[str] = None) -> s.Schema:

    try:
        parsed = SCHEMA.parse(source)
    except ParseError as exc:
        log_parse_error(exc)
        raise

    declarations = parsed['declarations']

    includes = frozenset(parsed.get('includes', []))

    namespace = '.'.join(get_last_decl(declarations, 'namespace', ['']))
    file_identifier = get_last_decl(declarations, 'file_identifier', None)
    file_identifier = get_last_decl(declarations, 'file_identifier', None)
    file_extension = get_last_decl(declarations, 'file_extension', 'bin')
    root_type = get_last_decl(declarations, 'root_type', None)

    # check file_identifier
    # TODO move to schema validator
    if file_identifier and len(file_identifier) != FILE_IDENTIFIER_LENGTH:
        raise ValueError('File identifier must be '
                         f'{FILE_IDENTIFIER_LENGTH} characters long.')

    # attributes
    attributes = ft.compose(
        frozenset,
        ft.curry(map)(ft.partial(it.get, 1)),
        ft.curry(filter)(lambda v: v[0] == 'attribute'),
    )(declarations)

    # get type declarations
    type_tags = ['enum', 'struct', 'table', 'union']
    types_gen = filter(
        lambda v: v[0] in type_tags,
        declarations
    )

    # add namespace
    types_gen = map(
        lambda x: (x[0], dt.assoc(x[1], 'namespace', namespace)),
        types_gen
    )

    # set is_root and identifier for root_type
    types_gen = map(
        lambda x: (x[0], (
            x[0] != 'attribute' and x[1]['name'] == root_type
            and dt.merge((
                x[1],
                {'is_root': True, 'file_identifier': file_identifier}
            ))
            or x[1]
        )),
        types_gen
    )

    # make schema for declaratons
    types = frozenset(make_types(types_gen))

    schema = s.Schema(
        includes=includes,
        namespace=namespace,
        attributes=attributes,
        types=types,
        root_type=root_type,
        file_identifier=file_identifier,
        file_extension=file_extension,
        schema_file=schema_file,
    )

    # from pprint import pprint
    # pprint(schema)
    # import attr
    # pprint(attr.asdict(schema))

    return schema


def load_from_string(
        source: str,
        schema_file: Optional[str] = None,
) -> s.Schema:

    schema = parse(source, schema_file=schema_file)
    return schema


def load_with_includes(
        join_path: Callable[[Any, str], str],
        read: Callable[[Any, str], str],
        visited: FrozenSet[str],
        package: Any,
        resource: str,

) -> Optional[s.Schema]:

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
            ft.partial(load_with_includes,
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
    types: FrozenSet[s.TypeDeclaration]
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
        fpath: Union[pathlib.Path, str],
) -> s.Schema:

    if not isinstance(fpath, pathlib.Path):
        fpath = pathlib.Path(fpath)

    logger.debug('Loading schema from %s', fpath)

    schema = load_with_includes(
        lambda p, r: str(p / r),
        lambda p, r: (p / r).read_text(),
        frozenset(),
        fpath.parent,
        fpath.name,
    )

    assert schema

    return schema


def load_from_directory(
        path: Union[pathlib.Path, str],
        suffix: str = '.fbs'
) -> Iterator[s.Schema]:

    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    return map(
        load_from_file,
        path.glob(f'*{suffix}')
    )


def load_from_package(
        package: str,
        suffix: str = '.fbs'
) -> Iterator[s.Schema]:

    for name in importlib.resources.contents(package):
        if not name.endswith(suffix):
            continue
        logger.debug('Loading schema from %s/%s', package, name)
        schema = load_with_includes(
            lambda p, r: f'{p}/{r}',
            importlib.resources.read_text,
            frozenset(),
            package,
            name,
        )
        if schema:
            yield schema
