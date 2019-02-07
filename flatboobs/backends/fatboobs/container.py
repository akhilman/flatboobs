# pylint: disable=missing-docstring

from typing import Optional, TypeVar, Generic

from flatboobs.typing import UOffset
from .template import Template
from .backend import FatBoobs

_TT = TypeVar('_TT', bound=Template)


class Container(Generic[_TT]):  # pylint: disable=unsubscriptable-object
    # pylint: disable=too-few-public-methods
    backend: FatBoobs
    template: _TT
    buffer: Optional[bytes] = None
    offset: UOffset = 0

    @property
    def namespace(self: 'Container') -> str:
        return self.template.namespace

    @property
    def type_name(self: 'Container') -> str:
        return self.template.type_name

    @property
    def file_identifier(self: 'Container') -> str:
        return self.template.file_identifier

    def __hash__(self):
        return id(self)
