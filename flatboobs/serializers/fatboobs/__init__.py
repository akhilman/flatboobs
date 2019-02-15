# pylint: disable=missing-docstring

from .serializer import FatBoobs
from . import table  # NOQA


BACKEND = FatBoobs

__all__ = [
    'BACKEND',
    'FatBoobs'
]
