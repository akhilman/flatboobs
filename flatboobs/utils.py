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
