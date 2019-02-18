# pylint: disable=missing-docstring
from flatboobs.about import __version__
from flatboobs.registry import Registry
from flatboobs.utils import asnative
from flatboobs.serializers.fatboobs import FatBoobs

FlatBuffers = FatBoobs

__all__ = [
    'FatBoobs',
    'FlatBuffers',
    'Registry',
    '__version__',
    'asnative',
]
