"""
Abstract classes to define API
"""

import enum
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

import numpy as np

import flatboobs.schema
from flatboobs.constants import BaseType
from flatboobs.typing import Number, Scalar, TemplateId, UOffset

# pylint: disable=abstract-method
# pylint: disable=too-few-public-methods
# pylint: disable=missing-docstring


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
_ST = TypeVar(
    '_ST',
    flatboobs.schema.Enum,
    flatboobs.schema.Struct,
    flatboobs.schema.Table,
    flatboobs.schema.Union,
    None
)  # type declaration schema type of container, None for numbers and strings


class Container(Generic[_CT, _ST], ABC):

    @property
    @abstractmethod
    def enums(self: 'Container') -> Mapping[str, enum.Enum]:
        pass

    @property
    @abstractmethod
    def schema(self: 'Container') -> _ST:
        pass

    @abstractmethod
    def packb(self: 'Container') -> bytes:
        pass


class _TableLike(Container[_CT, _ST], Mapping[str, Any]):
    dtype: np.dtype

    @abstractmethod
    def evolve(
            self: '_TableLike',
            **kwargs: Mapping[str, Any]
    ) -> _CT:
        pass


class Table(_TableLike['Table', flatboobs.schema.Table]):
    pass


class Struct(_TableLike['Struct', flatboobs.schema.Struct]):
    pass


_IT = TypeVar(
    '_IT',
    Number,
    Struct,
    Table,
    str,
    covariant=True
)  # generic vector item


class _Vector(Container[_CT, _ST], Sequence[_IT]):
    dtype: np.dtype

    @abstractmethod
    def evolve(
            self: '_Vector',
            arr: Union[Iterable[_IT], np.ndarray]
    ) -> _CT:
        pass


class VectorOfNumbers(_Vector['VectorOfNumbers', None, Number]):
    pass


class VectorOfStrings(_Vector['VectorOfStrings', None, str]):
    pass


class VectorOfStructs(
        _Vector['VectorOfStructs', flatboobs.schema.Struct, Struct]):
    pass


class VectorOfTables(_Vector['VectorOfTables', flatboobs.schema.Table, Table]):
    pass


####
# Backend
##


class FileHeader(ABC):
    root_offset: UOffset
    file_identifier: str


class Template(ABC, Generic[_ST]):

    id: TemplateId
    schema: _ST

    @abstractmethod
    def finish(self: 'Template') -> TemplateId:
        pass


class EnumTemplate(Template[flatboobs.schema.Enum]):

    @abstractmethod
    def add_member(
            self: 'EnumTemplate',
            name: str,
            value: int
    ) -> None:
        pass


class StructTemplate(Template[flatboobs.schema.Struct]):

    @abstractmethod
    def add_scalar_field(
            self: 'StructTemplate',
            name: str,
            is_vector: bool,
            value_type: BaseType,
            default: Scalar,
    ) -> None:
        pass


class TableTemplate(Template[flatboobs.schema.Table]):

    @abstractmethod
    def add_depreacated_field(
            self: 'TableTemplate',
    ) -> None:
        pass

    @abstractmethod
    def add_scalar_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_type: BaseType,
            default: Scalar,
    ) -> None:
        pass

    @abstractmethod
    def add_string_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
    ) -> None:
        pass

    @abstractmethod
    def add_struct_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template: TemplateId,
    ) -> None:
        pass

    @abstractmethod
    def add_table_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template: TemplateId,
    ) -> None:
        pass

    @abstractmethod
    def add_enum_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template: TemplateId,
            default: int,
    ) -> None:
        pass

    @abstractmethod
    def add_union_field(
            self: 'TableTemplate',
            name: str,
            value_template: TemplateId,
    ) -> None:
        pass


class UnionTemplate(Template[flatboobs.schema.Union]):

    @abstractmethod
    def add_member(
            self: 'UnionTemplate',
            variant_id: enum.IntEnum,
            value_template: TemplateId,
    ) -> None:
        pass


class Backend(ABC):

    @abstractmethod
    def read_header(
            self: 'Backend',
            buffer: bytes
    ) -> FileHeader:
        pass

    @abstractmethod
    def new_enum_template(
            self: 'Backend',
            type_decl: flatboobs.schema.Enum,
            value_type: BaseType,
            bit_flags: bool,
    ) -> EnumTemplate:
        pass

    @abstractmethod
    def new_struct_template(
            self: 'Backend',
            type_decl: flatboobs.schema.Struct,
    ) -> StructTemplate:
        pass

    @abstractmethod
    def new_table_template(
            self: 'Backend',
            type_decl: flatboobs.schema.Table
    ) -> TableTemplate:
        pass

    @abstractmethod
    def new_union_template(
            self: 'Backend',
            type_decl: flatboobs.schema.Union
    ) -> UnionTemplate:
        pass

    @abstractmethod
    def get_template_id(
            self: 'Backend',
            type_decl: flatboobs.schema.TypeDeclaration
    ) -> TemplateId:
        """
        -1 if template not exist
        """

    @abstractmethod
    def new_container(
            self: 'Backend',
            template_id: TemplateId,
            buffer: Optional[bytes] = None,
            offset: UOffset = UOffset(0),
            mutation: Optional[Mapping[str, Any]] = None
    ) -> Container:
        pass
