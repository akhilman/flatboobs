# pylint: disable=missing-docstring

from typing import Any

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
    lines = list()
    for n in range(0, len(buffer), 8):
        lines.append(f'{n:02x}\t'+''.join(f'{x:02x} ' for x in buffer[n:n+8]))
    return '\n'.join(lines)


def remove_prefix(prefix: str, text: str) -> str:
    return text[text.startswith(prefix) and len(prefix):]
