# pylint: disable=missing-docstring

from typing import Any

from .abc import Struct, Table


def apply(func, args):
    return func(*args)


def applykw(func, kwargs):
    return func(**kwargs)


def asdict(something: Any) -> Any:

    if isinstance(something, (Struct, Table)):
        return {k: asdict(v) for k, v in something.items()}

    return something
