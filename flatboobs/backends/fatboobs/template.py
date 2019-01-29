# pylint: disable=missing-docstring

from typing import Generic, TypeVar

import attr

import flatboobs.schema
from flatboobs import abc

from . import backend as b  # pylint: disable=unused-import

_ST = TypeVar('_ST', bound=flatboobs.schema.TypeDeclaration)


@attr.s(auto_attribs=True, slots=True)
class Template(
        abc.Template,
        Generic[_ST]  # pylint: disable=unsubscriptable-object
):
    # pylint: disable=too-few-public-methods
    backend: 'b.FatBoobs'
    id: abc.TemplateId
    schema: _ST

    finished: bool = attr.ib(False, init=False)

    def finish(self: 'Template') -> abc.TemplateId:
        self.finished = True
        return self.id
