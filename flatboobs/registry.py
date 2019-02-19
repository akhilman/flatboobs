"""
Registry class is main access point for flatboobs functionality
"""

import collections
import pathlib
from typing import Dict, Iterable, Optional, Set, Union

import attr
import toolz.functoolz as ft

import flatboobs.abc as abc
from flatboobs import logging, parser, schema
from flatboobs.constants import BASE_TYPE_ALIASES, BASE_TYPES

# pylint: disable=missing-docstring  # TODO write docstrings

logger = logging.getLogger('flatboobs')


@attr.s(auto_attribs=True)
class Registry(abc.Registry):

    default_namespace: Optional[str] = None

    types: Set[schema.TypeDeclaration] = attr.ib(factory=set)

    _cached_type_maps: \
        Dict[str, Dict[str, schema.TypeDeclaration]] \
        = attr.ib(factory=dict, init=False, repr=False, cmp=False)
    _cached_types_by_identifier: \
        Dict[str, Dict[str, schema.TypeDeclaration]] = attr.ib(
            factory=ft.partial(collections.defaultdict, dict),
            init=False, repr=False, cmp=False
        )

    def add_types(
            self: 'Registry',
            types: Union[Iterable[schema.TypeDeclaration], schema.Schema]
    ) -> None:

        if isinstance(types, schema.Schema):
            types = types.types

        # pylint: disable=unsupported-assignment-operation  # attr.ib
        self.types |= set(types)
        self._cached_type_maps.clear()

    def load_schema_from_string(
            self: 'Registry',
            source: str,
            schema_file: Optional[str] = None,
    ) -> None:
        self.add_types(parser.load_from_string(source, schema_file))

    def load_schema_from_file(
            self: 'Registry',
            fpath: Union[pathlib.Path, str],
    ) -> None:
        self.add_types(parser.load_from_file(fpath))

    def load_schema_from_directory(
            self: 'Registry',
            path: Union[pathlib.Path, str],
            suffix: str = '.fbs'
    ) -> None:
        for schema_ in parser.load_from_directory(path, suffix):
            self.add_types(schema_)

    def load_schema_from_package(
            self: 'Registry',
            package: str,
            suffix: str = '.fbs'
    ) -> None:
        for schema_ in parser.load_from_package(package, suffix):
            self.add_types(schema_)

    def _type_map(
            self: 'Registry',
            namespace: Optional[str],
    ) -> Dict[str, schema.TypeDeclaration]:

        namespace = namespace or self.default_namespace or ''
        type_map = self._cached_type_maps.get(namespace, None)
        if type_map:
            return type_map

        if namespace:
            types = filter(lambda x: x.namespace == namespace, self.types)
        else:
            types = iter(self.types)

        # pylint: disable=unsupported-assignment-operation  # attr.ib
        type_map = {x.name: x for x in types}
        self._cached_type_maps[namespace] = type_map

        return type_map

    def type_by_name(
            self: 'Registry',
            type_name: str,
            namespace: Optional[str] = None
    ) -> schema.TypeDeclaration:
        type_decl: schema.TypeDeclaration
        if type_name == 'string':
            type_decl = schema.String()
        elif type_name in BASE_TYPES | set(BASE_TYPE_ALIASES):
            type_ = BASE_TYPE_ALIASES.get(type_name, type_name)
            type_decl = schema.Scalar(name=type_)
        else:
            type_decl = self._type_map(namespace)[type_name]
        return type_decl

    def type_by_identifier(
            self: 'Registry',
            file_identifier: str,
            namespace: Optional[str] = None
    ) -> schema.TypeDeclaration:

        namespace = namespace or self.default_namespace or ''
        ident_map = self._cached_types_by_identifier.get(namespace, None)
        if ident_map:
            type_decl = ident_map.get(file_identifier, None)
            if type_decl:
                return type_decl

        type_map = self._type_map(namespace)
        ident_map = {x.file_identifier: x
                     for x in type_map.values() if x.file_identifier}
        type_decl = ident_map[file_identifier]
        # pylint: disable=unsupported-assignment-operation  # attr.ib
        self._cached_types_by_identifier[namespace] = ident_map

        return type_decl
