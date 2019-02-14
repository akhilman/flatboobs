# pylint: disable=missing-docstring

import itertools
from typing import Any, Dict, Iterator, Mapping, Optional, Type, TypeVar

from flatboobs import abc
from flatboobs.constants import BaseType
from flatboobs.typing import TemplateId, UOffset

from . import reader
from .abc import Backend, Template
from .table import Table
from .template import EnumTemplate, TableTemplate, UnionTemplate

_TT = TypeVar('_TT')  # Template type


class FatBoobs(Backend):

    def __init__(self):

        self.template_ids: Dict[str, TemplateId] = dict()
        self.templates: Dict[TemplateId, Template] = dict()
        self._template_count: Iterator[TemplateId] = itertools.count(1)

    @staticmethod
    def _template_key(namespace: str, type_name: str) -> str:
        return f'{namespace}.{type_name}'

    def _new_template(
            self: 'FatBoobs',
            factory: Type[_TT],
            namespace: str,
            type_name: str,
            file_identifier: str,
            *args,
            **kwargs
    ) -> _TT:
        template_id = next(self._template_count)
        template = factory(  # type: ignore
            self, template_id, namespace, type_name, file_identifier,
            *args, **kwargs
        )
        key = self._template_key(namespace, type_name)
        self.template_ids[key] = template_id
        self.templates[template_id] = template  # type: ignore
        return template

    @staticmethod
    def read_header(
            buffer: bytes
    ) -> abc.FileHeader:
        return reader.read_header(buffer)

    def get_template_id(
            self: 'FatBoobs',
            namespace: str,
            type_name: str,
    ) -> TemplateId:
        key = self._template_key(namespace, type_name)
        template_id = self.template_ids.get(key, TemplateId(0))
        return template_id

    def new_enum_template(
            # pylint: disable=too-many-arguments
            self: 'FatBoobs',
            namespace: str,
            type_name: str,
            file_identifier: str,
            value_type: BaseType,
            bit_flags: bool
    ) -> abc.EnumTemplate:
        return self._new_template(
            EnumTemplate,
            namespace,
            type_name,
            file_identifier,
            value_type,
            bit_flags
        )

    def new_struct_template(
            self: 'FatBoobs',
            namespace: str,
            type_name: str,
            file_identifier: str
    ) -> abc.StructTemplate:
        raise NotImplementedError

    def new_table_template(
            self: 'FatBoobs',
            namespace: str,
            type_name: str,
            file_identifier: str
    ) -> TableTemplate:
        return self._new_template(
            TableTemplate,
            namespace,
            type_name,
            file_identifier
        )

    def new_union_template(
            self: 'FatBoobs',
            namespace: str,
            type_name: str,
            file_identifier: str
    ) -> abc.UnionTemplate:
        return self._new_template(
            UnionTemplate,
            namespace,
            type_name,
            file_identifier,
        )

    def new_table(
            self: 'FatBoobs',
            template_id: TemplateId,
            buffer: Optional[bytes] = None,
            offset: UOffset = 0,
            mutation: Optional[Mapping[str, Any]] = None
    ) -> Table:
        template = self.templates[template_id]
        assert isinstance(template, TableTemplate)
        mutation = mutation or dict()
        if not isinstance(mutation, dict):
            raise TypeError(f"Mutation should be dict, {mutation} is given")
        return Table.new(
            self, template, buffer, offset, mutation
        )
