# pylint: disable=missing-docstring

from typing import NewType, Union

import numpy as np

Bool = Union[bool, np.bool, np.bool8]
Float = Union[float, np.floating]
Integer = Union[int, np.integer]
Number = Union[Float, Integer]

TemplateId = NewType('TemplateId', int)
UOffset = int
SOffset = int
VOffset = int
USize = int
VSize = int

Scalar = Union[Bool, Number, UOffset, SOffset, VOffset, USize, VSize]
