# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods

import collections
import enum
import operator as op
import struct
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
from flatboobs.typing import Scalar

from . import builder, reader
from .abc import Container, Serializer
from .constants import (
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
from .enum import any_to_enum
from .skeleton import (
    EnumSkeleton,
    ScalarFieldSkeleton,
    ScalarSkeleton,
    StructSkeleton,
    TableSkeleton,
    UnionSkeleton
)
from .struct import Struct
from .typing import UOffset, USize

###
# Container
##


@attr.s(auto_attribs=True, slots=True, cmp=False, repr=False)
class Table(Container[TableSkeleton], abc.Table):
    # pylint: disable=too-many-ancestors
    serializer: Serializer
    skeleton: TableSkeleton
    buffer: Optional[bytes] = None
    offset: UOffset = 0
    mutation: Mapping[str, Any] = attr.ib(factory=dict)
    vtable: Optional[Sequence[UOffset]] = attr.ib(None, init=False)
    _cached_items: Dict[str, Any] = attr.ib(factory=dict, init=False)
    _hash: int = 0

    @staticmethod
    def new(
            serializer: Serializer,
            skeleton: TableSkeleton,
            buffer: Optional[bytes],
            offset: UOffset,
            mutation: Optional[Dict[str, Any]]
    ) -> 'Table':

        if mutation is None:
            mutation = {}
        elif not isinstance(mutation, collections.abc.Mapping):
            raise TypeError('Mutation should be mapping type or None, '
                            f'{type(mutation)} is given')

        bad_keys = set(mutation) - set(skeleton.field_map)
        if bad_keys:
            raise KeyError(', '.join(bad_keys))

        non_unions = {
            k: convert_field_value(
                serializer,
                skeleton.field_map[k],
                skeleton.field_map[k].value_skeleton,
                v
            )
            for k, v in mutation.items()
            if not isinstance(
                skeleton.field_map[k].value_skeleton, UnionSkeleton)
        }

        unions = ft.compose(
            dict,
            it.concat,
            ft.curry(map)(lambda x: convert_union_fields(serializer, *x)),
            ft.curry(filter)(lambda x: isinstance(x[1], UnionSkeleton)),
            ft.curry(map)(lambda x: (
                skeleton.field_map[x[0]],
                skeleton.field_map[x[0]].value_skeleton,
                non_unions.get(f'{x[0]}_type', 0),
                x[1]
            ))
        )(mutation.items())

        mutation = cast(Dict[str, Any], dt.merge(non_unions, unions))

        return Table(serializer, skeleton, buffer, offset, mutation)

    def __attrs_post_init__(self):

        if self.buffer:
            self.vtable = reader.read_vtable(self.buffer, self.offset)

    def __hash__(self):
        if not self._hash:
            self._hash = hash((
                id(self.skeleton),
                id(self.buffer),
                self.offset,
                tuple(self.mutation.items())
            ))
        return self._hash

    def __getitem__(
            self: 'Table',
            key: str
    ) -> Any:

        # pylint: disable=unsupported-membership-test
        # pylint: disable=unsubscriptable-object
        # pylint: disable=unsupported-assignment-operation

        if key in self._cached_items:
            return self._cached_items[key]

        if self.mutation and key in self.mutation:
            value = self.mutation[key]
        elif key in self.skeleton.field_map:
            field_skeleton = self.skeleton.field_map[key]
            value_skeleton = field_skeleton.value_skeleton
            value = read_field(self, field_skeleton, value_skeleton)
        else:
            raise KeyError(key)

        self._cached_items[key] = value

        return value

    def __iter__(
            self: 'Table'
    ) -> Iterator[str]:
        return map(op.attrgetter('name'), self.skeleton.fields)

    def __len__(
            self: 'Table'
    ) -> int:
        return len(self.skeleton.fields)

    def __repr__(self: 'Table') -> str:
        return f"{self.type_name}({dict(self)})"

    def evolve(
            self: 'Table',
            **kwargs: Mapping[str, Any]
    ) -> 'Table':
        return Table.new(
            self.serializer,
            self.skeleton,
            self.buffer,
            self.offset,
            kwargs
        )

    def packb(self: 'Table') -> bytes:
        return builder.build(self)


###
# Field value converter
##

# Callable[[Serializer, ScalarFieldSkeleton, Skeleton, value], Any]
convert_field_value = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.convert_field_value")

@convert_field_value.register(
    Serializer, ScalarFieldSkeleton, EnumSkeleton, object)
def convert_enum_field_value(
        serializer: Serializer,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: EnumSkeleton,
        value: Any
) -> enum.IntEnum:
    # pylint: disable=unused-argument
    return any_to_enum(value_skeleton.value_factory, value)


@convert_field_value.register(
    Serializer, ScalarFieldSkeleton, ScalarSkeleton, object)
def convert_scalar_field_value(
        serializer: Serializer,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: ScalarSkeleton,
        value: Any
) -> Scalar:
    # pylint: disable=unused-argument

    pytype = PYTYPE_MAP[value_skeleton.value_type]
    format_ = FORMAT_MAP[value_skeleton.value_type]

    value = pytype(value)

    try:
        struct.pack(format_, value)
    except struct.error as exc:
        raise ValueError(
            f"Bad value for {field_skeleton.name}: "
            + ' '.join(exc.args)
        )

    return value


@convert_field_value.register(
    Serializer, ScalarFieldSkeleton, StructSkeleton, object)
def convert_struct_field_value(
        serializer: Serializer,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: StructSkeleton,
        value: Any
) -> Struct:
    # pylint: disable=unused-argument
    return Struct.new(
        serializer,
        value_skeleton,
        None,
        0,
        value
    )

@convert_field_value.register(
    Serializer, ScalarFieldSkeleton, TableSkeleton, type(None))
def convert_table_field_value_from_none(
        serializer: Serializer,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: TableSkeleton,
        value: None
) -> Optional[Container]:
    # pylint: disable=unused-argument
    return None


@convert_field_value.register(
    Serializer, ScalarFieldSkeleton, TableSkeleton, Container)
def convert_table_field_value_from_container(
        serializer: Serializer,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: TableSkeleton,
        value: Container
) -> Optional[Container]:
    # pylint: disable=unused-argument

    if (not isinstance(value, Table)
            or value.skeleton != value_skeleton):
        raise ValueError(
            f"Bad value for {field_skeleton.name}: {value}"
        )

    return value


@convert_field_value.register(
    Serializer, ScalarFieldSkeleton, TableSkeleton, object)
def convert_table_field_value(
        serializer: Serializer,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: TableSkeleton,
        value: Any
) -> Optional[Container]:
    # pylint: disable=unused-argument
    return Table.new(
        serializer,
        value_skeleton,
        None,
        0,
        value
    )


def convert_union_fields(
        serializer: Serializer,
        field_skeleton: ScalarFieldSkeleton,
        union_skeleton: UnionSkeleton,
        union_type: int,
        value: Any
) -> Tuple[Tuple[str, enum.IntEnum], Tuple[str, Optional[Table]]]:

    enum_class = union_skeleton.enum_skeleton.value_factory
    assert issubclass(enum_class, enum.IntEnum)  # type: ignore
    key = field_skeleton.name
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
            v: k for k, v in union_skeleton.value_skeletons.items()
        }
        try:
            union_type = union_type_map[value.skeleton]
        except KeyError:
            raise ValueError(f'{value.skeleton.type_name} is bad type '
                             f'for union field "{key}".')
        container = value
    else:
        if union_type == 0:
            raise ValueError(f'Union type "{enum_key}" is not provided.')

        value_skeleton = union_skeleton.value_skeletons[union_type]
        assert isinstance(value_skeleton, TableSkeleton)
        container = Table.new(
            serializer,
            value_skeleton,
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
# Callable[[Table, ScalarFieldSkeleton, Skeleton], Any]
read_field = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.read_field")


@read_field.register(Table, ScalarFieldSkeleton, EnumSkeleton)
def read_enum_field(
        table: Table,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: EnumSkeleton
) -> Scalar:

    enum_class = value_skeleton.value_factory
    assert issubclass(enum_class, (enum.IntEnum, enum.IntFlag))  # type: ignore

    value = read_scalar_field(table, field_skeleton, value_skeleton)
    assert isinstance(value, int)

    return enum_class(value)  # type: ignore


@read_field.register(Table, ScalarFieldSkeleton, ScalarSkeleton)
def read_scalar_field(
        table: Table,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: Union[ScalarSkeleton, EnumSkeleton]
) -> Scalar:

    if not table.buffer or not table.offset:
        return field_skeleton.default

    assert isinstance(table.vtable, tuple)
    idx = field_skeleton.index
    if idx >= len(table.vtable):
        return field_skeleton.default

    foffset = table.vtable[idx]
    if not foffset:
        return field_skeleton.default

    return reader.read_scalar(
        FORMAT_MAP[value_skeleton.value_type],
        table.buffer,
        table.offset + foffset
    )


@read_field.register(Table, ScalarFieldSkeleton, StructSkeleton)
def read_struct_field(
        table: Table,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: StructSkeleton
) -> Optional[Struct]:

    if not table.buffer or not table.offset:
        return None

    assert isinstance(table.vtable, tuple)
    idx = field_skeleton.index
    if idx >= len(table.vtable):
        return field_skeleton.default

    foffset = table.vtable[idx]
    if not foffset:
        return None

    return Struct.new(
        table.serializer,
        value_skeleton,
        table.buffer,
        table.offset + foffset,
        None,
    )


@read_field.register(Table, ScalarFieldSkeleton, TableSkeleton)
def read_table_field(
        table: Table,
        field_skeleton: ScalarFieldSkeleton,
        value_skeleton: TableSkeleton
) -> Optional[Table]:

    if not table.buffer or not table.offset:
        return None

    assert isinstance(table.vtable, tuple)
    idx = field_skeleton.index
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
        value_skeleton,
        table.buffer,
        offset,
        dict()
    )


@read_field.register(Table, ScalarFieldSkeleton, UnionSkeleton)
def read_union_field(
        table: Table,
        field_skeleton: ScalarFieldSkeleton,
        union_skeleton: UnionSkeleton
) -> Optional[Container]:

    union_type = table[f'{field_skeleton.name}_type']
    if union_type == 0:
        return None

    value_skeleton = union_skeleton.value_skeletons[union_type]

    return read_table_field(table, field_skeleton, value_skeleton)


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
        if isinstance(value, Table):
            yield from builder.flatten(recursion_limit - 1, value)

    yield table


@builder.calc_size.register(int, Table)
def calc_table_size(
        size: UOffset,
        table: Table
) -> USize:
    field_count = 0
    for key, value in table.items():
        field_skeleton = table.skeleton.field_map[key]
        if value == field_skeleton.default:
            continue
        value_skeleton = field_skeleton.value_skeleton
        size += value_skeleton.inline_size
        size += -size % value_skeleton.inline_align
        field_count = max(field_count, field_skeleton.index + 1)

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


@inline_value.register(int, dict, Struct)
def inline_struct_value(offset, offset_map, value):
    # pylint: disable=unused-argument
    yield value.asbytes()


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


def align_blocks(
        cursor: USize,
        blocks: Iterable[InlineBlock]
) -> Sequence[InlineBlock]:
    packed: Deque[InlineBlock] = collections.deque()
    pending = sorted(blocks, key=lambda x: (-x.size, -x.index))

    if not pending:
        return packed

    while pending:
        gap = -(cursor + pending[0].size) % pending[0].align
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
            table.skeleton.field_map[x].index,
            table.skeleton.field_map[x].value_skeleton.inline_size,
            table.skeleton.field_map[x].value_skeleton.inline_align,
            table.skeleton.field_map[x].value_skeleton.inline_format,
            table[x],
        )),
        ft.curry(filter)(lambda x: table[x]
                         != table.skeleton.field_map[x].default)
    )(table.keys())

    from pprint import pprint
    pprint(inline_blocks)

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
