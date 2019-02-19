# pylint: disable=missing-docstring

import enum
import struct
from typing import Dict, FrozenSet

from .typing import SOffset, UOffset, USize, VOffset, VSize


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
