# pylint: disable=missing-docstring

import enum
import struct
from typing import Dict, FrozenSet, NamedTuple

from flatboobs.typing import SOffset, UOffset, USize, VOffset, VSize

UNDEFINED = object()

FILE_IDENTIFIER_LENGTH = USize(4)
UOFFSET_FMT = 'I'
SOFFSET_FMT = 'i'
VOFFSET_FMT = 'H'
USIZE_FMT = 'I'
VSIZE_FMT = 'H'
UOFFSET_SIZE = UOffset(struct.calcsize(UOFFSET_FMT))
SOFFSET_SIZE = SOffset(struct.calcsize(SOFFSET_FMT))
VOFFSET_SIZE = VOffset(struct.calcsize(VOFFSET_FMT))
USIZE_SIZE = USize(struct.calcsize(USIZE_FMT))
VSIZE_SIZE = VSize(struct.calcsize(VSIZE_FMT))


BASE_TYPES: FrozenSet[str] = frozenset({
    'string',

    'bool',

    'int8',
    'int16',
    'int32',
    'int64',

    'uint8',
    'uint16',
    'uint32',
    'uint64',

    'float32',
    'float64',
})

BASE_TYPE_ALIASES: Dict[str, str] = {
    'byte': 'int8',
    'short': 'int16',
    'int': 'int32',
    'long': 'int64',

    'ubyte': 'uint8',
    'ushort': 'uint16',
    'uint': 'uint32',
    'ulong': 'uint64',

    'float': 'float32',
    'double': 'float64',
}

# TODO write tests for this constants / conversion


class BaseType(enum.IntEnum):

    NULL = 0

    BOOL = enum.auto()

    INT8 = enum.auto()
    INT16 = enum.auto()
    INT32 = enum.auto()
    INT64 = enum.auto()

    UINT8 = enum.auto()
    UINT16 = enum.auto()
    UINT32 = enum.auto()
    UINT64 = enum.auto()

    FLOAT32 = enum.auto()
    FLOAT64 = enum.auto()

    ENUM = enum.auto()
    STRING = enum.auto()
    STRUCT = enum.auto()
    TABLE = enum.auto()
    UNION = enum.auto()

    VOID = enum.auto()

    BYTE = INT8
    SHORT = INT16
    INT = INT32
    LONG = INT64

    UBYTE = UINT8
    USHORT = UINT16
    UINT = UINT32
    ULONG = UINT64

    FLOAT = FLOAT32
    DOUBLE = FLOAT64


SIGNED_INTEGER_TYPES: FrozenSet[BaseType] = frozenset({
    BaseType.INT8, BaseType.INT16,
    BaseType.INT32, BaseType.INT64,
})

UNSIGNED_INTEGER_TYPES: FrozenSet[BaseType] = frozenset({
    BaseType.UINT8, BaseType.UINT16,
    BaseType.UINT32, BaseType.UINT64,
})

INTEGER_TYPES: FrozenSet[BaseType] = (
    SIGNED_INTEGER_TYPES
    | UNSIGNED_INTEGER_TYPES
)

FLOAT_TYPES: FrozenSet[BaseType] = frozenset({
    BaseType.FLOAT32, BaseType.FLOAT64,
})

SCALAR_TYPES: FrozenSet[BaseType] = (
    INTEGER_TYPES
    | FLOAT_TYPES
    | {BaseType.BOOL}
)

STRING_TO_SCALAR_TYPE_MAP: Dict[str, BaseType] = {
    k.lower(): v for k, v in BaseType.__members__.items()
    if v in SCALAR_TYPES
}

FORMAT_MAP: Dict[BaseType, str] = {

    BaseType.BOOL: '?',

    BaseType.INT8: 'b',
    BaseType.UINT8: 'B',
    BaseType.INT16: 'h',
    BaseType.UINT16: 'H',
    BaseType.INT32: 'i',
    BaseType.UINT32: 'I',
    BaseType.INT64: 'q',
    BaseType.UINT64: 'Q',

    BaseType.FLOAT32: 'f',
    BaseType.FLOAT64: 'd',

    BaseType.STRING: UOFFSET_FMT,
    BaseType.STRUCT: UOFFSET_FMT,
    BaseType.TABLE: UOFFSET_FMT,
}

NBYTES_MAP: Dict[BaseType, USize] = {
    k: USize(struct.calcsize(v)) for k, v in FORMAT_MAP.items()
}


class _IntLimits(NamedTuple):
    min: int
    max: int


INTEGER_LIMITS: Dict[BaseType, _IntLimits] = {

    BaseType.INT8: _IntLimits(-0x80, 0x7F),
    BaseType.INT16: _IntLimits(-0x8000, 0x7FFF),
    BaseType.INT32: _IntLimits(-0x80000000, 0x7FFFFFFF),
    BaseType.INT64: _IntLimits(-0x8000000000000000, 0x7FFFFFFFFFFFFFFF),

    BaseType.UINT8: _IntLimits(0, 0xFF),
    BaseType.UINT16: _IntLimits(0, 0xFFFF),
    BaseType.UINT32: _IntLimits(0, 0xFFFFFFFF),
    BaseType.UINT64: _IntLimits(0, 0xFFFFFFFFFFFFFFFF),
}


PYTYPE_MAP: Dict[BaseType, type] = {
    BaseType.BOOL: bool,
    BaseType.INT8: int,
    BaseType.UINT8: int,
    BaseType.INT16: int,
    BaseType.UINT16: int,
    BaseType.INT32: int,
    BaseType.UINT32: int,
    BaseType.INT64: int,
    BaseType.UINT64: int,
    BaseType.FLOAT32: float,
    BaseType.FLOAT64: float,
    BaseType.STRING: str,
}
