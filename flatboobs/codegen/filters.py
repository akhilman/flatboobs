# pylint: disable=missing-docstring

import re
from pathlib import Path
from typing import Union

import toolz.itertoolz as it

from flatboobs.idl import BaseType  # type: ignore

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
    BaseType.NONE: "uint8_t",
    BaseType.UTYPE: "uint8_t",
    BaseType.BOOL: "uint8_t",
    BaseType.CHAR: "int8_t",
    BaseType.UCHAR: "uint8_t",
    BaseType.SHORT: "int16_t",
    BaseType.USHORT: "uint16_t",
    BaseType.INT: "int32_t",
    BaseType.UINT: "uint32_t",
    BaseType.LONG: "int64_t",
    BaseType.ULONG: "uint64_t",
    BaseType.FLOAT: "float",
    BaseType.DOUBLE: "double",
}


def escape_cpp_keyward(txt: str) -> str:
    if txt in CPP_KEYWORDS:
        return txt + '_'
    return txt


def escape_python_keyward(txt: str) -> str:
    if txt in PYTHON_KEYWORDS:
        return txt + '_'
    return txt


def include_guard(fname: Union[str, Path]) -> str:
    guard: str = Path(fname).stem
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


def to_cpp_type(type_: BaseType) -> str:
    return CPP_TYPES[type_]


FILTERS = {
    'include_guard': include_guard,
    'escape_cpp_keyword': escape_cpp_keyward,
    'escape_python_keyword': escape_python_keyward,
    'basename': basename,
    'dirname': dirname,
    'relative_path': relative_path,
    'with_suffix': with_suffix,
    'stem': stem,
    'to_cpp_type': to_cpp_type,
    'concat': it.concat,
}
