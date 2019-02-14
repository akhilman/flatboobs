# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods

import enum
import itertools
import operator as op
import struct
from functools import reduce
from typing import Any, Dict, Iterator, List, Mapping, Optional, Type, cast

import attr

from flatboobs import abc
from flatboobs.constants import FORMAT_MAP, UOFFSET_FMT, BaseType
from flatboobs.typing import Scalar, TemplateId, USize

from .abc import Backend, Template


@attr.s(auto_attribs=True, slots=True, cmp=False)
class BaseTemplate(
        Template,
):
    # pylint: disable=too-few-public-methods

    backend: Backend
    id: TemplateId
    namespace: str
    type_name: str
    file_identifier: str

    value_type: BaseType = attr.ib(BaseType.NULL, init=False)
    inline_format: str = attr.ib('', init=False)
    inline_size: USize = attr.ib(0, init=False)
    inline_align: USize = attr.ib(0, init=False)

    finished: bool = attr.ib(False, init=False)

    def __attrs_post_init__(self: 'BaseTemplate') -> None:
        if not self.inline_format:
            self.inline_format = FORMAT_MAP[self.value_type]
        self.inline_size = struct.calcsize(self.inline_format)
        self.inline_align = max(map(struct.calcsize, self.inline_format))

    def finish(self: 'BaseTemplate') -> TemplateId:
        self.finished = True
        return self.id


@attr.s(auto_attribs=True, slots=True, cmp=False)
class FieldTemplate:
    index: int
    name: str
    value_template: Template
    is_vector: bool
    default: Any = None


@attr.s(auto_attribs=True, slots=True, cmp=False)
class ScalarFieldTemplate(FieldTemplate):
    is_vector: bool = attr.ib(False, init=False)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class VectorFieldTemplate(FieldTemplate):
    is_vector: bool = attr.ib(False, init=True)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class EnumTemplate(BaseTemplate, abc.EnumTemplate):

    value_type: BaseType
    bit_flags: bool

    enum_class: Optional[Type[enum.IntEnum]] = attr.ib(None, init=False)
    _members: Dict[str, int] = attr.ib(factory=dict, init=False, repr=False)

    def add_member(
            self: 'EnumTemplate',
            name: str,
            value: int
    ) -> None:
        # pylint: disable=unsupported-assignment-operation
        self._members[name] = value

    def finish(self: 'EnumTemplate') -> TemplateId:

        if self.bit_flags:
            # pylint: disable=unsupported-assignment-operation
            # pylint: disable=unsupported-membership-test
            if 'NONE' not in self._members:
                self._members['NONE'] = 0
            if 'ALL' not in self._members:
                self._members['ALL'] = reduce(op.or_, self._members.values())

        cls = enum.IntFlag if self.bit_flags else enum.IntEnum
        self.enum_class = cls(self.type_name, self._members)

        return super().finish()


@attr.s(auto_attribs=True, slots=True, cmp=False)
class UnionTemplate(BaseTemplate, abc.UnionTemplate):

    value_type: BaseType = attr.ib(BaseType.UNION, init=False)
    value_templates: Dict[int, Template] = attr.ib(factory=dict, init=False)
    enum_template: EnumTemplate = attr.ib(attr.Factory(
        lambda self: self.backend.new_enum_template(
            self.namespace,
            f'_{self.type_name}Type',
            '',
            BaseType.UBYTE,
            False
        ), takes_self=True
    ), init=False)
    inline_format: str = attr.ib(UOFFSET_FMT, init=False)

    def add_member(
            self: 'UnionTemplate',
            name: str,
            variant_id: int,
            value_template_id: TemplateId
    ) -> None:
        # pylint: disable=unsupported-assignment-operation
        self.enum_template.add_member(name, variant_id)
        value_template = self.backend.templates[value_template_id]
        self.value_templates[variant_id] = value_template

    def finish(self: 'UnionTemplate') -> TemplateId:

        # pylint: disable=unsupported-assignment-operation
        # pylint: disable=unsupported-membership-test

        self.enum_template.add_member('NONE', 0)
        self.enum_template.finish()

        return super().finish()


@attr.s(auto_attribs=True, slots=True, cmp=False)
class ScalarTemplate(BaseTemplate):

    value_type: BaseType

    id: TemplateId = attr.ib(cast(TemplateId, 0), init=False)
    namespace: str = attr.ib('', init=False)
    type_name: str = attr.ib('', init=False)
    file_identifier: str = attr.ib('', init=False)
    finished: bool = attr.ib(True, init=False)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class StringTemplate(BaseTemplate):

    value_type: BaseType = attr.ib(BaseType.STRING, init=False)
    id: TemplateId = attr.ib(cast(TemplateId, 0), init=False)
    namespace: str = attr.ib('', init=False)
    type_name: str = attr.ib('', init=False)
    file_identifier: str = attr.ib('', init=False)
    finished: bool = attr.ib(True, init=False)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class StructTemplate:

    value_type: BaseType = attr.ib(BaseType.STRUCT, init=False)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class TableTemplate(BaseTemplate, abc.TableTemplate):

    value_type: BaseType = attr.ib(BaseType.TABLE, init=False)
    fields: List[FieldTemplate] = attr.ib(factory=list, init=False)
    field_count: int = attr.ib(0, init=False)
    _field_counter: Iterator[int] = attr.ib(  # type: ignore
        factory=itertools.count,
        hash=False, init=False, repr=False
    )

    field_map: Mapping[str, FieldTemplate] = cast(
        Mapping[str, FieldTemplate],
        attr.ib(
            factory=dict,
            hash=False, init=False, repr=False
        )
    )

    def add_depreacated_field(self: 'TableTemplate') -> None:
        next(self._field_counter)

    def add_scalar_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_type: BaseType,
            default: Scalar,
    ) -> None:
        index = next(self._field_counter)
        value_template = ScalarTemplate(self.backend, value_type)
        field = (VectorFieldTemplate if is_vector else ScalarFieldTemplate)(
            index, name, value_template, default)
        self.fields.append(field)

    def add_string_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
    ) -> None:
        raise NotImplementedError

    def add_struct_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template_id: TemplateId
    ) -> None:
        raise NotImplementedError

    def add_table_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template_id: TemplateId
    ) -> None:
        index = next(self._field_counter)
        value_template = self.backend.templates[value_template_id]
        field = (VectorFieldTemplate if is_vector else ScalarFieldTemplate)(
            index, name, value_template)
        self.fields.append(field)

    def add_enum_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template_id: TemplateId,
            default: int,
    ) -> None:
        index = next(self._field_counter)
        value_template = self.backend.templates[value_template_id]
        field = (VectorFieldTemplate if is_vector else ScalarFieldTemplate)(
            index, name, value_template, default)
        self.fields.append(field)

    def add_union_field(
            self: 'TableTemplate',
            name: str,
            value_template_id: TemplateId
    ) -> None:
        value_template = self.backend.templates[value_template_id]
        assert isinstance(value_template, UnionTemplate)
        self.add_enum_field(
            f'{name}_type', False, value_template.enum_template.id, 0)
        index = next(self._field_counter)
        field = ScalarFieldTemplate(
            index, name, value_template)
        self.fields.append(field)

    def finish(self: 'TableTemplate') -> TemplateId:
        self.field_map = {f.name: f for f in self.fields}
        self.field_count = next(self._field_counter)
        return super().finish()
