# pylint: disable=missing-docstring

try:
    import numpy
except ImportError:
    numpy = None  # type: ignore


__all__ = [
    'numpy'
]
