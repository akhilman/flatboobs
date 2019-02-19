# pylint: disable=missing-docstring

import struct
from functools import reduce
from typing import Any, Dict, List, Mapping, Tuple

import toolz.functoolz as ft
import toolz.itertoolz as it
from multipledispatch import Dispatcher

from flatboobs.constants import FILE_IDENTIFIER_LENGTH

from .abc import Container
from .constants import UOFFSET_FMT, UOFFSET_SIZE, USIZE_SIZE
from .typing import UOffset, USize

# Callable[[int, Container], Generator[Container, None, None]]
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
) -> UOffset:

    ident = file_identifier.encode()[:FILE_IDENTIFIER_LENGTH]

    format_ = ''
    values: List[Any] = []
    if ident:
        format_ = f'{FILE_IDENTIFIER_LENGTH}s{format_}'
        cursor += FILE_IDENTIFIER_LENGTH
        values = [ident, *values]

    format_ = f'{UOFFSET_FMT}{format_}'
    cursor += UOFFSET_SIZE
    cursor += -cursor % 8
    values = [cursor - root_offset, *values]

    assert cursor <= len(buffer)

    struct.pack_into(
        format_,
        buffer,
        len(buffer) - cursor,
        *values,
    )
    return cursor


def build(content: Container) -> bytes:

    max_recursion = 100
    blocks = ft.compose(
        list,
        it.unique,
        ft.partial(flatten, max_recursion),
    )(content)

    size: USize = reduce(calc_size, blocks, 0)
    print('calc size:', size)
    size += -size % 8
    size += FILE_IDENTIFIER_LENGTH
    size += UOFFSET_SIZE

    buffer = bytearray(size)
    offset_map: Dict[int, UOffset] = {}

    cursor: UOffset = 0
    for block in blocks:
        cursor, offset = write(
            buffer, cursor, offset_map, block)
        offset_map[hash(block)] = offset

    print('cursor:', cursor)

    file_identifier = content.skeleton.file_identifier
    cursor = write_header(
        buffer, offset_map[hash(content)], file_identifier, cursor)

    buffer = buffer[-cursor:]

    return buffer
