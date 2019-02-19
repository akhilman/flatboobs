# pylint: disable=missing-docstring

from typing import Any, Dict, Mapping, Optional, TypeVar, Union

import attr

from flatboobs import abc, schema

from . import reader
from .abc import Container, Serializer, Skeleton
from .constants import INTEGER_TYPES, STRING_TO_SCALAR_TYPE_MAP, BaseType
from .skeleton import (
    EnumSkeleton,
    ScalarSkeleton,
    StringSkeleton,
    StructSkeleton,
    TableSkeleton,
    UnionSkeleton
)
from .struct import Struct
from .table import Table
from .typing import UOffset

_TT = TypeVar('_TT')  # Skeleton type


class FatBoobs(Serializer):

    def __init__(self, registry: abc.Registry):

        self.registry = registry
        self.skeletons: Dict[schema.TypeDeclaration, Skeleton] = dict()

    @staticmethod
    def _skeleton_key(namespace: str, type_name: str) -> str:
        return f'{namespace}.{type_name}'

    def _add_enum_skeleton(
            self: 'FatBoobs',
            type_decl: schema.Enum
    ) -> EnumSkeleton:

        value_type = STRING_TO_SCALAR_TYPE_MAP.get(
            type_decl.type, BaseType.NULL)

        if value_type not in INTEGER_TYPES:
            raise TypeError(
                'Enum value type should be one of '
                f'{INTEGER_TYPES}, but {value_type or type_decl.type} is given'
            )

        pytype = type_decl.asenum()
        bit_flags = type_decl.metadata_map.get('bit_flags', False)

        skeleton = EnumSkeleton(type_decl, value_type, bit_flags, pytype)
        self.skeletons[type_decl] = skeleton

        skeleton.finish()

        return skeleton

    def _add_scalar_skeleton(
            self: 'FatBoobs',
            type_decl: schema.Scalar,
    ) -> ScalarSkeleton:
        type_ = STRING_TO_SCALAR_TYPE_MAP[type_decl.name]
        skeleton = ScalarSkeleton(type_decl, type_)
        self.skeletons[type_decl] = skeleton
        return skeleton

    def _add_string_skeleton(
            self: 'FatBoobs',
            type_decl: schema.String,
    ) -> StringSkeleton:
        skeleton = StringSkeleton(type_decl)
        self.skeletons[type_decl] = skeleton
        return skeleton

    def _add_table_skeleton(
            self: 'FatBoobs',
            type_decl: schema.Table,
    ) -> TableSkeleton:

        value_skeleton: Skeleton

        skeleton = TableSkeleton(type_decl)
        self.skeletons[type_decl] = skeleton

        for field in type_decl.fields:

            if field.metadata_map.get('deprecated', False):
                skeleton.add_depreacated_field()
                continue

            value_type_decl = self.registry.type_by_name(
                field.type, type_decl.namespace)
            value_skeleton = self._get_add_skeleton(value_type_decl)

            if isinstance(value_skeleton, UnionSkeleton):
                enum_field = attr.evolve(
                    field,
                    name=f'{field.name}_type',
                    type=value_skeleton.enum_skeleton.type_name,
                    default=0
                )
                skeleton.add_field(enum_field, value_skeleton.enum_skeleton)

            skeleton.add_field(field, value_skeleton)

        skeleton.finish()

        return skeleton

    def _add_struct_skeleton(
            self: 'FatBoobs',
            type_decl: schema.Struct,
    ) -> StructSkeleton:

        value_skeleton: Skeleton
        skeleton = StructSkeleton(type_decl)
        self.skeletons[type_decl] = skeleton

        for field in type_decl.fields:

            assert not field.is_vector

            value_type_decl = self.registry.type_by_name(
                field.type, type_decl.namespace)
            if not isinstance(value_type_decl, (schema.Scalar, schema.Enum)):
                raise TypeError(
                    f'Struct "{type_decl.name}" field "{field.name}" type '
                    f'could not be {field.type}, '
                    'only floats, integers, bools and enums are allowed'
                )
            some_value_skeleton = self._get_add_skeleton(value_type_decl)
            assert isinstance(some_value_skeleton,
                              (ScalarSkeleton, EnumSkeleton))
            value_skeleton = some_value_skeleton

            skeleton.add_field(field, value_skeleton)

        skeleton.finish()

        return skeleton

    def _add_union_skeleton(
            self: 'FatBoobs',
            type_decl: schema.Union,
    ) -> UnionSkeleton:

        pytype = type_decl.asenum()

        enum_skeleton = EnumSkeleton(type_decl, BaseType.UBYTE, False, pytype)
        enum_skeleton.finish()

        union_skeleton = UnionSkeleton(type_decl, enum_skeleton)
        self.skeletons[type_decl] = union_skeleton

        for member in type_decl.members:

            value_type_decl = self.registry.type_by_name(
                member.name, type_decl.namespace)
            value_skeleton = self._get_add_skeleton(value_type_decl)
            assert isinstance(value_skeleton, TableSkeleton)

            enum_value = int(pytype.__members__[member.name])
            union_skeleton.add_member(enum_value, value_skeleton)

        union_skeleton.finish()

        return union_skeleton

    def _get_add_skeleton(
            self: 'FatBoobs',
            type_decl: schema.TypeDeclaration
    ) -> Skeleton:

        if type_decl in self.skeletons:
            return self.skeletons[type_decl]

        skeleton: Skeleton
        if isinstance(type_decl, schema.Scalar):
            skeleton = self._add_scalar_skeleton(type_decl)
        elif isinstance(type_decl, schema.String):
            skeleton = self._add_string_skeleton(type_decl)
        elif isinstance(type_decl, schema.Struct):
            skeleton = self._add_struct_skeleton(type_decl)
        elif isinstance(type_decl, schema.Table):
            skeleton = self._add_table_skeleton(type_decl)
        elif isinstance(type_decl, schema.Union):
            skeleton = self._add_union_skeleton(type_decl)
        elif isinstance(type_decl, schema.Enum):
            skeleton = self._add_enum_skeleton(type_decl)
        else:
            raise NotImplementedError('Unsupported type')

        assert skeleton

        self.skeletons[type_decl] = skeleton

        return skeleton

    def _new_container(
            self: 'FatBoobs',
            skeleton: Skeleton,
            buffer: Optional[bytes],
            offset: UOffset,
            mutation: Any
    ) -> Union[Table, Struct]:
        """
        Internal routine, Use FatBoobs.new().
        """
        if isinstance(skeleton, TableSkeleton):
            return Table.new(self, skeleton, buffer, offset, mutation)
        if isinstance(skeleton, StructSkeleton):
            return Struct.new(self, skeleton, buffer, offset, mutation)
        raise NotImplementedError(
            'Unsupported skeleton type {skeleton.__class__.__name__}')

    def _new_vector_container(
            self: 'FatBoobs',
            skeleton: Skeleton,
            buffer: Optional[bytes],
            offset: UOffset,
            mutation: Any
    ) -> Container:
        """
        Internal routine, Use FatBoobs.new().
        """
        raise NotImplementedError

    def new(
            self: 'FatBoobs',
            type_name: str,
            mutation: Any = None,
            *,
            namespace: Optional[str] = None
    ) -> Union[Table, Struct]:

        type_decl = self.registry.type_by_name(type_name, namespace)
        skeleton = self._get_add_skeleton(type_decl)

        return self._new_container(skeleton, None, 0, mutation)

    def unpackb(
            self: 'FatBoobs',
            type_name: Optional[str],
            buffer: bytes,
            *,
            namespace: Optional[str] = None
    ) -> Table:

        header = reader.read_header(buffer)

        if type_name:
            type_decl = self.registry.type_by_name(type_name, namespace)
        elif header.file_identifier:
            type_decl = self.registry.type_by_identifier(
                header.file_identifier, namespace)
        else:
            raise TypeError(
                'Nor file idenitifer nor type_name is defined.')

        skeleton = self._get_add_skeleton(type_decl)
        assert isinstance(skeleton, TableSkeleton)

        table = self._new_container(
            skeleton, buffer, header.root_offset, dict()
        )
        assert isinstance(table, Table)
        return table

    def packb(
            self: 'FatBoobs',
            type_name: str,
            mutation: Optional[Mapping[str, Any]] = None,
            *,
            namespace: Optional[str] = None
    ) -> bytes:

        table = self.new(
            type_name,
            mutation=mutation,
            namespace=namespace,
        )
        assert isinstance(table, Table)
        return table.packb()
