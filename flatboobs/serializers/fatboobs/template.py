# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods

import enum
import itertools
import struct
from typing import Any, Dict, Iterator, List, Mapping, Optional, Type, cast

import attr

from flatboobs import schema
from flatboobs.constants import FORMAT_MAP, PYTYPE_MAP, UOFFSET_FMT, BaseType
from flatboobs.typing import USize

from .abc import Template
from .enum import any_to_enum


@attr.s(auto_attribs=True, slots=True, cmp=False)
class BaseTemplate(Template):
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    type_decl: Optional[schema.TypeDeclaration]

    value_type: BaseType = attr.ib(BaseType.NULL, init=False)
    value_pytype: Optional[type] = attr.ib(None, init=False)
    inline_format: str = attr.ib('', init=False)
    inline_size: USize = attr.ib(0, init=False)
    inline_align: USize = attr.ib(0, init=False)

    finished: bool = attr.ib(False, init=False)

    def __attrs_post_init__(self: 'BaseTemplate') -> None:
        if not self.value_pytype:
            self.value_pytype = PYTYPE_MAP.get(self.value_type, None)
        if not self.inline_format:
            self.inline_format = FORMAT_MAP[self.value_type]
        self.inline_size = struct.calcsize(self.inline_format)
        self.inline_align = max(map(struct.calcsize, self.inline_format))

        if self.type_decl:
            self.namespace = self.type_decl.namespace or ''
            self.type_name = self.type_decl.name or ''
            self.file_identifier = self.type_decl.file_identifier or ''

    def finish(self: 'BaseTemplate') -> None:
        assert not self.finished
        self.finished = True


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
class EnumTemplate(BaseTemplate):

    value_type: BaseType
    value_pytype: type


@attr.s(auto_attribs=True, slots=True, cmp=False)
class ScalarTemplate(BaseTemplate):

    value_type: BaseType
    type_decl: Optional[schema.TypeDeclaration] = attr.ib(None, init=False)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class StringTemplate(BaseTemplate):

    type_decl: Optional[schema.TypeDeclaration] = attr.ib(None, init=False)
    value_type: BaseType = attr.ib(BaseType.STRING, init=False)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class StructTemplate:

    value_type: BaseType = attr.ib(BaseType.STRUCT, init=False)

    # if field.is_vector:
    #     raise TypeError(
    #         f'Struct "{type_decl.name}" field "{field.name}" '
    #         'could not be vector.'
    #     )

    # if (field.type not in STRING_TO_SCALAR_TYPE_MAP
    #         and not isinstance(
    #             type_map.get(field.type, None),
    #             schema.Enum
    #         )):
    #     raise TypeError(
    #         f'Struct "{type_decl.name}" field "{field.name}" type '
    #         f'could not be {field.type}'
    #     )

    # self._add_template_field(type_map, template, field)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class TableTemplate(BaseTemplate):

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
        assert not self.finished
        next(self._field_counter)

    def add_field(
            self: 'TableTemplate',
            field: schema.Field,
            value_template: Template
    ) -> None:

        assert not self.finished

        field_factory: Type[FieldTemplate]
        field_template: FieldTemplate

        index = next(self._field_counter)
        if field.is_vector:
            field_factory = VectorFieldTemplate
        else:
            field_factory = ScalarFieldTemplate

        default = field.default
        if isinstance(value_template, ScalarTemplate):
            assert value_template.value_pytype
            if default is None:
                default = value_template.value_pytype()
            else:
                default = value_template.value_pytype(default)
        elif isinstance(value_template, EnumTemplate):
            assert issubclass(value_template.value_pytype,
                              (enum.IntEnum, enum.IntFlag))
            if default is None:
                default = value_template.value_pytype(
                    min(value_template.value_pytype)  # type: ignore
                )
            else:
                default = any_to_enum(value_template.value_pytype, default)

        field_template = field_factory(
            index, field.name, value_template, default)
        self.fields.append(field_template)

    def finish(self: 'TableTemplate') -> None:
        assert not self.finished
        self.field_map = {
            f.name: f for f in self.fields  # pylint: disable=not-an-iterable
        }
        self.field_count = next(self._field_counter)
        super().finish()


@attr.s(auto_attribs=True, slots=True, cmp=False)
class UnionTemplate(BaseTemplate):

    enum_template: EnumTemplate
    value_type: BaseType = attr.ib(BaseType.UNION, init=False)
    value_templates: Dict[int, TableTemplate] = \
        attr.ib(factory=dict, init=False)
    inline_format: str = attr.ib(UOFFSET_FMT, init=False)

    def add_member(
            self: 'UnionTemplate',
            enum_value: int,
            value_template: TableTemplate
    ) -> None:
        # pylint: disable=unsupported-assignment-operation
        assert not self.finished
        self.value_templates[enum_value] = value_template
