# pylint: disable=missing-docstring

import collections
import operator as op
import struct
from typing import Any, Iterator, Mapping, Optional, Sequence, Tuple, Union

import attr

import toolz.dicttoolz as dt
from flatboobs import abc
from flatboobs.compat import numpy as np
from flatboobs.typing import DType, NDArray, Scalar, UOffset

from . import reader
from .abc import Container, Serializer
from .skeleton import StructSkeleton


@attr.s(auto_attribs=True, slots=True, cmp=False, repr=False)
class Struct(Container[StructSkeleton], abc.Struct):

    # pylint: disable=too-many-ancestors
    serializer: Serializer
    skeleton: StructSkeleton
    buffer: bytes
    offset: UOffset = 0
    _cached_values: Optional[Tuple[Scalar, ...]] = attr.ib(None, init=False)
    _hash: int = 0

    @staticmethod
    def new(
            serializer: Serializer,
            skeleton: StructSkeleton,
            buffer: Optional[bytes],
            offset: UOffset,
            mutation: Union[None, bytes, Sequence, Mapping]
    ) -> 'Struct':

        def from_values(values):
            try:
                mutation = struct.pack('<'+skeleton.struct_format, *values)
            except struct.error as exc:
                raise ValueError(*exc.args)
            return Struct(serializer, skeleton, mutation, 0)

        if buffer and not mutation:
            return Struct(serializer, skeleton, buffer, offset)

        if not mutation:
            mutation = tuple(map(op.attrgetter('default'), skeleton.fields))
            return from_values(mutation)

        if isinstance(mutation, bytes):
            if len(mutation) != skeleton.inline_size:
                raise ValueError(
                    f'Mutation should have {skeleton.inline_size} bytes')
            return Struct(serializer, skeleton, mutation, 0)

        if isinstance(mutation, collections.abc.Mapping):
            bad_keys = set(mutation) - set(skeleton.field_map)
            if bad_keys:
                raise KeyError(', '.join(bad_keys))

            values = (mutation.get(k, skeleton.field_map[k].default)
                      for k in map(op.attrgetter('name'), skeleton.fields))
            return from_values(values)

        if isinstance(mutation, collections.abc.Sequence):
            if len(mutation) != len(skeleton.fields):
                raise ValueError(
                    f'Mutation should have {len(skeleton.fields)} items')
            return from_values(mutation)

        raise NotImplementedError

    @property
    def dtype(
            self: 'Struct'
    ) -> DType:
        if not np or not self.skeleton.dtype:
            raise RuntimeError('numpy not available')
        return self.skeleton.dtype

    def __hash__(self):
        if not self._hash:
            self._hash = hash((id(self.skeleton), self.asbytes()))
        return self._hash

    def __getitem__(
            self: 'Struct',
            key: str
    ) -> Any:
        index = self.skeleton.field_map[key].index
        values = self._read_values()
        return values[index]

    def __iter__(
            self: 'Struct'
    ) -> Iterator[str]:
        return map(op.attrgetter('name'), self.skeleton.fields)

    def __len__(
            self: 'Struct'
    ) -> int:
        return len(self.skeleton.fields)

    def __repr__(self: 'Struct') -> str:
        return f"{self.type_name}({dict(self)})"

    def _read_values(self: 'Struct') -> Tuple[Scalar, ...]:
        if self._cached_values is not None:
            return self._cached_values
        format_ = self.skeleton.struct_format
        values = reader.read_struct(format_, self.buffer, self.offset)
        values = tuple(
            f.value_skeleton.value_factory(v)
            for f, v in zip(self.skeleton.fields, values)
        )
        self._cached_values = values
        return values

    def asarray(self: 'Struct') -> NDArray:
        dtype = self.dtype
        return np.frombuffer(self.buffer, dtype=dtype,
                             count=1, offset=self.offset)

    def asbytes(self: 'Struct') -> bytes:
        # p
        return self.buffer[self.offset:self.offset+self.skeleton.inline_size]

    def astuple(self: 'Struct') -> Tuple[Scalar, ...]:
        return self._read_values()

    def evolve(
            self: 'Struct',
            **kwargs: Mapping[str, Any]
    ) -> 'Struct':
        mutation = dt.merge(
            self,
            kwargs
        )
        return Struct.new(
            self.serializer,
            self.skeleton,
            self.buffer,
            self.offset,
            mutation
        )
