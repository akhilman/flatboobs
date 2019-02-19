# pylint: disable=missing-docstring

from typing import Dict, FrozenSet

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
