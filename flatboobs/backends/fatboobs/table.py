# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods

import enum
import itertools
import operator as op
import struct
import weakref
from typing import (
    Any,
    Generator,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast
)

import attr
import toolz.dicttoolz as dt
import toolz.functoolz as ft
import toolz.itertoolz as it
from multipledispatch import Dispatcher

import flatboobs.schema
from flatboobs import abc
from flatboobs.constants import (
    FORMAT_MAP,
    NBYTES_MAP,
    SOFFSET_FMT,
    SOFFSET_SIZE,
    UOFFSET_FMT,
    UOFFSET_SIZE,
    VOFFSET_FMT,
    VOFFSET_SIZE,
    VSIZE_FMT,
    VSIZE_SIZE,
    BaseType
)
from flatboobs.typing import DType, Integer, Scalar, TemplateId, UOffset, USize

from . import builder, reader
from .container import Container
from .template import Template

###
# Template
##


@attr.s(auto_attribs=True, slots=True)
class FieldTemplate:
    index: int
    name: str
    is_vector: bool
    value_type: BaseType
    default: Any


@attr.s(auto_attribs=True, slots=True)
class ScalarFieldTemplate(FieldTemplate):
    default: Scalar


@attr.s(auto_attribs=True, slots=True)
class EnumFieldTemplate(FieldTemplate):
    default: Integer


@attr.s(auto_attribs=True, slots=True)
class PointerFieldTemplate(FieldTemplate):
    value_type: BaseType
    default: None = None


@attr.s(auto_attribs=True, slots=True)
class StringFieldTemplate(FieldTemplate):
    value_type: BaseType = attr.ib(BaseType.STRING, init=False)
    default: None = None


@attr.s(auto_attribs=True, slots=True)
class UnionFieldTemplate(FieldTemplate):
    value_type: BaseType = attr.ib(BaseType.UNION, init=False)
    default: None = None


@attr.s(auto_attribs=True, slots=True)
class TableTemplate(Template[flatboobs.schema.Table], abc.TableTemplate):

    backend: weakref.ProxyType = (  # type: ignore
        attr.ib(converter=weakref.proxy))
    id: abc.TemplateId
    schema: flatboobs.schema.Table

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
    finished: bool = attr.ib(False, init=False)

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
        field = ScalarFieldTemplate(
            index, name, is_vector, value_type, default)
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
            value_template: TemplateId,
    ) -> None:
        raise NotImplementedError

    def add_table_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template: TemplateId,
    ) -> None:
        raise NotImplementedError

    def add_enum_field(
            self: 'TableTemplate',
            name: str,
            is_vector: bool,
            value_template: TemplateId,
            default: int,
    ) -> None:
        raise NotImplementedError

    def add_union_field(
            self: 'TableTemplate',
            name: str,
            value_template: TemplateId,
    ) -> None:
        raise NotImplementedError

    def finish(self: 'TableTemplate') -> TemplateId:
        super().finish()
        self.field_map = {f.name: f for f in self.fields}
        self.field_count = next(self._field_counter)
        return self.id


###
# Container
##

@attr.s(auto_attribs=True, slots=True, cmp=False)
class Table(Container[TableTemplate], abc.Table):
    # pylint: disable=too-many-ancestors
    template: TableTemplate
    buffer: Optional[bytes] = None
    offset: UOffset = 0
    mutation: Optional[Mapping[str, Any]] = None
    vtable: Optional[Sequence[UOffset]] = None

    def __attrs_post_init__(self):
        if self.buffer:
            self.vtable = reader.read_vtable(self.buffer, self.offset)

    @property
    def enums(
            self: 'Table'
    ) -> Mapping[str, enum.IntEnum]:
        raise NotImplementedError

    @property
    def schema(
            self: 'Table'
    ) -> flatboobs.schema.Table:
        raise NotImplementedError

    @property
    def dtype(
            self: 'Table'
    ) -> DType:
        raise NotImplementedError

    def __getitem__(
            self: 'Table',
            key: str
    ) -> Any:

        if self.mutation and key in self.mutation:
            return self.mutation[key]

        field_template = self.template.field_map[key]
        value = read_field(self, field_template)

        return value

    def __iter__(
            self: 'Table'
    ) -> Iterator[str]:
        return map(op.attrgetter('name'), self.template.fields)

    def __len__(
            self: 'Table'
    ) -> int:
        return len(self.template.fields)

    def evolve(
            self: 'Table',
            **kwargs: Mapping[str, Any]
    ) -> 'Table':
        bad_keys = set(kwargs) - set(self)
        if bad_keys:
            raise KeyError(', '.join(bad_keys))
        mutation = dt.merge(
            self.mutation or {},
            kwargs
        )
        return attr.evolve(self, mutation=mutation)

    def packb(self: 'Table') -> bytes:
        return builder.build(self)

###
# Read
##


# Callable[[Table, FieldTemplate], Any]
read_field = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.read_field")


@read_field.register(Table, ScalarFieldTemplate)
def read_scalar_field(
        table: Table,
        field_template: ScalarFieldTemplate
) -> abc.Scalar:

    if not table.buffer or not table.offset:
        return field_template.default

    assert table.vtable
    idx = field_template.index
    if idx >= len(table.vtable):
        return field_template.default

    foffset = table.vtable[idx]
    if not foffset:
        return field_template.default

    return reader.read_scalar(
        FORMAT_MAP[field_template.value_type],
        table.buffer,
        table.offset + foffset
    )


###
# Write
##


@builder.flatten.register(Table)
def flatten_table(
        table: Table
) -> Generator[Container, None, None]:
    for value in table.values():
        if isinstance(value, Container):
            yield from builder.flatten(value)

    yield table


# Callable[[Table, FieldTemplate], USize]
field_size = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.field_size")

# Callable[[Table, FieldTemplate], str]
field_format = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.field_format")


@field_format.register(Table, ScalarFieldTemplate)
def scalar_field_format(
        table: Table,
        field_template: ScalarFieldTemplate
) -> str:
    # pylint: disable=unused-argument
    return FORMAT_MAP[field_template.value_type]


@field_format.register(Table, PointerFieldTemplate)
@field_format.register(Table, StringFieldTemplate)
def pointer_field_format(
        table: Table,
        field_template: Union[PointerFieldTemplate, StringFieldTemplate]
) -> str:
    # pylint: disable=unused-argument
    return UOFFSET_FMT


@field_size.register(Table, ScalarFieldTemplate)
def scalar_field_size(
        table: Table,
        field_template: ScalarFieldTemplate
) -> USize:
    # pylint: disable=unused-argument
    return NBYTES_MAP[field_template.value_type]


@field_size.register(Table, PointerFieldTemplate)
@field_size.register(Table, StringFieldTemplate)
def pointer_field_size(
        table: Table,
        field_template: Union[PointerFieldTemplate, StringFieldTemplate]
) -> USize:
    # pylint: disable=unused-argument
    return UOFFSET_SIZE


@builder.calc_size.register(int, Table)
def calc_table_size(
        size: UOffset,
        table: Table
) -> USize:
    for key, value in table.items():
        field_template = table.template.field_map[key]
        if value == field_template.default:
            continue
        size += field_size(table, field_template)

    size += -size % UOFFSET_SIZE
    size += UOFFSET_SIZE
    size += table.template.field_count * VOFFSET_SIZE + 2 * VSIZE_SIZE

    return size


@builder.write.register(bytearray, int, dict, Table)
def write_table(
        buffer: bytearray,
        cursor: UOffset,
        offset_map: Mapping[int, UOffset],
        table: Table,
) -> Tuple[UOffset, UOffset]:
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals  # TODO split to smaller functions?

    field_map = table.template.field_map
    body_values = {k: v for k, v in table.items()
                   if v != field_map[k].default}
    keys = list(body_values.keys())
    size_map = {k: field_size(table, field_map[k])
                for k in keys}
    format_map = {k: field_format(table, field_map[k])
                  for k in keys}

    # Fill space between table's UOffset and first largest value
    # by smaller values
    pad_left = - SOFFSET_SIZE % max(size_map.values())
    keys = sorted(keys, key=lambda k: size_map[k], reverse=True)
    for key in keys:
        if not pad_left:
            break
        if size_map[key] <= pad_left:
            keys.remove(key)
            keys.insert(0, key)
            pad_left -= size_map[key]

    body_size = sum(size_map.values())
    pad_right = -(body_size+cursor) % SOFFSET_SIZE

    print('keys', keys)
    # print('sizes', [size_map[k] for k in keys])
    # print('formats', [format_map[k] for k in keys])
    # print('pad_left', pad_left, 'pad_right', pad_right)

    # field_count = table.template.field_count
    field_count = max(map(lambda x: field_map[x].index, keys)) + 1
    vtable_size = VSIZE_SIZE * 2 + VOFFSET_SIZE * field_count

    composed_format = ''.join((
        '<',
        VSIZE_FMT * 2,
        VOFFSET_FMT * field_count,
        SOFFSET_FMT,
        'x'*pad_left,
        *(format_map[k] for k in keys),
        'x'*pad_right,
    ))
    print(composed_format)

    vtable_offsets = dict(zip(
        map(lambda k: field_map[k].index, keys),
        ft.compose(
            ft.curry(it.accumulate)(op.add),
            ft.curry(it.cons)(pad_left+SOFFSET_SIZE),
            ft.curry(map)(lambda k: size_map[k])
        )(keys)
    ))

    vtable = map(lambda n: vtable_offsets.get(n, 0), range(field_count))

    offset = cursor + pad_right + body_size + pad_left + SOFFSET_SIZE
    cursor = offset + vtable_size

    struct.pack_into(
        composed_format,
        buffer,
        len(buffer) - cursor,
        vtable_size, SOFFSET_SIZE + pad_left + body_size, *vtable,
        vtable_size, *(body_values[k] for k in keys)
    )

    # print(cursor, offset)

    return cursor, offset
