# pylint: disable=missing-docstring

import re
from pathlib import Path
from typing import Any, Mapping, Sequence, Set, Union

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

KEYWORDS = CPP_KEYWORDS | PYTHON_KEYWORDS

CPP_TYPES = {
    idl.BaseType.NONE: "uint8_t",
    idl.BaseType.UTYPE: "uint8_t",
    idl.BaseType.BOOL: "bool",
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
        keywords: Union[Sequence, Set] = KEYWORDS
) -> str:
    if any(map(lambda x: re.match(r'^'+x+r'_*$', txt), set(keywords))):
        return txt + '_'
    return txt


def include_guard(fname: Union[str, Path]) -> str:
    guard: str = Path(fname).name
    guard = re.sub(r'[^\w]', '_', guard)
    guard = f'FLATBOOBS_GENERATED_{guard.upper()}_'
    return guard


def quote(txt: str) -> str:
    return f'"{txt}"'


# Path related

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


def filters(
        output_dir: Path,
        options: Mapping[str, Any]
):
    # pylint: disable=unused-argument
    return {
        'concat': it.concat,
        'escape_keyword': escape_keyword,
        'include_guard': include_guard,
        'quote': quote,
        # path related
        'basename': basename,
        'dirname': dirname,
        'relative_path': relative_path,
        'stem': stem,
        'with_suffix': with_suffix,
    }
