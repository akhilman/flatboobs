# pylint: disable=missing-docstring

from pathlib import Path
from typing import Any, Mapping


def instance_of(obj: Any, class_name: str) -> bool:
    return obj.__class__.__name__ == class_name


def tests(
        output_dir: Path,
        options: Mapping[str, Any]

):
    # pylint: disable=unused-argument
    return {
        'instance_of': instance_of,
    }
