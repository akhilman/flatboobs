# pylint: disable=missing-docstring
# pylint: disable=abstract-method
# pylint: disable=too-few-public-methods

from abc import abstractmethod

from typing import Dict, Generic, Optional, TypeVar

from flatboobs import abc, schema
from flatboobs.typing import UOffset, USize
from flatboobs.constants import BaseType


class Template:
    # pylint: disable=too-few-public-methods
    # pylint: disable=abstract-method

    type_decl: Optional[schema.TypeDeclaration]
    namespace: str
    type_name: str
    file_identifier: str
    value_type: BaseType
    value_pytype: Optional[type]
    inline_format: str
    inline_size: USize
    inline_align: USize


_TT = TypeVar('_TT', bound=Template)


class Container(Generic[_TT]):  # pylint: disable=unsubscriptable-object
    # pylint: disable=too-few-public-methods
    serializer: 'Serializer'
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

    @abstractmethod
    def __hash__(self):
        raise NotImplementedError


class Serializer(abc.Serializer):

    templates: Dict[schema.TypeDeclaration, Template]
