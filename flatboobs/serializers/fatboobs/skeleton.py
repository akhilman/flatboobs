# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods

import itertools
import operator as op
import struct
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Type,
    cast
)

import attr
import toolz.functoolz as ft

from flatboobs import schema
from flatboobs.compat import numpy as np
from flatboobs.constants import FORMAT_MAP, PYTYPE_MAP, UOFFSET_FMT, BaseType
from flatboobs.typing import DType, UOffset, USize

from .abc import Skeleton
from .enum import any_to_enum


def _default_value_factory(value=None) -> Callable[..., Any]:
    raise NotImplementedError


@attr.s(auto_attribs=True, slots=True, cmp=False)
class BaseSkeleton(Skeleton):
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    type_decl: schema.TypeDeclaration
    value_type: BaseType

    value_factory: Callable[..., Any] = attr.ib(
        _default_value_factory, init=False)
    inline_format: str = attr.ib('', init=False)
    inline_size: USize = attr.ib(0, init=False)
    inline_align: USize = attr.ib(0, init=False)

    finished: bool = attr.ib(False, init=False)

    def __attrs_post_init__(self: 'BaseSkeleton') -> None:
        if self.value_factory is _default_value_factory:
            self.value_factory = PYTYPE_MAP.get(
                self.value_type, _default_value_factory)
        if not self.inline_format:
            self.inline_format = FORMAT_MAP[self.value_type]
        self.inline_size = struct.calcsize(self.inline_format)
        self.inline_align = max(map(struct.calcsize, self.inline_format))

        if self.type_decl:
            self.namespace = self.type_decl.namespace or ''
            self.type_name = self.type_decl.name or ''
            self.file_identifier = self.type_decl.file_identifier or ''

    def finish(self: 'BaseSkeleton') -> None:
        assert not self.finished
        self.finished = True


@attr.s(auto_attribs=True, slots=True, cmp=False)
class FieldSkeleton:
    index: int
    name: str
    value_skeleton: Skeleton
    is_vector: bool
    default: Any = None


@attr.s(auto_attribs=True, slots=True, cmp=False)
class ScalarFieldSkeleton(FieldSkeleton):
    is_vector: bool = attr.ib(False, init=False)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class VectorFieldSkeleton(FieldSkeleton):
    is_vector: bool = attr.ib(False, init=True)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class EnumSkeleton(BaseSkeleton):

    value_type: BaseType
    bit_flags: bool
    value_factory: Callable[..., Any]


@attr.s(auto_attribs=True, slots=True, cmp=False)
class ScalarSkeleton(BaseSkeleton):

    pass


@attr.s(auto_attribs=True, slots=True, cmp=False)
class StringSkeleton(BaseSkeleton):

    value_type: BaseType = attr.ib(BaseType.STRING, init=False)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class _TableLikeSkeleton(BaseSkeleton):

    fields: List[FieldSkeleton] = attr.ib(factory=list, init=False)
    field_count: int = attr.ib(0, init=False)
    _field_counter: Iterator[int] = attr.ib(  # type: ignore
        factory=itertools.count,
        hash=False, init=False, repr=False
    )

    field_map: Mapping[str, FieldSkeleton] = cast(
        Mapping[str, FieldSkeleton],
        attr.ib(
            factory=dict,
            hash=False, init=False, repr=False
        )
    )

    @staticmethod
    def _find_default_value(
            field: schema.Field,
            value_skeleton: Skeleton,
    ) -> Any:
        default = field.default
        if isinstance(value_skeleton, ScalarSkeleton):
            assert value_skeleton.value_factory
            if default is None:
                default = value_skeleton.value_factory()
            else:
                default = value_skeleton.value_factory(default)
        elif isinstance(value_skeleton, EnumSkeleton):
            if default is None:
                default = value_skeleton.value_factory(
                    min(value_skeleton.value_factory)  # type: ignore
                )
            else:
                default = any_to_enum(value_skeleton.value_factory, default)
        return default

    def add_field(
            self: '_TableLikeSkeleton',
            field: schema.Field,
            value_skeleton: Skeleton
    ) -> None:
        raise NotImplementedError

    def finish(self: '_TableLikeSkeleton') -> None:
        assert not self.finished
        self.field_map = {
            f.name: f for f in self.fields  # pylint: disable=not-an-iterable
        }
        self.field_count = next(self._field_counter)
        super().finish()


@attr.s(auto_attribs=True, slots=True, cmp=False)
class StructSkeleton(_TableLikeSkeleton):

    value_type: BaseType = attr.ib(BaseType.STRUCT, init=False)
    field_offsets: List[UOffset] = attr.ib(tuple(), init=False)

    struct_format: str = attr.ib('', init=False)
    dtype: Optional[DType] = attr.ib(None, init=False)

    def add_field(
            self: 'StructSkeleton',
            field: schema.Field,
            value_skeleton: Skeleton
    ) -> None:

        assert not self.finished

        index = next(self._field_counter)
        default = self._find_default_value(field, value_skeleton)

        field_skeleton = ScalarFieldSkeleton(
            index, field.name, value_skeleton, default)
        self.fields.append(field_skeleton)

    def finish(self: 'StructSkeleton') -> None:
        super().finish()

        field_offsets = []
        struct_format = ''
        struct_size = 0

        for field in self.fields:  # pylint: disable=not-an-iterable
            field_format = field.value_skeleton.inline_format
            field_size = field.value_skeleton.inline_size
            field_align = field.value_skeleton.inline_align
            pad = -struct_size % field_align if struct_size else 0
            if pad:
                struct_format += f'{pad}x'
                struct_size += pad
            field_offsets.append(struct_size)
            struct_format += field_format
            struct_size += field_size

        struct_align = ft.compose(
            max,
            ft.curry(map)(op.attrgetter('inline_align')),
            ft.curry(map)(op.attrgetter('value_skeleton')),
        )(self.fields)
        pad = -struct_size % struct_align if struct_size else 0
        if pad:
            struct_format += f'{pad}x'
            struct_size += pad

        self.struct_format = struct_format
        self.inline_format = f'{struct_size}s'
        self.inline_size = struct_size
        self.inline_align = struct_align
        self.field_offsets = field_offsets

        if np:
            self.dtype = np.dtype(
                {
                    field.name: (
                        f'<{field.value_skeleton.inline_format}',
                        offset
                    )
                    for field, offset
                    in zip(
                        self.fields,
                        field_offsets
                    )
                },
                align=True
            )
            print(self.dtype)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class TableSkeleton(_TableLikeSkeleton):

    value_type: BaseType = attr.ib(BaseType.TABLE, init=False)

    def add_depreacated_field(self: 'TableSkeleton') -> None:
        assert not self.finished
        next(self._field_counter)

    def add_field(
            self: 'TableSkeleton',
            field: schema.Field,
            value_skeleton: Skeleton
    ) -> None:

        assert not self.finished

        field_factory: Type[FieldSkeleton]
        field_skeleton: FieldSkeleton

        index = next(self._field_counter)
        default = self._find_default_value(field, value_skeleton)

        if field.is_vector:
            field_factory = VectorFieldSkeleton
        else:
            field_factory = ScalarFieldSkeleton

        field_skeleton = field_factory(
            index, field.name, value_skeleton, default)
        self.fields.append(field_skeleton)


@attr.s(auto_attribs=True, slots=True, cmp=False)
class UnionSkeleton(BaseSkeleton):

    enum_skeleton: EnumSkeleton
    value_type: BaseType = attr.ib(BaseType.UNION, init=False)
    value_skeletons: Dict[int, TableSkeleton] = \
        attr.ib(factory=dict, init=False)
    inline_format: str = attr.ib(UOFFSET_FMT, init=False)

    def add_member(
            self: 'UnionSkeleton',
            enum_value: int,
            value_skeleton: TableSkeleton
    ) -> None:
        # pylint: disable=unsupported-assignment-operation
        assert not self.finished
        self.value_skeletons[enum_value] = value_skeleton
