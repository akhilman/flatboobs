# pylint: disable=missing-docstring

from abc import abstractmethod
from typing import Any, Dict, Generic, Mapping, Optional, TypeVar

from flatboobs import abc
from flatboobs.typing import TemplateId, UOffset, USize
from flatboobs.constants import BaseType


class Template(
        abc.Template,
):
    # pylint: disable=too-few-public-methods
    # pylint: disable=abstract-method

    serializer: 'Serializer'
    id: TemplateId
    namespace: str
    type_name: str
    file_identifier: str
    value_type: BaseType
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

    def __hash__(self):
        return id(self)


class Serializer(abc.Serializer):
    template_ids: Dict[str, TemplateId]
    templates: Dict[TemplateId, Template]

    # TODO rename to new_table()
    @abstractmethod
    def new_table(
            self: 'Serializer',
            template_id: TemplateId,
            buffer: Optional[bytes] = None,
            offset: UOffset = 0,
            mutation: Optional[Mapping[str, Any]] = None
    ) -> abc.Table:
        pass
