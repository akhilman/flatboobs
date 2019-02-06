# pylint: disable=missing-docstring

import struct
from functools import reduce
from typing import Dict, Mapping, Tuple

import toolz.functoolz as ft
import toolz.itertoolz as it
from multipledispatch import Dispatcher

from flatboobs.constants import (
    FILE_IDENTIFIER_LENGTH,
    UOFFSET_FMT,
    UOFFSET_SIZE,
    USIZE_SIZE
)
from flatboobs.typing import UOffset, USize

from .container import Container


# Callable[[Container], Generator[Container, None, None]]
flatten = Dispatcher(f'{__name__}.flatten')  # pylint: disable=invalid-name

# Callable[[USize, Container], USize]
calc_size = Dispatcher(f'{__name__}.calc_size')  # pylint: disable=invalid-name

# Callable[[bytearray, UOffset, Mapping[int, UOffset], Container],
#          Tuple[UOffset, UOffset]]
write = Dispatcher(f'{__name__}.write')  # pylint: disable=invalid-name


@calc_size.register(int, str)
def calc_string_size(size: USize, string: str) -> USize:
    size = size + len(string) + 1
    size += -size % USIZE_SIZE
    size += USIZE_SIZE

    return size


@write.register(bytearray, int, dict, str)
def write_string(
        buffer: bytearray,
        cursor: UOffset,
        offset_map: Mapping[int, UOffset],
        content: str
) -> Tuple[UOffset, UOffset]:
    raise NotImplementedError


def write_header(
        buffer: bytearray,
        root_offset: UOffset,
        file_identifier: str,
        cursor: UOffset,
) -> None:

    ident = file_identifier.encode()[:FILE_IDENTIFIER_LENGTH]

    # print(ident, type(ident))
    # print('cursor', len(buffer) - cursor)
    # print('root_offset', root_offset, len(buffer) - root_offset)

    struct.pack_into(
        f'{UOFFSET_FMT}{FILE_IDENTIFIER_LENGTH}s',
        buffer,
        len(buffer) - cursor,
        len(buffer) - root_offset,
        ident
    )


def build(content: Container) -> bytes:

    blocks = ft.compose(
        list,
        it.unique,
        flatten,
    )(content)

    size: USize = reduce(calc_size, blocks, 0)
    size += FILE_IDENTIFIER_LENGTH
    size += -size % UOFFSET_SIZE
    size += UOFFSET_SIZE

    buffer = bytearray(size)
    offset_map: Dict[int, UOffset] = {}

    cursor: UOffset = 0
    for block in blocks:
        cursor, offset = write(
            buffer, cursor, offset_map, block)
        offset_map[hash(block)] = offset
        cursor += 1

    cursor = len(buffer)

    root_block = blocks[-1]
    if isinstance(root_block, Container):
        file_identifier = root_block.template.file_identifier
    else:
        file_identifier = ''
    write_header(
        buffer, offset_map[hash(root_block)], file_identifier, cursor)

    return buffer
