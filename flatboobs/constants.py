import enum
import struct
from typing import Dict, FrozenSet, Optional
from flatboobs.typing import UOffset, SOffset, VOffset, USize, VSize

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
INT32_MAX = 0x7FFFFFFF


# TODO write tests for this constants / conversion
class BasicType(enum.IntEnum):
    VOID = 0
    BOOL = enum.auto()
    INT8 = enum.auto()
    UINT8 = enum.auto()
    INT16 = enum.auto()
    UINT16 = enum.auto()
    INT32 = enum.auto()
    UINT32 = enum.auto()
    INT64 = enum.auto()
    UINT64 = enum.auto()
    FLOAT32 = enum.auto()
    FLOAT64 = enum.auto()
    BYTE = INT8
    UBYTE = UINT8
    SHORT = INT16
    USHORT = UINT16
    INT = INT32
    UINT = UINT32
    LONG = INT64
    ULONG = UINT64
    FLOAT = FLOAT32
    DOUBLE = FLOAT64
    STRING = enum.auto()
    STRUCT = enum.auto()
    TABLE = enum.auto()
    UNION = enum.auto()


SCALAR_TYPES: FrozenSet[BasicType] = frozenset({
    BasicType.INT8, BasicType.INT16,
    BasicType.INT32, BasicType.INT64,
    BasicType.UINT8, BasicType.UINT16,
    BasicType.UINT32, BasicType.UINT64,
    BasicType.FLOAT32, BasicType.FLOAT64,
    BasicType.BOOL,
})

STRING_TO_TYPE_MAP: Dict[str, BasicType] = {
    k.lower(): v for k, v in BasicType.__members__.items()
    if v not in [BasicType.STRUCT, BasicType.TABLE,
                 BasicType.UNION, BasicType.VOID]
}


FORMAT_MAP: Dict[BasicType, str] = {
    BasicType.VOID: 'P',
    BasicType.BOOL: '?',
    BasicType.INT8: 'b',
    BasicType.UINT8: 'B',
    BasicType.INT16: 'h',
    BasicType.UINT16: 'H',
    BasicType.INT32: 'i',
    BasicType.UINT32: 'I',
    BasicType.INT64: 'q',
    BasicType.UINT64: 'Q',
    BasicType.FLOAT32: 'f',
    BasicType.FLOAT64: 'd',
    BasicType.STRING: UOFFSET_FMT,
    BasicType.STRUCT: UOFFSET_FMT,
    BasicType.TABLE: UOFFSET_FMT,
    BasicType.UNION: 'B',
}

NBYTES_MAP: Dict[BasicType, USize] = {
    k: USize(struct.calcsize(v)) for k, v in FORMAT_MAP.items()
}

PYTYPE_MAP: Dict[BasicType, Optional[type]] = {
    BasicType.VOID: None,
    BasicType.BOOL: bool,
    BasicType.INT8: int,
    BasicType.UINT8: int,
    BasicType.INT16: int,
    BasicType.UINT16: int,
    BasicType.INT32: int,
    BasicType.UINT32: int,
    BasicType.INT64: int,
    BasicType.UINT64: int,
    BasicType.FLOAT32: float,
    BasicType.FLOAT64: float,
    BasicType.STRING: str,
    BasicType.STRUCT: None,
    BasicType.TABLE: None,
    BasicType.UNION: None,
}
