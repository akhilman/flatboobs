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

from flatboobs.constants import BaseType
from flatboobs.typing import (
    DType,
    NDArray,
    Number,
    Scalar,
    TemplateId,
    UOffset
)

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
# Backend
##


class FileHeader(ABC):
    root_offset: UOffset
    file_identifier: str


class Template(ABC):

    id: TemplateId
    namespace: str
    type_name: str
    file_identifier: str  # empty string if no file identifier

    @abstractmethod
    def finish(self: 'Template') -> TemplateId:
        pass


class EnumTemplate(Template):

    @abstractmethod
    def add_member(
            self: 'EnumTemplate',
            name: str,
            value: int
    ) -> None:
        pass


class StructTemplate(Template):

    @abstractmethod
    def add_scalar_field(
            self: 'StructTemplate',
            name: str,
            is_vector: bool,
            value_type: BaseType,
            default: Scalar,
    ) -> None:
        pass


class TableTemplate(Template):

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
            value_template_id: TemplateId,
    ) -> None:
        pass

    @abstractmethod
    def add_table_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template_id: TemplateId,
    ) -> None:
        pass

    @abstractmethod
    def add_enum_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template_id: TemplateId,
            default: int,
    ) -> None:
        pass

    @abstractmethod
    def add_union_field(
            self: 'TableTemplate',
            name: str,
            value_template_id: TemplateId,
    ) -> None:
        pass


class UnionTemplate(Template):

    @abstractmethod
    def add_member(
            self: 'UnionTemplate',
            name: str,
            variant_id: int,
            value_template_id: TemplateId,
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
            # pylint: disable=too-many-arguments
            self: 'Backend',
            namespace: str,
            type_name: str,
            file_identifier: str,
            value_type: BaseType,
            bit_flags: bool,
    ) -> EnumTemplate:
        pass

    @abstractmethod
    def new_struct_template(
            self: 'Backend',
            namespace: str,
            type_name: str,
            file_identifier: str
    ) -> StructTemplate:
        pass

    @abstractmethod
    def new_table_template(
            self: 'Backend',
            namespace: str,
            type_name: str,
            file_identifier: str
    ) -> TableTemplate:
        pass

    @abstractmethod
    def new_union_template(
            self: 'Backend',
            namespace: str,
            type_name: str,
            file_identifier: str
    ) -> UnionTemplate:
        pass

    @abstractmethod
    def get_template_id(
            self: 'Backend',
            namespace: str,
            type_name: str,
    ) -> TemplateId:
        """
        0 if template not exist
        """

    @abstractmethod
    def new_table(
            self: 'Backend',
            template_id: TemplateId,
            buffer: Optional[bytes] = None,
            offset: UOffset = UOffset(0),
            mutation: Optional[Mapping[str, Any]] = None
    ) -> Container:
        pass
