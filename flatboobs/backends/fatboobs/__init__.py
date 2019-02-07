# pylint: disable=missing-docstring

from .backend import FatBoobs
from . import table  # NOQA


BACKEND = FatBoobs

__all__ = [
    'BACKEND',
    'FatBoobs'
]
