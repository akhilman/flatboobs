# pylint: disable=missing-docstring  # TODO write docstrings

import operator
from pathlib import Path
from typing import Optional

from frozendict import frozendict
from parsy import regex, seq, string, success
from toolz import dicttoolz, itertoolz

from flatboobs.schema import (
    Attribute,
    Enum,
    Field,
    Schema,
    Struct,
    Table,
    Union
)

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
SCALAR = lexeme(
    regex(r'-?(0|[1-9][0-9]*)([.][0-9]+)?([eE][+-]?[0-9]+)?')
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
IDENT = lexeme(regex(r'[a-zA-Z_]\w*'))
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
).map(lambda v: {'name': v}).tag('attribute')
METADATA = (
    (
        LPAR >> seq(
            IDENT,
            (COLON >> SINGLE_VALUE) | success(True)
        ).sep_by(COMMA).map(frozendict)
        << RPAR
    )
    | success({})
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
ENUMVAL_DECL = (
    LBRACE
    >> seq(
        IDENT,
        (
            EQ >> SCALAR
        ).optional()
    ).sep_by(COMMA)
    << RBRACE
).tag('members')
ENUM_DECL = seq(
    lexeme(string('enum'))
    >> IDENT.tag('name'),
    (
        COLON
        >> IDENT
    ).optional().tag('type'),
    METADATA,
    ENUMVAL_DECL
).map(dict).tag('enum')
UNION_DECL = seq(
    lexeme(string('union'))
    >> IDENT.tag('name'),
    METADATA,
    ENUMVAL_DECL
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


def parse(source: str, file_path: Optional[Path] = None) -> Schema:

    # from pprint import pprint
    # pprint(SCHEMA.parse_partial(source))

    parsed = SCHEMA.parse(source)
    keys_to_move = [
        'file_extension', 'file_identifier', 'namespace', 'root_type'
    ]

    def type_factory(args):
        type_, kwargs = args
        if type_ in ['struct', 'table']:
            kwargs = dicttoolz.assoc(
                kwargs, 'fields',
                tuple(map(Field, kwargs['fields']))
            )
        return {
            'attribute': Attribute,
            'enum': Enum,
            'union': Union,
            'struct': Struct,
            'table': Table,
        }[type_](**kwargs)

    kwargs = dicttoolz.merge(
        parsed,
        {
            'declarations': tuple(
                map(
                    type_factory,
                    filter(
                        lambda v: v[0] not in keys_to_move,
                        parsed['declarations'],
                    )
                )

            ),
            'file_path': file_path
        },
        dict(
            itertoolz.unique(
                filter(
                    lambda v: v[0] in keys_to_move,
                    reversed(
                        parsed['declarations']
                    ),
                ),
                operator.itemgetter(0)
            )
        )
    )
    schema = Schema(**kwargs)

    return schema


def parse_file(file_path: Path):

    src = file_path.read_text()
    schema = parse(src, file_path)

    return schema
