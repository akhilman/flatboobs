# pylint: disable=missing-docstring

from typing import Any


def instance_of(obj: Any, class_name: str) -> bool:
    return obj.__class__.__name__ == class_name


TESTS = {
    'instance_of': instance_of,
}
