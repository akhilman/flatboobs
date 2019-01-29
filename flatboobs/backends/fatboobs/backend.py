# pylint: disable=missing-docstring

import itertools
from typing import Any, Dict, Iterator, Mapping, Optional, Type, TypeVar

from flatboobs import abc, schema
from flatboobs.constants import BasicType
from flatboobs.typing import TemplateId, UOffset

from . import reader, table


_T = TypeVar('_T')


class FatBoobs(abc.Backend):

    def __init__(self):

        self._template_ids: Dict[str, TemplateId] = dict()
        self._templates: Dict[TemplateId, abc.Template] = dict()
        self._template_count: Iterator[TemplateId] = itertools.count()

    @staticmethod
    def _template_key(type_decl: schema.TypeDeclaration) -> str:
        return f'{type_decl.namespace}.{type_decl.name}'

    def _new_template(
            self: 'FatBoobs',
            factory: Type[_T],
            type_decl: schema.TypeDeclaration,
            *args,
            **kwargs
    ) -> _T:
        template_id = next(self._template_count)
        template = factory(  # type: ignore
            self, template_id, type_decl, *args, **kwargs)
        key = self._template_key(type_decl)
        self._template_ids[key] = template_id
        self._templates[template_id] = template  # type: ignore
        return template

    def read_header(
            self: 'FatBoobs',
            buffer: bytes
    ) -> abc.FileHeader:
        return reader.read_header(buffer)

    def get_template_id(
            self: 'FatBoobs',
            type_decl: schema.TypeDeclaration
    ) -> TemplateId:
        key = self._template_key(type_decl)
        template_id = self._template_ids.get(key, TemplateId(-1))
        return template_id

    def new_enum_template(
            self: 'FatBoobs',
            type_decl: schema.Enum,
            value_type: BasicType,
            bit_flags: bool
    ) -> abc.EnumTemplate:
        raise NotImplementedError

    def new_struct_template(
            self: 'FatBoobs',
            type_decl: schema.Struct
    ) -> abc.StructTemplate:
        raise NotImplementedError

    def new_table_template(
            self: 'FatBoobs',
            type_decl: schema.Table
    ) -> table.TableTemplate:
        return self._new_template(
            table.TableTemplate,
            type_decl
        )

    def new_union_template(
            self: 'FatBoobs',
            type_decl: schema.Union
    ) -> abc.UnionTemplate:
        raise NotImplementedError

    def new_container(
            self: 'FatBoobs',
            template_id: TemplateId,
            buffer: Optional[bytes] = None,
            offset: UOffset = 0,
            mutation: Optional[Mapping[str, Any]] = None
    ) -> abc.Container:
        template = self._templates[template_id]
        if isinstance(template, table.TableTemplate):
            return table.Table(
                buffer=buffer,
                offset=offset,
                template=template,
                mutation=mutation
            )
        raise NotImplementedError
