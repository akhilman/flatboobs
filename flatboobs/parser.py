# pylint: disable=missing-docstring  # TODO write docstrings

from typing import Optional

from parsy import regex, seq, string, success
from toolz import dicttoolz as dt
from toolz import functoolz as ft
from toolz import itertoolz as it

from flatboobs.schema import (
    Enum,
    EnumMember,
    Field,
    MetadataMember,
    Schema,
    Struct,
    Table,
    Union
)
from flatboobs.util import applykw

WHITESPACE = regex(r'\s*')
COMMENT = regex(r'\s*//.*\s*').many()


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
SINGLE_VALUE = FLOAT_CONST | INTEGER_CONST | BOOL_CONST | STRING_CONSTANT
VALUE = (
    SINGLE_VALUE
    # | OBJECT  # TODO add object tag
    # | (
    #     LBRACK
    #     >> VALUE.sep_by(COMMA)  # TODO add value list recursion
    #     << RBRACK
    # )

)
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
            map(ft.curry(applykw)(MetadataMember), kwargs['metadata'])
        )
    )


def make_enum_members(enum, start_value):
    next_value = start_value
    for member in enum:
        if member['value'] is None:
            value = next_value
        else:
            value = member['value']
        if value < next_value:
            raise ValueError(
                "Enum values must be specified in ascending order.")
        next_value = value + 1
        yield dt.assoc(member, 'value', value)


def make_enum(kwargs, union=False):
    if union or any(m['name'] == 'bit_flags' for m in kwargs['metadata']):
        start_value = 1
    else:
        start_value = 0
    kwargs = dt.assoc(kwargs, 'type', kwargs.get('type', 'byte'))
    return dt.assoc(
        kwargs, 'members', tuple(
            map(ft.curry(applykw)(EnumMember),
                make_enum_members(kwargs['members'], start_value))
        )
    )


def make_union(kwargs):
    return make_enum(kwargs, union=True)


def make_fields(kwargs):
    return dt.assoc(
        kwargs, 'fields', tuple(
            map(
                ft.compose(
                    ft.curry(applykw)(Field),
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
                ft.curry(applykw)(Enum), make_metadata, make_enum),
            'union': ft.compose(
                ft.curry(applykw)(Union), make_metadata, make_union),
            'struct': ft.compose(
                ft.curry(applykw)(Struct), make_metadata, make_fields),
            'table': ft.compose(
                ft.curry(applykw)(Table), make_metadata, make_fields)
        }[x[0]](x[1]),
        types_gen
    )

def _get_last_decl(declarations, key, default=None):
    # pylint: disable=no-value-for-parameter
    return ft.compose(
        it.first,
        it.partial(ft.flip(it.concatv), [default]),
        ft.curry(map)(ft.partial(it.get, 1)),
        ft.curry(filter)(lambda x: x[0] == key),
        reversed,
    )(declarations)


def parse(source: str, schema_file: Optional[str] = None) -> Schema:

    # from pprint import pprint
    # pprint(SCHEMA.parse_partial(source))

    parsed = SCHEMA.parse(source)

    declarations = parsed['declarations']

    includes = frozenset(parsed.get('includes', []))

    namespace = '.'.join(_get_last_decl(declarations, 'namespace', ['']))
    file_identifier = _get_last_decl(declarations, 'file_identifier', None)
    file_identifier = _get_last_decl(declarations, 'file_identifier', None)
    file_extension = _get_last_decl(declarations, 'file_extension', 'bin')
    root_type = _get_last_decl(declarations, 'root_type', None)

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

    schema = Schema(
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
