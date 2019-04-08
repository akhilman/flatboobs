# pylint: disable=missing-docstring

from typing import Any, Union

from flatboobs import idl  # type: ignore


def instance_of(obj: Any, class_name: str) -> bool:
    return obj.__class__.__name__ == class_name


def defined_here(
        definition: Union[idl.StructDef, idl.EnumDef],
        parser: idl.Parser,
) -> bool:
    return parser.included_files[definition.file] == ""


TESTS = {
    'instance_of': instance_of,
    'defined_here': defined_here
}
