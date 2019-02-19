# pylint: disable=missing-docstring

from struct import calcsize, unpack_from
from typing import Sequence, Tuple, cast

import attr

from flatboobs.typing import Scalar

from .constants import (
    FILE_IDENTIFIER_LENGTH,
    SOFFSET_FMT,
    UOFFSET_FMT,
    VOFFSET_FMT
)
from .typing import UOffset

FILE_HEADER_FMT = UOFFSET_FMT + f"{FILE_IDENTIFIER_LENGTH}s"


@attr.s(auto_attribs=True, frozen=True, slots=True)
class FileHeader:
    # pylint: disable=too-few-public-methods
    root_offset: UOffset
    file_identifier: str


def read_header(buffer: bytes) -> FileHeader:
    header = unpack_from(f"<{FILE_HEADER_FMT}", buffer, 0)
    return FileHeader(header[0], header[1].decode('ascii'))


def read_vtable(buffer: bytes, offset: int) -> Sequence[int]:
    vtable_offset = unpack_from(f"<{SOFFSET_FMT}", buffer, offset)[0]
    vtable_header = unpack_from(f"<2{VOFFSET_FMT}", buffer,
                                offset - vtable_offset)
    voffset_size = calcsize(VOFFSET_FMT)
    field_offsets = unpack_from(
        f"<{(vtable_header[0] // voffset_size - 2)}{VOFFSET_FMT}",
        buffer,
        offset - vtable_offset + voffset_size * 2
    )
    return field_offsets


def read_scalar(
        format_: str,
        buffer: bytes,
        offset: UOffset
) -> Scalar:

    return unpack_from(format_, buffer, offset)[0]


def read_struct(
        format_: str,
        buffer: bytes,
        offset: UOffset
) -> Tuple[Scalar, ...]:

    return cast(Tuple[Scalar, ...], unpack_from(format_, buffer, offset))
