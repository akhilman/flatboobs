# pylint: disable=missing-docstring
import itertools
import string
from typing import Any

import toolz.functoolz as ft
import toolz.itertoolz as it

from .abc import Struct, Table


def apply(func, args):
    return func(*args)


def applykw(func, kwargs):
    return func(**kwargs)


def asnative(something: Any) -> Any:
    """
    Recursively onverts FlatBoobs containers to native python objects
    like dict, list, tuple, int, float, bool and str.
    Result by default compatible with flatc's JSON.
    """

    if isinstance(something, (Struct, Table)):
        return {k: asnative(v) for k, v in something.items()}

    return something


def hexdump(buffer: bytes) -> str:

    printable = string.ascii_letters + string.digits

    def format_hex(values):
        return ''.join(f'{x:02x} ' for x in values)

    def format_chr(values):
        return ''.join(chr(x) if chr(x) in printable else '.'
                       for x in values)

    def format_line(line_n, values):
        return '{:04x}   {:<52} {:<19}'.format(
            line_n * 16,
            ' '.join(map(format_hex, values)),
            ' '.join(map(format_chr, values))
        )

    return ft.compose(
        '\n'.join,
        ft.curry(map)(
            lambda x, cnt=itertools.count(): format_line(next(cnt), x)),
        ft.partial(it.partition_all, 4),
        ft.partial(it.partition_all, 4),
    )(buffer)


def remove_prefix(prefix: str, text: str) -> str:
    return text[text.startswith(prefix) and len(prefix):]
