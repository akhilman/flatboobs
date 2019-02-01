# pylint: disable=missing-docstring

import weakref
from typing import Generic, TypeVar

import flatboobs.schema
from flatboobs import abc

_ST = TypeVar('_ST', bound=flatboobs.schema.TypeDeclaration)


class Template(
        abc.Template,
        Generic[_ST]  # pylint: disable=unsubscriptable-object
):
    # pylint: disable=too-few-public-methods
    backend: weakref.ProxyType
    id: abc.TemplateId
    schema: _ST

    finished: bool

    def finish(self: 'Template') -> abc.TemplateId:
        self.finished = True
        return self.id
