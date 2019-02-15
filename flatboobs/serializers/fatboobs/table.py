# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods

import collections
import enum
import operator as op
import struct
from functools import reduce
from typing import (
    Any,
    Deque,
    Dict,
    Generator,
    Iterable,
    Iterator,
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

from flatboobs import abc
from flatboobs.constants import (
    FORMAT_MAP,
    PYTYPE_MAP,
    SOFFSET_FMT,
    UOFFSET_FMT,
    UOFFSET_SIZE,
    VOFFSET_FMT,
    VOFFSET_SIZE,
    VSIZE_FMT,
    VSIZE_SIZE
)
from flatboobs.typing import DType, Scalar, UOffset, USize
from flatboobs.utils import remove_prefix

from . import builder, reader
from .abc import Serializer, Container
from .template import (
    EnumTemplate,
    ScalarFieldTemplate,
    ScalarTemplate,
    TableTemplate,
    UnionTemplate
)

###
# Container
##


@attr.s(auto_attribs=True, slots=True, cmp=False, repr=False)
class Table(Container[TableTemplate], abc.Table):
    # pylint: disable=too-many-ancestors
    serializer: Serializer
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

    @staticmethod
    def new(
            serializer: Serializer,
            template: TableTemplate,
            buffer: Optional[bytes],
            offset: UOffset,
            mutation: Dict[str, Any]
    ) -> 'Table':
        # TODO Replace this by @mutation.converter when
        # converter decorator will be implemented
        # https://github.com/python-attrs/attrs/issues/240

        if not isinstance(mutation, collections.abc.Mapping):
            raise TypeError('Mutation should be mapping type, '
                            f'{type(mutation)} is given')

        bad_keys = set(mutation) - set(template.field_map)
        if bad_keys:
            raise KeyError(', '.join(bad_keys))

        non_unions = {
            k: convert_field_value(
                template.field_map[k],
                template.field_map[k].value_template,
                v
            )
            for k, v in mutation.items()
            if not isinstance(
                template.field_map[k].value_template, UnionTemplate)
        }

        unions = ft.compose(
            dict,
            it.concat,
            ft.curry(map)(lambda x: convert_union_fields(serializer, *x)),
            ft.curry(filter)(lambda x: isinstance(x[1], UnionTemplate)),
            ft.curry(map)(lambda x: (
                template.field_map[x[0]],
                template.field_map[x[0]].value_template,
                non_unions.get(f'{x[0]}_type', 0),
                x[1]
            ))
        )(mutation.items())

        mutation = dt.merge(non_unions, unions)

        return Table(serializer, template, buffer, offset, mutation)

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
            value_template = field_template.value_template
            value = read_field(self, field_template, value_template)
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
        return self.new(
            self.serializer,
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

# Callable[[ScalarFieldTemplate, Template, value], Any]
convert_field_value = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.convert_field_value")


@convert_field_value.register(ScalarFieldTemplate, ScalarTemplate, object)
def convert_scalar_field_value(
        field_template: ScalarFieldTemplate,
        value_template: ScalarTemplate,
        value: Any
) -> Scalar:
    # pylint: disable=unused-argument

    pytype = PYTYPE_MAP[value_template.value_type]
    format_ = FORMAT_MAP[value_template.value_type]

    value = pytype(value)

    try:
        struct.pack(format_, value)
    except struct.error as exc:
        raise ValueError(
            f"Bad value for {field_template.name}: "
            + ' '.join(exc.args)
        )

    return value


@convert_field_value.register(ScalarFieldTemplate, EnumTemplate, object)
def convert_enum_field_value(
        field_template: ScalarFieldTemplate,
        value_template: EnumTemplate,
        value: Any
) -> enum.IntEnum:
    assert isinstance(value_template, (EnumTemplate, UnionTemplate))
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


@convert_field_value.register(ScalarFieldTemplate, EnumTemplate, str)
def convert_enum_field_value_from_string(
        field_template: ScalarFieldTemplate,
        value_template: EnumTemplate,
        value: str
) -> enum.IntEnum:
    enum_class = value_template.enum_class
    assert enum_class
    value = remove_prefix(f'{enum_class.__name__}.', value)
    if value_template.bit_flags:
        values = set(value.split('|'))
    else:
        values = {value}
    try:
        ret = reduce(
            op.or_,
            map(lambda x: enum_class.__members__[x], values)  # type: ignore
        )
    except KeyError as exc:
        raise ValueError(
            f"Bad value for {field_template.name}: "
            + ' '.join(exc.args)
        )

    return ret


@convert_field_value.register(ScalarFieldTemplate, TableTemplate, type(None))
def convert_table_field_value_from_none(
        field_template: ScalarFieldTemplate,
        value_template: TableTemplate,
        value: None
) -> Optional[Container]:
    # pylint: disable=unused-argument
    return None


@convert_field_value.register(ScalarFieldTemplate, TableTemplate, Container)
def convert_table_field_value_from_container(
        field_template: ScalarFieldTemplate,
        value_template: TableTemplate,
        value: Container
) -> Optional[Container]:

    if (not isinstance(value, Table)
            or value.template != value_template):
        raise ValueError(
            f"Bad value for {field_template.name}: {value}"
        )

    return value


@convert_field_value.register(ScalarFieldTemplate, TableTemplate, object)
def convert_table_field_value(
        field_template: ScalarFieldTemplate,
        value_template: TableTemplate,
        value: Any
) -> Optional[Container]:
    # pylint: disable=unused-argument
    return Table.new(
        value_template.serializer,
        value_template,
        None,
        0,
        value
    )


def convert_union_fields(
        serializer: Serializer,
        field_template: ScalarFieldTemplate,
        union_template: UnionTemplate,
        union_type: int,
        value: Any
) -> Tuple[Tuple[str, enum.IntEnum], Tuple[str, Optional[Table]]]:

    enum_class = union_template.enum_template.enum_class
    assert issubclass(enum_class, enum.IntEnum)  # type: ignore
    key = field_template.name
    enum_key = f'{key}_type'

    if value is None:
        union_type = 0
        container = None
    elif isinstance(value, Table):
        if union_type:
            raise ValueError(
                f'For evolving "{key}" union field value with Table '
                f'instance value of {enum_key} should be 0 (NONE)'
            )
        union_type_map = {
            v.id: k for k, v in union_template.value_templates.items()
        }
        try:
            union_type = union_type_map[value.template.id]
        except KeyError:
            raise ValueError(f'{value.template.type_name} is bad type '
                             f'for union field "{key}".')
        container = value
    else:
        if union_type == 0:
            raise ValueError(f'Union type "{enum_key}" is not provided.')

        value_template = union_template.value_templates[union_type]
        assert isinstance(value_template, TableTemplate)
        container = Table.new(
            serializer,
            value_template,
            None,
            0,
            value
        )
    return (
        (enum_key, enum_class(union_type)),  # type: ignore
        (key, container)
    )


###
# Read
##
# Callable[[Table, ScalarFieldTemplate, Template], Any]
read_field = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.read_field")


@read_field.register(Table, ScalarFieldTemplate, ScalarTemplate)
def read_scalar_field(
        table: Table,
        field_template: ScalarFieldTemplate,
        value_template: Union[ScalarTemplate, EnumTemplate]
) -> Scalar:

    if not table.buffer or not table.offset:
        return field_template.default

    assert isinstance(table.vtable, tuple)
    idx = field_template.index
    if idx >= len(table.vtable):
        return field_template.default

    foffset = table.vtable[idx]
    if not foffset:
        return field_template.default

    return reader.read_scalar(
        FORMAT_MAP[value_template.value_type],
        table.buffer,
        table.offset + foffset
    )


@read_field.register(Table, ScalarFieldTemplate, EnumTemplate)
def read_enum_field(
        table: Table,
        field_template: ScalarFieldTemplate,
        value_template: EnumTemplate
) -> Scalar:

    enum_class = value_template.enum_class
    assert issubclass(enum_class, (enum.IntEnum, enum.IntFlag))  # type: ignore

    value = read_scalar_field(table, field_template, value_template)
    assert isinstance(value, int)

    return enum_class(value)  # type: ignore


@read_field.register(Table, ScalarFieldTemplate, TableTemplate)
def read_table_field(
        table: Table,
        field_template: ScalarFieldTemplate,
        value_template: TableTemplate
) -> Optional[Container]:

    if not table.buffer or not table.offset:
        return None

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
    offset = cast(UOffset, offset)

    return Table.new(
        table.serializer,
        value_template,
        table.buffer,
        offset,
        dict()
    )


@read_field.register(Table, ScalarFieldTemplate, UnionTemplate)
def read_union_field(
        table: Table,
        field_template: ScalarFieldTemplate,
        union_template: UnionTemplate
) -> Optional[Container]:

    union_type = table[f'{field_template.name}_type']
    if union_type == 0:
        return None

    value_template = union_template.value_templates[union_type]

    return read_table_field(table, field_template, value_template)


###
# Write
##


@builder.flatten.register(int, Table)
def flatten_table(
        recursion_limit: int,
        table: Table
) -> Generator[Container, None, None]:
    if recursion_limit < 1:
        raise RecursionError('Maximum recursion limit reached')
    for value in table.values():
        if isinstance(value, Container):
            yield from builder.flatten(recursion_limit - 1, value)

    yield table


@builder.calc_size.register(int, Table)
def calc_table_size(
        size: UOffset,
        table: Table
) -> USize:
    field_count = 0
    for key, value in table.items():
        field_template = table.template.field_map[key]
        if value == field_template.default:
            continue
        value_template = field_template.value_template
        size += value_template.inline_size
        size += -size % value_template.inline_align
        field_count = max(field_count, field_template.index + 1)

    size += UOFFSET_SIZE
    size += -size % UOFFSET_SIZE
    size += field_count * VOFFSET_SIZE + 2 * VSIZE_SIZE

    return size


# Callable[[UOffset, Mapping[int, UOffset], Any],
#          Generator[Scalar, None, None,]]
inline_value = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.field_size")


@inline_value.register(int, dict, object)
def inline_scalar_value(offset, offset_map, value):
    # pylint: disable=unused-argument
    yield value


@inline_value.register(int, dict, Table)
def inline_table_value(offset, offset_map, table):
    yield offset - offset_map[hash(table)]


@attr.s(auto_attribs=True, frozen=True, slots=True)
class InlineBlock:
    index: int = -1  # -1 for padding
    size: USize = 0
    align: USize = 0
    format: str = ''
    value: Any = None
    pinned: bool = False


def align_blocks(
        cursor: USize,
        blocks: Iterable[InlineBlock]
) -> Sequence[InlineBlock]:
    packed: Deque[InlineBlock] = collections.deque()
    pending = sorted(blocks, key=op.attrgetter('size'), reverse=True)

    if not pending:
        return packed

    while pending:
        gap = -cursor % pending[0].align if cursor else 0
        if gap:
            for block in pending:
                if block.align <= gap:
                    pending.remove(block)
                    break
            else:
                block = InlineBlock(size=gap, format='x'*gap)
        else:
            block = pending.pop(0)
        packed.appendleft(block)
        cursor += block.size

    gap = -cursor % UOFFSET_SIZE
    if gap:
        block = InlineBlock(size=gap, format='x'*gap)
        packed.appendleft(block)

    return packed


@builder.write.register(bytearray, int, dict, Table)
def write_table(
        buffer: bytearray,
        cursor: UOffset,
        offset_map: Mapping[int, UOffset],
        table: Table,
) -> Tuple[UOffset, UOffset]:
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals  # TODO split to smaller functions?

    inline_blocks = ft.compose(
        ft.curry(align_blocks)(cursor),
        ft.curry(map)(lambda x: InlineBlock(
            table.template.field_map[x].index,
            table.template.field_map[x].value_template.inline_size,
            table.template.field_map[x].value_template.inline_align,
            table.template.field_map[x].value_template.inline_format,
            table[x],
        )),
        ft.curry(filter)(lambda x: table[x]
                         != table.template.field_map[x].default)
    )(table.keys())

    if inline_blocks:
        vtable = [0] * (max(map(op.attrgetter('index'), inline_blocks)) + 1)
    else:
        vtable = []
    vtable_size = VSIZE_SIZE * 2 + VOFFSET_SIZE * len(vtable)

    body_size = UOFFSET_SIZE
    for block in inline_blocks:
        if block.index >= 0:
            vtable[block.index] = body_size
        body_size += block.size

    cursor += body_size
    offset = cursor
    cursor += vtable_size

    format_ = ''.join([
        '<',
        VSIZE_FMT * 2,
        VOFFSET_FMT * len(vtable),
        SOFFSET_FMT,
        *map(op.attrgetter('format'), inline_blocks)
    ])

    values = ft.compose(
        list,
        it.concat,
        ft.curry(it.cons)([vtable_size, body_size]),
        ft.curry(it.cons)(vtable),
        ft.curry(it.cons)([vtable_size]),
        ft.curry(map)(lambda x: inline_value(
            offset - vtable[x.index], offset_map, x.value)),
        ft.curry(filter)(lambda x: x.value is not None)
    )(inline_blocks)

    # from pprint import pprint
    # pprint(inline_blocks)
    print('format:', format_)
    print('values:', values)
    print('cursor', hex(cursor), 'offset', hex(offset))

    struct.pack_into(format_, buffer, len(buffer) - cursor, *values)

    return cursor, offset
