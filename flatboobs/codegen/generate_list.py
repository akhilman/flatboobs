# pylint: disable=missing-docstring

from pathlib import Path
from typing import Any, Mapping, Sequence

import click

from flatboobs import load_schema


def generate_list(
        schema_files: Sequence[Path],
        include_paths: Sequence[Path],
        options: Mapping[str, Any],
) -> None:
    # pylint: disable=unused-argument

    all_schema = set()
    for schema_file, _ in load_schema(schema_files, include_paths):
        all_schema.add(str(schema_file.resolve()))

    click.echo('\n'.join(sorted(all_schema)))
