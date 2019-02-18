"""
Abstract classes to define API
"""

from abc import ABC, abstractmethod
from typing import (
    Any,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union
)

from flatboobs.typing import (
    DType,
    NDArray,
    Number,
)
from flatboobs.schema import TypeDeclaration

# pylint: disable=abstract-method
# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring


####
# Registry
##

class Registry(ABC):

    @abstractmethod
    def type_by_name(
            self: 'Registry',
            type_name: str,
            namespace: Optional[str] = None
    ) -> TypeDeclaration:
        pass

    @abstractmethod
    def type_by_identifier(
            self: 'Registry',
            file_identifier: str,
            namespace: Optional[str] = None
    ) -> TypeDeclaration:
        pass


####
# Container
##

_CT = TypeVar(
    '_CT',
    'Table',
    'Struct',
    'VectorOfNumbers',
    'VectorOfStrings',
    'VectorOfStructs',
    'VectorOfTables',
    covariant=True
)  # container type for `self`


class Container(Generic[_CT], ABC):

    @property
    @abstractmethod
    def namespace(self: 'Container') -> str:
        pass

    @property
    @abstractmethod
    def type_name(self: 'Container') -> str:
        pass

    @property
    @abstractmethod
    def file_identifier(self: 'Container') -> str:
        pass

    @abstractmethod
    def packb(self: 'Container') -> bytes:
        pass


class _TableLike(Container[_CT], Mapping[str, Any]):

    @property
    @abstractmethod
    def dtype(
            self: '_TableLike',
    ) -> DType:
        pass

    @abstractmethod
    def evolve(
            self: '_TableLike',
            **kwargs: Mapping[str, Any]
    ) -> _CT:
        pass


class Table(_TableLike['Table']):
    pass


class Struct(_TableLike['Struct']):
    pass


_IT = TypeVar(
    '_IT',
    Number,
    Struct,
    Table,
    str,
    covariant=True
)  # generic vector item


class _Vector(Container[_CT], Sequence[_IT]):

    @property
    @abstractmethod
    def dtype(
            self: '_Vector',
    ) -> DType:
        pass

    @abstractmethod
    def evolve(
            self: '_Vector',
            arr: Union[Iterable[_IT], NDArray]
    ) -> _CT:
        pass


class VectorOfNumbers(_Vector['VectorOfNumbers', Number]):
    pass


class VectorOfStrings(_Vector['VectorOfStrings', str]):
    pass


class VectorOfStructs(
        _Vector['VectorOfStructs', Struct]):
    pass


class VectorOfTables(_Vector['VectorOfTables', Table]):
    pass


####
# Serializer
##


class Serializer(ABC):

    registry: Registry

    @abstractmethod
    def new(
            self: 'Serializer',
            type_name: str,
            mutation: Optional[Mapping[str, Any]] = None,
            *,
            namespace: str = ''
    ) -> Table:
        pass
