"""
Registry class is main access point for flatboobs functionality
"""

import collections
import importlib
import pathlib
from typing import Any, Dict, Iterable, Optional, Set, Union

import attr
import toolz.functoolz as ft

import flatboobs.abc as abc
from flatboobs import logging, schema
from flatboobs.constants import PYTYPE_MAP, SCALAR_TYPES, BasicType
from flatboobs.typing import TemplateId, UOffset

# pylint: disable=missing-docstring  # TODO write docstrings

logger = logging.getLogger('flatboobs')

UNDEFINED = object()


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
        self.add_types(schema.load_from_string(source, schema_file))

    def load_schema_from_file(
            self: 'Registry',
            fpath: Union[pathlib.Path, str],
    ) -> None:
        self.add_types(schema.load_from_file(fpath))

    def load_schema_from_directory(
            self: 'Registry',
            path: Union[pathlib.Path, str],
            suffix: str = '.fbs'
    ) -> None:
        for schema_ in schema.load_from_directory(path, suffix):
            self.add_types(schema_)

    def load_schema_from_package(
            self: 'Registry',
            package: str,
            suffix: str = '.fbs'
    ) -> None:
        for schema_ in schema.load_from_package(package, suffix):
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

    def _type_by_name(
            self: 'Registry',
            namespace: Optional[str],
            type_name: str
    ) -> schema.TypeDeclaration:
        type_decl = self._type_map(namespace)[type_name]
        return type_decl

    def _type_by_identifier(
            self: 'Registry',
            namespace: Optional[str],
            file_identifier: str
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
        # pylint: disable=unsubscriptable-object  # attr.ib
        self._cached_types_by_identifier[namespace][file_identifier] \
            = type_decl

        return type_decl

    def _add_enum_template(
            self: 'Registry',
            type_decl: schema.Enum
    ) -> abc.TemplateId:

        bit_flags = 'bit_flags' in type_decl.metadata_map
        type_map = self._type_map(type_decl.namespace)
        value_type = schema.type_by_name(type_map, type_decl.type)

        assert isinstance(value_type, BasicType)

        template = self.backend.new_enum_template(
            type_decl, value_type, bit_flags)

        if bit_flags:
            template.add_member('NONE', 0)

        for member in type_decl.members:
            template.add_member(member.name, member.value)

        if bit_flags:
            template.add_member('ALL', sum(x.value for x in type_decl.members))

        return template.finish()

    def _add_template_member(
            # pylint: disable=too-many-arguments
            self: 'Registry',
            namespace: Optional[str],
            template: abc.Template,
            method_suffix: str,
            type_name: str,
            pre_args: Iterable[Any],
            default=UNDEFINED,
    ) -> None:

        # pylint: disable=too-many-branches

        type_map = self._type_map(namespace)

        member_type = schema.type_by_name(type_map, type_name)

        def adder(type_, *args):
            meth = getattr(template, f'add_{type_}{method_suffix}')
            meth(*pre_args, *args)

        if isinstance(member_type, (
                schema.Struct, schema.Table, schema.Enum, schema.Union
        )):
            member_template_id = self._get_add_template(member_type)
        else:
            member_template_id = TemplateId(-1)

        if member_type in SCALAR_TYPES:
            fun = ft.partial(adder, 'scalar', member_type)
            if default is not UNDEFINED:
                # member_type here is always instance of BasicType
                # because of all values in SCALAR_TYPES are BasicType instances
                pytype = PYTYPE_MAP[member_type]  # type: ignore
                fun(default and pytype(default) or pytype())  # type: ignore
            else:
                fun()
        elif member_type == BasicType.STRING:
            adder('string')
        elif isinstance(member_type, schema.Struct):
            adder('struct', member_template_id)
        elif isinstance(member_type, schema.Table):
            adder('table', member_template_id)
        elif isinstance(member_type, schema.Union):
            adder('union', member_template_id)
        elif isinstance(member_type, schema.Enum):
            fun = ft.partial(adder, 'enum', member_template_id)
            if default is not UNDEFINED:
                if not default:
                    if 'bit_flags' in member_type.metadata_map:
                        default = 0
                    else:
                        default = member_type.members[0].value
                elif isinstance(default, str):
                    default = member_type.members_map[default]
                else:
                    default = int(default)
                fun(default)
            else:
                fun()

    def _add_struct_template(
            self: 'Registry',
            type_decl: schema.Struct,
    ) -> TemplateId:

        template = self.backend.new_struct_template(type_decl)

        for field in type_decl.fields:
            self._add_template_member(
                type_decl.namespace,
                template,
                '_field',
                field.type,
                (field.name, field.is_vector),
                field.default
            )

        return template.finish()

    def _add_table_template(
            self: 'Registry',
            type_decl: schema.Table,
    ) -> TemplateId:

        template = self.backend.new_table_template(type_decl)

        for field in type_decl.fields:
            if 'deprecated' in field.metadata_map:
                template.add_depreacated_field()
                continue
            self._add_template_member(
                type_decl.namespace,
                template,
                '_field',
                field.type,
                (field.name, field.is_vector),
                field.default
            )

        return template.finish()

    def _add_union_template(
            self: 'Registry',
            type_decl: schema.Union,
    ) -> TemplateId:

        template = self.backend.new_union_template(type_decl)

        for member in type_decl.members:
            self._add_template_member(
                type_decl.namespace,
                template,
                '_member',
                member.name,
                (member.value,),
            )

        return template.finish()

    def _get_add_template(
            self: 'Registry',
            type_decl: schema.TypeDeclaration,
    ) -> TemplateId:

        template_id = self.backend.get_template_id(type_decl)
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
            offset: UOffset = 0
    ) -> abc.Container:

        template = self._get_add_template(type_decl)

        if buffer:
            container = self.backend.new_container(template, buffer, offset)
        else:
            container = self.backend.new_container(template, buffer)

        return container

    def new(
            self: 'Registry',
            *,
            namespace: Optional[str] = None,
            type_name: Optional[str] = None,
            file_identifier: Optional[str] = None,
    ) -> abc.Container:

        if type_name:
            type_decl = self._type_by_name(namespace, type_name)
        elif file_identifier:
            type_decl = self._type_by_identifier(namespace, file_identifier)
        else:
            raise TypeError('Missing required type or idenitifer argument.')

        return self._create_container(type_decl)

    def unpackb(
            self: 'Registry',
            buffer: bytes,
            *,
            namespace: Optional[str] = None,
            type_name: Optional[str] = None,
    ) -> abc.Container:

        header = self.backend.read_header(buffer)

        if type_name:
            type_decl = self._type_by_name(namespace, type_name)
        elif header.file_identifier:
            type_decl = self._type_by_identifier(namespace,
                                                 header.file_identifier)
        else:
            raise TypeError(
                'Missing required type_name argument or file idenitifer.')

        return self._create_container(
            type_decl,
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
