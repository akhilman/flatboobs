# pylint: disable=missing-docstring

from typing import Any, Dict, Mapping, Optional, TypeVar

import attr

from flatboobs import abc, schema
from flatboobs.constants import (
    INTEGER_TYPES,
    STRING_TO_SCALAR_TYPE_MAP,
    BaseType
)

from . import reader
from .abc import Serializer, Template
from .table import Table
from .template import (
    EnumTemplate,
    ScalarTemplate,
    TableTemplate,
    UnionTemplate
)

_TT = TypeVar('_TT')  # Template type


class FatBoobs(Serializer):

    def __init__(self, registry: abc.Registry):

        self.registry = registry
        self.templates: Dict[schema.TypeDeclaration, Template] = dict()

    @staticmethod
    def _template_key(namespace: str, type_name: str) -> str:
        return f'{namespace}.{type_name}'

    def _add_enum_template(
            self: 'FatBoobs',
            type_decl: schema.Enum
    ) -> EnumTemplate:

        value_type = STRING_TO_SCALAR_TYPE_MAP.get(
            type_decl.type, BaseType.NULL)

        if value_type not in INTEGER_TYPES:
            raise TypeError(
                'Enum value type should be one of '
                f'{INTEGER_TYPES}, but {value_type or type_decl.type} is given'
            )

        pytype = type_decl.asenum()

        template = EnumTemplate(type_decl, value_type, pytype)
        self.templates[type_decl] = template

        template.finish()

        return template

    def _add_table_template(
            self: 'FatBoobs',
            type_decl: schema.Table,
    ) -> TableTemplate:

        value_template: Template

        template = TableTemplate(type_decl)
        self.templates[type_decl] = template

        for field in type_decl.fields:

            if 'deprecated' in field.metadata_map:
                template.add_depreacated_field()
                continue

            value_type = \
                STRING_TO_SCALAR_TYPE_MAP.get(field.type, BaseType.NULL)
            if value_type != BaseType.NULL:
                value_template = ScalarTemplate(value_type)
            else:
                value_type_decl = self.registry.type_by_name(
                    field.type, type_decl.namespace)
                value_template = self._get_add_template(value_type_decl)

            if isinstance(value_template, UnionTemplate):
                enum_field = attr.evolve(
                    field,
                    name=f'{field.name}_type',
                    type=value_template.enum_template.type_name,
                    default=0
                )
                template.add_field(enum_field, value_template.enum_template)

            template.add_field(field, value_template)

        template.finish()

        return template

    def _add_struct_template(
            self: 'FatBoobs',
            type_decl: schema.Struct,
    ) -> TableTemplate:

        raise NotImplementedError

    def _add_union_template(
            self: 'FatBoobs',
            type_decl: schema.Union,
    ) -> UnionTemplate:

        pytype = type_decl.asenum()

        enum_template = EnumTemplate(type_decl, BaseType.UBYTE, pytype)
        enum_template.finish()

        union_template = UnionTemplate(type_decl, enum_template)
        self.templates[type_decl] = union_template

        for member in type_decl.members:

            value_type_decl = self.registry.type_by_name(
                member.name, type_decl.namespace)
            value_template = self._get_add_template(value_type_decl)
            assert isinstance(value_template, TableTemplate)

            enum_value = int(pytype.__members__[member.name])
            union_template.add_member(enum_value, value_template)

        union_template.finish()

        return union_template

    def _get_add_template(
            self: 'FatBoobs',
            type_decl: schema.TypeDeclaration
    ) -> Template:

        if type_decl in self.templates:
            return self.templates[type_decl]

        template: Template
        if isinstance(type_decl, schema.Struct):
            template = self._add_struct_template(type_decl)
        elif isinstance(type_decl, schema.Table):
            template = self._add_table_template(type_decl)
        elif isinstance(type_decl, schema.Union):
            template = self._add_union_template(type_decl)
        elif isinstance(type_decl, schema.Enum):
            template = self._add_enum_template(type_decl)

        return template

    def new(
            self: 'FatBoobs',
            type_name: str,
            mutation: Optional[Mapping[str, Any]] = None,
            *,
            namespace: Optional[str] = None
    ) -> Table:

        type_decl = self.registry.type_by_name(type_name, namespace)
        assert isinstance(type_decl, schema.Table)
        template = self._get_add_template(type_decl)
        assert isinstance(template, TableTemplate)

        mutation = mutation or dict()
        if not isinstance(mutation, dict):
            raise TypeError(f"Mutation should be dict, {mutation} is given")
        return Table.new(
            self, template, None, 0, mutation
        )

    def unpackb(
            self: 'FatBoobs',
            type_name: Optional[str],
            buffer: bytes,
            *,
            namespace: Optional[str] = None
    ) -> abc.Container:

        header = reader.read_header(buffer)

        if type_name:
            type_decl = self.registry.type_by_name(type_name, namespace)
        elif header.file_identifier:
            type_decl = self.registry.type_by_identifier(
                header.file_identifier, namespace)
        else:
            raise TypeError(
                'Nor file idenitifer nor type_name is defined.')

        template = self._get_add_template(type_decl)
        assert isinstance(template, TableTemplate)

        return Table.new(
            self, template, buffer, header.root_offset, dict()
        )

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
        return table.packb()
