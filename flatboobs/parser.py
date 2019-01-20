# pylint: disable=missing-docstring  # TODO write docstrings

import operator
from typing import Optional

from parsy import regex, seq, string, success
from toolz import dicttoolz, functoolz, itertoolz

from flatboobs.schema import (
    Attribute,
    Enum,
    EnumMember,
    Field,
    MetadataMember,
    Schema,
    Struct,
    Table,
    Union,
    UnionMember
)
from flatboobs.util import unpack_kwargs

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
    regex(r'-?(0|[1-9][0-9]*)([.][0-9]+)([eE][+-]?[0-9]+)?')
).map(float)
SCALAR = INTEGER_CONST | BOOL_CONST | FLOAT_CONST | IDENT
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
SINGLE_VALUE = STRING_CONSTANT | SCALAR
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
ATTRIBUTE_DECL = seq(
    lexeme(string('attribute'))
    >> STRING_CONSTANT.tag('name')
    << SEMICOLON
).map(dict).tag('attribute')
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
        **dicttoolz.dissoc(v, 'type'),
        **v['type']
    }
)
TYPE_DECL = seq(
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
        (EQ >> SCALAR).optional().tag('value')
    ).map(dict).sep_by(COMMA)
    << RBRACE
)
ENUM_DECL = seq(
    lexeme(string('enum'))
    >> IDENT.tag('name'),
    (
        COLON
        >> IDENT
    ).optional().tag('type'),
    METADATA,
    ENUM_MEMBER_DECL.tag('members')
).map(dict).tag('enum')
UNION_MEMBER_DECL = (
    LBRACE
    >> seq(
        IDENT.tag('type'),
        (EQ >> SCALAR).optional().tag('value')
    ).map(dict).sep_by(COMMA)
    << RBRACE
)
UNION_DECL = seq(
    lexeme(string('union'))
    >> IDENT.tag('name'),
    METADATA,
    UNION_MEMBER_DECL.tag('members')
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
            | TYPE_DECL
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


def fix_metadata(kwargs):
    return dicttoolz.assoc(
        kwargs, 'metadata', tuple(
            map(unpack_kwargs(MetadataMember), kwargs['metadata'])
        )
    )


def fix_enum_values(enum, bit_flags=False):
    next_value = 1 if bit_flags else 0
    for member in enum:
        if member['value'] is None:
            value = next_value
        else:
            value = member['value']
        if value < next_value:
            raise ValueError(
                "Enum values must be specified in ascending order.")
        next_value = value + 1
        yield dicttoolz.assoc(member, 'value', value)


def fix_enum(kwargs):
    bit_flags = any(
        m['name'] == 'bit_flags' for m in kwargs['metadata']
    )
    return dicttoolz.assoc(
        kwargs, 'members', tuple(
            map(unpack_kwargs(EnumMember),
                fix_enum_values(kwargs['members'], bit_flags=bit_flags))
        )
    )


def fix_union(kwargs):
    return dicttoolz.assoc(
        kwargs, 'members', tuple(
            map(unpack_kwargs(UnionMember),
                fix_enum_values(kwargs['members']))
        )
    )


def fix_fields(kwargs):
    return dicttoolz.assoc(
        kwargs, 'fields', tuple(
            map(functoolz.compose(unpack_kwargs(Field), fix_metadata),
                kwargs['fields'])
        )
    )


def parse(source: str, schema_file: Optional[str] = None) -> Schema:

    keys_to_move = [
        'file_extension', 'file_identifier', 'namespace', 'root_type'
    ]

    # from pprint import pprint
    # pprint(SCHEMA.parse_partial(source))

    parsed = SCHEMA.parse(source)

    # add keys listed in keys_to_move dict root
    last_decl = dict(
        itertoolz.unique(
            filter(
                lambda v: v[0] in keys_to_move,
                reversed(
                    parsed['declarations']
                ),
            ),
            operator.itemgetter(0)
        ),
    )
    namespace = (tuple(last_decl['namespace'])
                 if 'namespace' in last_decl else None)
    file_identifier = last_decl.get('file_identifier', None)
    file_extension = last_decl.get('file_extension', 'bin')
    root_type = last_decl.get('root_type', None)

    includes = tuple(parsed.get('includes', []))

    # exclude keys_to_move from declarations
    declarations_gen = filter(
        lambda v: v[0] not in keys_to_move,
        parsed['declarations']
    )

    # add namespace
    declarations_gen = map(
        lambda x: (x[0], dicttoolz.assoc(x[1], 'namespace', namespace)),
        declarations_gen
    )

    # set is_root and identifier for root_type
    declarations_gen = map(
        lambda x: (x[0], (
            x[0] != 'attribute' and x[1]['name'] == root_type
            and dicttoolz.merge((
                x[1],
                {'is_root': True, 'identifier': file_identifier}
            ))
            or x[1]
        )),
        declarations_gen
    )

    # fix declarations
    declarations_gen = map(
        lambda x: {
            'attribute': unpack_kwargs(Attribute),
            'enum': functoolz.compose(
                unpack_kwargs(Enum), fix_metadata, fix_enum),
            'union': functoolz.compose(
                unpack_kwargs(Union), fix_metadata, fix_union),
            'struct': functoolz.compose(
                unpack_kwargs(Struct), fix_metadata, fix_fields),
            'table': functoolz.compose(
                unpack_kwargs(Table), fix_metadata, fix_fields)
        }[x[0]](x[1]),
        declarations_gen
    )

    # resolve generator
    declarations = tuple(declarations_gen)

    schema = Schema(
        includes=includes,
        namespace=namespace,
        declarations=declarations,
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
