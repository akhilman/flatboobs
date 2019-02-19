# pylint: disable=missing-docstring
# pylint: disable=abstract-method
# pylint: disable=too-few-public-methods

from abc import abstractmethod
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from flatboobs import abc, schema
from flatboobs.constants import BaseType
from flatboobs.typing import UOffset, USize


class Skeleton:
    # pylint: disable=too-few-public-methods
    # pylint: disable=abstract-method

    type_decl: Optional[schema.TypeDeclaration]
    namespace: str
    type_name: str
    file_identifier: str
    value_type: BaseType
    value_factory: Callable[..., Any]
    inline_format: str
    inline_size: USize
    inline_align: USize


_ST = TypeVar('_ST', bound=Skeleton)


class Container(Generic[_ST]):  # pylint: disable=unsubscriptable-object
    # pylint: disable=too-few-public-methods
    serializer: 'Serializer'
    skeleton: _ST
    buffer: Optional[bytes] = None
    offset: UOffset = 0

    @property
    def namespace(self: 'Container') -> str:
        return self.skeleton.namespace

    @property
    def type_name(self: 'Container') -> str:
        return self.skeleton.type_name

    @property
    def file_identifier(self: 'Container') -> str:
        return self.skeleton.file_identifier

    def __eq__(self, other):
        return hash(self) == hash(other)

    @abstractmethod
    def __hash__(self):
        raise NotImplementedError


class Serializer(abc.Serializer):

    skeletons: Dict[schema.TypeDeclaration, Skeleton]
