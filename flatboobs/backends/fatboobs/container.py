# pylint: disable=missing-docstring

from typing import Optional, TypeVar, Generic

from flatboobs.typing import UOffset
from .template import Template

_TT = TypeVar('_TT', bound=Template)


class Container(Generic[_TT]):  # pylint: disable=unsubscriptable-object
    # pylint: disable=too-few-public-methods
    template: _TT
    buffer: Optional[bytes] = None
    offset: UOffset = 0

    def __hash__(self):
        return id(self)
