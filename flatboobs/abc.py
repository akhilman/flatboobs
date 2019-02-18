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
    Tuple,
    TypeVar,
    Union
)

from flatboobs.schema import TypeDeclaration
from flatboobs.typing import DType, NDArray, Number, Scalar

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


class _NumpyCompatible(ABC):

    @property
    @abstractmethod
    def dtype(
            self: '_NumpyCompatible',
    ) -> DType:
        pass

    @abstractmethod
    def asarray(
            self: '_NumpyCompatible',
    ) -> NDArray:
        pass

    @abstractmethod
    def asbytes(
            self: '_NumpyCompatible',
    ) -> bytes:
        pass


class Table(_TableLike['Table']):
    pass


class Struct(
        _NumpyCompatible,
        _TableLike['Struct']
):

    @abstractmethod
    def astuple(
            self: 'Struct',
    ) -> Tuple[Scalar, ...]:
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

    @abstractmethod
    def evolve(
            self: '_Vector',
            arr: Union[Iterable[_IT], NDArray]
    ) -> _CT:
        pass


class VectorOfNumbers(
        _NumpyCompatible,
        _Vector['VectorOfNumbers', Number]
):
    pass


class VectorOfStrings(_Vector['VectorOfStrings', str]):
    pass


class VectorOfStructs(
        _NumpyCompatible,
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
            namespace: Optional[str] = None
    ) -> Table:
        pass

    def unpackb(
            self: 'Serializer',
            type_name: Optional[str],
            buffer: bytes,
            *,
            namespace: Optional[str] = None
    ) -> Container:
        """
        If type_name is None, then type will be detected by file_identifier
        in message itself.
        """

    def packb(
            self: 'Serializer',
            type_name: str,
            mutation: Optional[Mapping[str, Any]] = None,
            *,
            namespace: Optional[str] = None
    ) -> bytes:
        pass

    loads = unpackb
    dumps = packb
