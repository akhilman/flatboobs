# pylint: disable=missing-docstring

import re
from pathlib import Path
from typing import Sequence, Set, Union

import toolz.itertoolz as it

from flatboobs import idl  # type: ignore

CPP_KEYWORDS = {
    "alignas",
    "alignof",
    "and",
    "and_eq",
    "asm",
    "atomic_cancel",
    "atomic_commit",
    "atomic_noexcept",
    "auto",
    "bitand",
    "bitor",
    "bool",
    "break",
    "case",
    "catch",
    "char",
    "char16_t",
    "char32_t",
    "class",
    "compl",
    "concept",
    "const",
    "constexpr",
    "const_cast",
    "continue",
    "co_await",
    "co_return",
    "co_yield",
    "decltype",
    "default",
    "delete",
    "do",
    "double",
    "dynamic_cast",
    "else",
    "enum",
    "explicit",
    "export",
    "extern",
    "false",
    "float",
    "for",
    "friend",
    "goto",
    "if",
    "import",
    "inline",
    "int",
    "long",
    "module",
    "mutable",
    "namespace",
    "new",
    "noexcept",
    "not",
    "not_eq",
    "nullptr",
    "operator",
    "or",
    "or_eq",
    "private",
    "protected",
    "public",
    "register",
    "reinterpret_cast",
    "requires",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "static_assert",
    "static_cast",
    "struct",
    "switch",
    "synchronized",
    "template",
    "this",
    "thread_local",
    "throw",
    "true",
    "try",
    "typedef",
    "typeid",
    "typename",
    "union",
    "unsigned",
    "using",
    "virtual",
    "void",
    "volatile",
    "wchar_t",
    "while",
    "xor",
    "xor_eq",
}

PYTHON_KEYWORDS = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}

CPP_TYPES = {
    idl.BaseType.NONE: "uint8_t",
    idl.BaseType.UTYPE: "uint8_t",
    idl.BaseType.BOOL: "uint8_t",
    idl.BaseType.CHAR: "int8_t",
    idl.BaseType.UCHAR: "uint8_t",
    idl.BaseType.SHORT: "int16_t",
    idl.BaseType.USHORT: "uint16_t",
    idl.BaseType.INT: "int32_t",
    idl.BaseType.UINT: "uint32_t",
    idl.BaseType.LONG: "int64_t",
    idl.BaseType.ULONG: "uint64_t",
    idl.BaseType.FLOAT: "float",
    idl.BaseType.DOUBLE: "double",
}


def escape_keyword(
        txt: str,
        keywords: Union[Sequence[str], Set[str]] = tuple(),
) -> str:
    if txt in set(keywords):
        return txt + '_'
    return txt


def escape_cpp_keyword(
        txt: str,
) -> str:
    return escape_keyword(txt, CPP_KEYWORDS)


def escape_python_keyword(
        txt: str,
) -> str:
    return escape_keyword(txt, PYTHON_KEYWORDS)


def include_guard(fname: Union[str, Path]) -> str:
    guard: str = Path(fname).name
    guard = re.sub(r'[^\w]', '_', guard)
    guard = f'FLATBOOBS_GENERATED_{guard.upper()}_'
    return guard


def basename(fname: Union[str, Path]) -> str:
    return Path(fname).name


def dirname(fname: Union[str, Path]) -> Path:
    return Path(fname).parent


def relative_path(fname: Union[str, Path], other: Union[str, Path]) -> Path:
    fname_path = Path(fname).resolve()
    other_path = Path(other).resolve()
    if other_path.is_file():
        other_path = other_path.parent
    return fname_path.relative_to(other_path)


def with_suffix(fname: Union[str, Path], suffix: str) -> Path:
    return Path(fname).with_suffix(suffix)


def stem(fname: Union[str, Path]) -> str:
    return Path(fname).stem


def to_cpp_enum(src: Union[str, int], enum_def: idl.EnumDef) -> str:
    value = int(src)
    result = []
    if 'bit_flags' in enum_def.attributes:
        for enum_value in enum_def.values:
            if value & enum_value.value:
                result.append('::'.join([
                    *enum_def.defined_namespace.components,
                    escape_cpp_keyword(enum_def.name),
                    escape_cpp_keyword(enum_value.name),
                ]))
        if not result:
            result.append('::'.join([
                *enum_def.defined_namespace.components,
                escape_cpp_keyword(enum_def.name),
                "NONE"
            ]))
    else:
        for enum_value in enum_def.values:
            if value == enum_value.value:
                result.append('::'.join([
                    *enum_def.defined_namespace.components,
                    escape_cpp_keyword(enum_def.name),
                    escape_cpp_keyword(enum_value.name),
                ]))
        if not result:
            result.append('::'.join([
                *enum_def.defined_namespace.components,
                escape_cpp_keyword(enum_def.name),
                escape_cpp_keyword(enum_def.values[0].name)
            ]))
    return '|'.join(result)


def to_cpp_type(
        type_: idl.Type,
        const=False,
        no_namespace=False,
        no_enum=False,
        no_pointer=False,
) -> str:
    base_type = type_.base_type
    definition = type_.definition
    if isinstance(definition, idl.EnumDef) and not no_enum:
        type_str = definition.name
        if not no_namespace:
            type_str = '::'.join(
                [*definition.defined_namespace.components, type_str])
        if const:
            type_str = f'const {type_str}'
    elif base_type in CPP_TYPES:  # base types
        type_str = CPP_TYPES[type_.base_type]
        if const:
            type_str = f'const {type_str}'
    else:
        raise NotImplementedError('Oops!')
    return type_str


def quote(txt: str) -> str:
    return f'"{txt}"'


FILTERS = {
    'include_guard': include_guard,
    'escape_keyword': escape_keyword,
    'escape_cpp_keyword': escape_cpp_keyword,
    'escape_python_keyword': escape_python_keyword,
    'basename': basename,
    'dirname': dirname,
    'relative_path': relative_path,
    'with_suffix': with_suffix,
    'stem': stem,
    'to_cpp_enum': to_cpp_enum,
    'to_cpp_type': to_cpp_type,
    'concat': it.concat,
    'quote': quote,
}
