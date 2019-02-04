# pylint: disable=missing-docstring
# pylint: disable=invalid-name

from typing import NewType, Union, SupportsFloat, SupportsInt
from flatboobs.compat import numpy as np

Bool = bool
Float = SupportsFloat
Integer = SupportsInt
Number = Union[Float, Integer]

TemplateId = NewType('TemplateId', int)
UOffset = int
SOffset = int
VOffset = int
USize = int
VSize = int

Scalar = Union[Bool, Number, UOffset, SOffset, VOffset, USize, VSize]

if np:
    DType = np.dtype
    NDArray = np.ndarray
else:
    # dummy types
    DType = NewType('NDArray', None)  # type: ignore
    NDArray = NewType('NDArray', None)  # type: ignore
