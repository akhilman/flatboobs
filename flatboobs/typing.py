# pylint: disable=missing-docstring
# pylint: disable=invalid-name

from typing import NewType, Union, SupportsFloat, SupportsInt
from flatboobs.compat import numpy as np

Bool = bool
Float = SupportsFloat
Integer = SupportsInt
Number = Union[Float, Integer]
Scalar = Union[Bool, Number]

if np:
    DType = np.dtype
    NDArray = np.ndarray
else:
    # dummy types
    DType = NewType('NDArray', None)  # type: ignore
    NDArray = NewType('NDArray', None)  # type: ignore
