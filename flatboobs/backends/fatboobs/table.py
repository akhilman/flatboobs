# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods

import enum
import operator as op
import struct
from typing import (
    Any,
    Dict,
    Generator,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union
)

import attr
import toolz.dicttoolz as dt
import toolz.functoolz as ft
import toolz.itertoolz as it
from multipledispatch import Dispatcher

from flatboobs import abc
from flatboobs.constants import (
    FORMAT_MAP,
    NBYTES_MAP,
    PYTYPE_MAP,
    SOFFSET_FMT,
    SOFFSET_SIZE,
    UOFFSET_FMT,
    UOFFSET_SIZE,
    VOFFSET_FMT,
    VOFFSET_SIZE,
    VSIZE_FMT,
    VSIZE_SIZE
)
from flatboobs.typing import DType, Scalar, UOffset, USize

from . import builder, reader
from .backend import FatBoobs, new_container
from .container import Container
from .template import (
    EnumFieldTemplate,
    EnumTemplate,
    PointerFieldTemplate,
    ScalarFieldTemplate,
    StringFieldTemplate,
    TableTemplate
)

###
# Container
##

@new_container.register(
    FatBoobs, TableTemplate, (type(None), bytes, bytearray), int, object)
def new_table(
        backend: FatBoobs,
        template: TableTemplate,
        buffer: Optional[bytes],
        offset: UOffset,
        mutation: Any
) -> 'Table':
    # TODO Replace this by @mutation.converter when
    # converter decorator will be implemented
    # https://github.com/python-attrs/attrs/issues/240

    if not isinstance(mutation, dict):
        raise TypeError(f"Mutation should be dict, {mutation} is given")
    bad_keys = set(mutation) - set(template.field_map)
    if bad_keys:
        raise KeyError(', '.join(bad_keys))

    mutation = {
        k: convert_field_value(backend, template.field_map[k], v)
        for k, v in mutation.items()
    }
    # TODO fix enums

    return Table(backend, template, buffer, offset, mutation)


@attr.s(auto_attribs=True, slots=True, cmp=False, repr=False)
class Table(Container[TableTemplate], abc.Table):
    # pylint: disable=too-many-ancestors
    backend: FatBoobs
    template: TableTemplate
    buffer: Optional[bytes] = None
    offset: UOffset = 0
    mutation: Mapping[str, Any] = attr.ib(factory=dict)
    vtable: Optional[Sequence[UOffset]] = attr.ib(None, init=False)
    _cached_items: Dict[str, Any] = attr.ib(factory=dict, init=False)
    _hash: int = 0

    def __attrs_post_init__(self):

        if self.buffer:
            self.vtable = reader.read_vtable(self.buffer, self.offset)

        self._hash = hash((
            id(self.template),
            id(self.buffer),
            self.offset,
            tuple(self.mutation.items())
        ))

    @property
    def dtype(
            self: 'Table'
    ) -> DType:
        raise NotImplementedError

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return self._hash

    def __getitem__(
            self: 'Table',
            key: str
    ) -> Any:

        if key in self._cached_items:
            return self._cached_items[key]

        if self.mutation and key in self.mutation:
            value = self.mutation[key]
        elif key in self.template.field_map:
            field_template = self.template.field_map[key]
            value = read_field(self, field_template)
        else:
            raise KeyError(key)

        self._cached_items[key] = value

        return value

    def __iter__(
            self: 'Table'
    ) -> Iterator[str]:
        return map(op.attrgetter('name'), self.template.fields)

    def __len__(
            self: 'Table'
    ) -> int:
        return len(self.template.fields)

    def __repr__(self: 'Table') -> str:
        return f"{self.type_name}({dict(self)})"

    def evolve(
            self: 'Table',
            **kwargs: Mapping[str, Any]
    ) -> 'Table':
        mutation = dt.merge(
            self.mutation or {},
            kwargs
        )
        return new_container(
            self.backend,
            self.template,
            self.buffer,
            self.offset,
            mutation
        )

    def packb(self: 'Table') -> bytes:
        return builder.build(self)


###
# Field value converter
##

# Callable[[FatBoobs, FieldTemplate, value], Any]
convert_field_value = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.convert_field_value")


@convert_field_value.register(FatBoobs, ScalarFieldTemplate, object)
def convert_scalar_field_value(
        backend: FatBoobs,
        field_template: ScalarFieldTemplate,
        value: Any
) -> Scalar:
    # pylint: disable=unused-argument

    pytype = PYTYPE_MAP[field_template.value_type]
    format_ = FORMAT_MAP[field_template.value_type]

    value = pytype(value)

    try:
        struct.pack(format_, value)
    except struct.error as exc:
        raise ValueError(
            f"Bad value for {field_template.name}: "
            + ' '.join(exc.args)
        )

    return value


@convert_field_value.register(FatBoobs, EnumFieldTemplate, object)
def convert_enum_field_value(
        backend: FatBoobs,
        field_template: EnumFieldTemplate,
        value: Any
) -> enum.IntEnum:
    value_template = backend.templates[field_template.value_template]
    assert isinstance(value_template, EnumTemplate)
    enum_class = value_template.enum_class
    assert enum_class
    try:
        value = enum_class(value)
    except ValueError as exc:
        raise ValueError(
            f"Bad value for {field_template.name}: "
            + ' '.join(exc.args)
        )

    return value


@convert_field_value.register(FatBoobs, EnumFieldTemplate, str)
def convert_enum_field_value_from_string(
        backend: FatBoobs,
        field_template: EnumFieldTemplate,
        value: str
) -> enum.IntEnum:
    value_template = backend.templates[field_template.value_template]
    assert isinstance(value_template, EnumTemplate)
    enum_class = value_template.enum_class
    assert enum_class
    try:
        ret = enum_class.__members__[value]  # typing: ignore
    except KeyError as exc:
        raise ValueError(
            f"Bad value for {field_template.name}: "
            + ' '.join(exc.args)
        )

    return ret


@convert_field_value.register(FatBoobs, PointerFieldTemplate, type(None))
def convert_pointer_field_value_from_none(
        backend: FatBoobs,
        field_template: PointerFieldTemplate,
        value: None
) -> Optional[Container]:
    # pylint: disable=unused-argument
    return None


@convert_field_value.register(FatBoobs, PointerFieldTemplate, Container)
def convert_pointer_field_value_from_container(
        backend: FatBoobs,
        field_template: PointerFieldTemplate,
        value: Container
) -> Optional[Container]:

    value_template = backend.templates[field_template.value_template]
    if (not isinstance(value, Table)
            or value.template != value_template):
        raise ValueError(
            f"Bad value for {field_template.name}: {value}"
        )

    return value


@convert_field_value.register(FatBoobs, PointerFieldTemplate, object)
def convert_pointer_field_value(
        backend: FatBoobs,
        field_template: PointerFieldTemplate,
        value: Any
) -> Optional[Container]:

    value_template = backend.templates[field_template.value_template]

    return new_container(
        backend,
        value_template,
        None,
        0,
        value
    )


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
) -> Scalar:

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


@read_field.register(Table, EnumFieldTemplate)
def read_enum_field(
        table: Table,
        field_template: EnumFieldTemplate
) -> Scalar:

    value_template = table.backend.templates[field_template.value_template]
    assert isinstance(value_template, EnumTemplate)
    enum_class = value_template.enum_class
    assert enum_class

    if not table.buffer or not table.offset:
        return enum_class(field_template.default)

    assert table.vtable
    idx = field_template.index
    if idx >= len(table.vtable):
        return enum_class(field_template.default)

    foffset = table.vtable[idx]
    if not foffset:
        return enum_class(field_template.default)

    value = reader.read_scalar(
        FORMAT_MAP[value_template.value_type],
        table.buffer,
        table.offset + foffset
    )

    assert isinstance(value, int)

    return enum_class(value)


@read_field.register(Table, PointerFieldTemplate)
def read_pointer_field(
        table: Table,
        field_template: PointerFieldTemplate
) -> Optional[Container]:

    if not table.buffer or not table.offset:
        return None

    value_template = table.backend.templates[field_template.value_template]

    assert isinstance(table.vtable, tuple)
    idx = field_template.index
    if idx >= len(table.vtable):
        return None

    foffset = table.vtable[idx]
    if not foffset:
        return None

    offset = reader.read_scalar(
        UOFFSET_FMT,
        table.buffer,
        table.offset + foffset
    )
    assert isinstance(offset, int)
    offset += foffset + table.offset

    return new_container(
        table.backend,
        value_template,
        table.buffer,
        offset,
        dict()
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


@field_format.register(Table, EnumFieldTemplate)
def enum_field_format(
        table: Table,
        field_template: EnumFieldTemplate
) -> str:
    value_template = table.backend.templates[field_template.value_template]
    assert isinstance(value_template, EnumTemplate)
    return FORMAT_MAP[value_template.value_type]


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


@field_size.register(Table, EnumFieldTemplate)
def enum_field_size(
        table: Table,
        field_template: EnumFieldTemplate
) -> USize:
    value_template = table.backend.templates[field_template.value_template]
    assert isinstance(value_template, EnumTemplate)
    return NBYTES_MAP[value_template.value_type]


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
    body_values = {k: v for k, v in table.items() if v != field_map[k].default}
    keys = list(body_values.keys())
    size_map = {k: field_size(table, field_map[k]) for k in keys}
    format_map = {k: field_format(table, field_map[k]) for k in keys}

    # Fill space between table's UOffset and first largest value
    # by smaller values
    if keys:
        pad_left = - SOFFSET_SIZE % max(size_map.values())
    else:
        pad_left = 0
    keys = sorted(keys, key=lambda k: size_map[k], reverse=True)
    for key in keys:
        if not pad_left:
            break
        if size_map[key] <= pad_left:
            keys.remove(key)
            keys.insert(0, key)
            pad_left -= size_map[key]

    body_size = sum(it.cons(0, size_map.values()))
    pad_right = -(body_size+cursor) % SOFFSET_SIZE

    print('table', table.type_name)
    print('cursor', hex(cursor), 'offset_map',
          {k: hex(v) for k, v in offset_map.items()})
    print('items', dict(body_values))
    print('hashes', {k: hash(v) for k, v in body_values.items()})
    # print('sizes', [size_map[k] for k in keys])
    # print('formats', [format_map[k] for k in keys])
    # print('pad_left', pad_left, 'pad_right', pad_right)

    # field_count = table.template.field_count
    if keys:
        field_count = max(map(lambda x: field_map[x].index, keys)) + 1
    else:
        field_count = 0
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
        keys,
        ft.compose(
            ft.curry(it.accumulate)(op.add),
            ft.curry(it.cons)(pad_left+SOFFSET_SIZE),
            ft.curry(map)(lambda k: size_map[k])
        )(keys)
    ))
    vtable_offsets_by_index = {
        field_map[k].index: vtable_offsets[k]
        for k in keys
    }

    vtable = map(
        lambda n: vtable_offsets_by_index.get(n, 0),
        range(field_count)
    )

    offset = cursor + pad_right + body_size + pad_left + SOFFSET_SIZE
    cursor = offset + vtable_size

    # replace containers with offsets
    for key, value in body_values.items():
        if isinstance(value, Container):
            body_values[key] = (
                offset - vtable_offsets[key] - offset_map[hash(value)])
            print(hex(body_values[key]), hex(offset), hex(
                vtable_offsets[key]), hex(offset_map[hash(value)]))

    struct.pack_into(
        composed_format,
        buffer,
        len(buffer) - cursor,
        vtable_size, SOFFSET_SIZE + pad_left + body_size, *vtable,
        vtable_size, *(body_values[k] for k in keys)
    )

    print('cursor', hex(cursor), 'offset', hex(offset))

    return cursor, offset
