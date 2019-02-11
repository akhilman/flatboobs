"""
Registry class is main access point for flatboobs functionality
"""

import collections
import importlib
import pathlib
from typing import Any, Dict, Iterable, Optional, Set, Union, cast

import attr
import toolz.functoolz as ft

import flatboobs.abc as abc
from flatboobs import logging, parser, schema
from flatboobs.constants import (
    INTEGER_TYPES,
    PYTYPE_MAP,
    SCALAR_TYPES,
    STRING_TO_SCALAR_TYPE_MAP,
    BaseType
)
from flatboobs.typing import Scalar, TemplateId, UOffset

# pylint: disable=missing-docstring  # TODO write docstrings

logger = logging.getLogger('flatboobs')


def _load_backend(
        arg: Union[None, Iterable[str], str, abc.Backend] = 'auto'
) -> abc.Backend:

    if isinstance(arg, abc.Backend):
        return arg

    if not arg or arg == 'auto':
        import flatboobs.backends
        variants = flatboobs.backends.BACKENDS
    elif isinstance(arg, str):
        variants = [arg]

    backend = None
    error = None
    for variant in variants:
        logger.debug(f'Trying to load backend "{variant}"')
        mod_name = f"flatboobs.backends.{variant}"
        try:
            mod = importlib.import_module(mod_name)
            backend = mod.BACKEND  # type: ignore
        except ImportError as exc:
            logger.debug(f'Can not import backend module "{mod_name}"')
            error = exc
        else:
            logger.debug(f'Backend module "{mod_name}" loaded')
            break

    if not backend:
        raise RuntimeError(f'Can not load any backend from: {arg}') from error

    return backend()


@attr.s(auto_attribs=True)
class Registry:

    backend: abc.Backend = attr.ib(None, converter=_load_backend)
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

        cache_key = namespace or ''
        type_map = self._cached_type_maps.get(cache_key, None)
        if type_map:
            return type_map

        if namespace:
            types = filter(lambda x: x.namespace == namespace, self.types)
        else:
            types = iter(self.types)

        # pylint: disable=unsupported-assignment-operation  # attr.ib
        type_map = {x.name: x for x in types}
        self._cached_type_maps[cache_key] = type_map

        return type_map

    def type_by_name(
            self: 'Registry',
            type_name: str,
            namespace: Optional[str] = None
    ) -> schema.TypeDeclaration:
        type_decl = self._type_map(namespace)[type_name]
        return type_decl

    def type_by_identifier(
            self: 'Registry',
            file_identifier: str,
            namespace: Optional[str] = None
    ) -> schema.TypeDeclaration:

        namespace = namespace or ''
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

    def _add_enum_template(
            self: 'Registry',
            type_decl: schema.Enum
    ) -> abc.TemplateId:

        bit_flags = 'bit_flags' in type_decl.metadata_map
        value_type = STRING_TO_SCALAR_TYPE_MAP.get(
            type_decl.type, BaseType.NULL)

        if value_type not in INTEGER_TYPES:
            raise TypeError(
                'Enum value type should be one of '
                f'{INTEGER_TYPES}, but {value_type or type_decl.type} is given'
            )

        template = self.backend.new_enum_template(
            type_decl.namespace, type_decl.name,
            type_decl.file_identifier or '',
            value_type, bit_flags
        )

        if bit_flags:
            template.add_member('NONE', 0)

        for member in type_decl.members:
            template.add_member(member.name, member.value)

        if bit_flags:
            template.add_member('ALL', sum(x.value for x in type_decl.members))

        return template.finish()

    def _add_template_field(
            self: 'Registry',
            type_map: Dict[str, schema.TypeDeclaration],
            template: Union[abc.TableTemplate, abc.StructTemplate],
            field: schema.Field,
    ) -> None:

        # pylint: disable=too-many-branches

        value_type = STRING_TO_SCALAR_TYPE_MAP.get(field.type, BaseType.VOID)

        if value_type in SCALAR_TYPES:

            pytype = PYTYPE_MAP[value_type]

            default: Scalar
            if field.default is None:
                default = pytype()
            else:
                default = pytype(field.default)

            template.add_scalar_field(
                field.name,
                field.is_vector,
                value_type,
                default
            )
            return

        # StructTemplate should not be here
        assert isinstance(template, abc.TableTemplate)

        if value_type == BaseType.STRING:
            template.add_string_field(
                field.name,
                field.is_vector,
            )
            return

        if field.type not in type_map:
            raise TypeError(
                f'Unknown type "{field.type}" for field "{field.name}" '
                f'of "{template.type_name}"'
            )

        value_type_decl = type_map[field.type]
        value_template_id = self._get_add_template(value_type_decl)

        if isinstance(value_type_decl, schema.Enum):
            default = field.default
            if default is None:
                if 'bit_flags' in value_type_decl.metadata_map:
                    default = 0
                else:
                    default = value_type_decl.members[0].value
            if isinstance(default, str):
                try:
                    default = value_type_decl.members_map[default]
                except KeyError as exc:
                    raise KeyError(
                        f'Unknown member "{default}" '
                        f'for enum {template.schema.name}'
                    ) from exc

            default = int(cast(int, default))

            template.add_enum_field(
                field.name,
                field.is_vector,
                value_template_id,
                default
            )
            return

        if isinstance(value_type_decl, schema.Struct):
            template.add_struct_field(
                field.name,
                field.is_vector,
                value_template_id
            )
            return

        if isinstance(value_type_decl, schema.Table):
            template.add_table_field(
                field.name,
                field.is_vector,
                value_template_id
            )
            return

        if isinstance(value_type_decl, schema.Union):
            template.add_union_field(
                field.name,
                value_template_id
            )
            return

        raise RuntimeError('We should not be here')

    def _add_struct_template(
            self: 'Registry',
            type_decl: schema.Struct,
    ) -> TemplateId:

        type_map = self._type_map(type_decl.namespace)
        template = self.backend.new_struct_template(
            type_decl.namespace, type_decl.name,
            type_decl.file_identifier or ''
        )

        for field in type_decl.fields:

            if field.is_vector:
                raise TypeError(
                    f'Struct "{type_decl.name}" field "{field.name}" '
                    'could not be vector.'
                )

            if (field.type not in STRING_TO_SCALAR_TYPE_MAP
                    and not isinstance(
                        type_map.get(field.type, None),
                        schema.Enum
                    )):
                raise TypeError(
                    f'Struct "{type_decl.name}" field "{field.name}" type '
                    f'could not be {field.type}'
                )

            self._add_template_field(type_map, template, field)

        return template.finish()

    def _add_table_template(
            self: 'Registry',
            type_decl: schema.Table,
    ) -> TemplateId:

        type_map = self._type_map(type_decl.namespace)
        template = self.backend.new_table_template(
            type_decl.namespace, type_decl.name,
            type_decl.file_identifier or ''
        )

        # TODO чего будем с векторами делать?
        for field in type_decl.fields:

            if 'deprecated' in field.metadata_map:
                template.add_depreacated_field()
                continue

            self._add_template_field(type_map, template, field)

        return template.finish()

    def _add_union_template(
            self: 'Registry',
            type_decl: schema.Union,
    ) -> TemplateId:

        type_map = self._type_map(type_decl.namespace)
        template = self.backend.new_union_template(
            type_decl.namespace, type_decl.name,
            type_decl.file_identifier or ''
        )

        for member in type_decl.members:

            value_type_decl = type_map.get(member.name, None)

            if not isinstance(value_type_decl, schema.Table):
                raise TypeError(
                    f'Union "{type_decl.name}" member "{member.name}" type '
                    f'should be Table but "{member.name}" is given'
                )

            value_template_id = self._get_add_template(value_type_decl)
            template.add_member(member.value, value_template_id)

        return template.finish()

    def _get_add_template(
            self: 'Registry',
            type_decl: schema.TypeDeclaration,
    ) -> TemplateId:

        template_id = self.backend.get_template_id(
            type_decl.namespace, type_decl.name)
        if template_id >= 0:
            # template already registered
            return template_id

        if isinstance(type_decl, schema.Struct):
            template_id = self._add_struct_template(type_decl)
        elif isinstance(type_decl, schema.Table):
            template_id = self._add_table_template(type_decl)
        elif isinstance(type_decl, schema.Union):
            pass
        elif isinstance(type_decl, schema.Enum):
            template_id = self._add_enum_template(type_decl)

        return template_id

    def _create_container(
            self: 'Registry',
            type_decl: schema.TypeDeclaration,
            buffer: Optional[bytes] = None,
            offset: UOffset = 0,
            mutation: Any = None
    ) -> abc.Container:

        template = self._get_add_template(type_decl)

        container = self.backend.new_container(
            template, buffer, offset, mutation)

        return container

    def new(
            self: 'Registry',
            type_name: str,
            mutation: Any = None,
            *,
            namespace: Optional[str] = None,
    ) -> abc.Container:

        type_decl = self.type_by_name(type_name, namespace)
        return self._create_container(type_decl, mutation=mutation)

    def unpackb(
            self: 'Registry',
            buffer: bytes,
            *,
            namespace: Optional[str] = None,
            root_type: Optional[str] = None,
    ) -> abc.Container:

        header = self.backend.read_header(buffer)

        if root_type:
            root_type_decl = self.type_by_name(root_type, namespace)
        elif header.file_identifier:
            root_type_decl = self.type_by_identifier(header.file_identifier,
                                                     namespace)
        else:
            raise TypeError(
                'Missing required root_type argument or file idenitifer.')

        return self._create_container(
            root_type_decl,
            buffer,
            header.root_offset
        )

    @staticmethod
    def packb(
            container: abc.Container
    ) -> bytes:

        return container.packb()

    loads = unpackb
    dumps = packb
