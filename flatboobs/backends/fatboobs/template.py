# pylint: disable=missing-docstring

import weakref

from flatboobs import abc


class Template(
        abc.Template,
):
    # pylint: disable=too-few-public-methods
    backend: weakref.ProxyType
    id: abc.TemplateId
    namespace: str
    type_name: str
    file_identifier: str

    finished: bool

    def finish(self: 'Template') -> abc.TemplateId:
        self.finished = True
        return self.id
