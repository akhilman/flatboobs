# pylint: disable=missing-docstring

from abc import abstractmethod
from typing import Any, Dict, Generic, Mapping, Optional, TypeVar

from flatboobs import abc
from flatboobs.typing import TemplateId, UOffset
from flatboobs.constants import BaseType


class Template(
        abc.Template,
):
    # pylint: disable=too-few-public-methods

    backend: 'Backend'
    id: TemplateId
    namespace: str
    type_name: str
    file_identifier: str
    value_type: BaseType


_TT = TypeVar('_TT', bound=Template)


class Container(Generic[_TT]):  # pylint: disable=unsubscriptable-object
    # pylint: disable=too-few-public-methods
    backend: 'Backend'
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


class Backend(abc.Backend):
    template_ids: Dict[str, TemplateId]
    templates: Dict[TemplateId, abc.Template]

    # TODO rename to new_table()
    @abstractmethod
    def new_table(
            self: 'Backend',
            template_id: TemplateId,
            buffer: Optional[bytes] = None,
            offset: UOffset = 0,
            mutation: Optional[Mapping[str, Any]] = None
    ) -> Container:
        pass
