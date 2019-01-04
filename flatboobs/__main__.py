"""
TODO Write module docstring
"""

from pathlib import Path
from typing import Sequence

import click

from flatboobs.parser import parse_file


# pylint: disable=no-value-for-parameter

@click.command()
@click.argument(
    'schema_files',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True
    ),
    nargs=-1
)
def main(schema_files: Sequence[str]):
    """
    TODO Write function docstring
    """
    schema = tuple(
        map(
            parse_file,
            map(
                Path,
                schema_files
            )
        )
    )
    print(schema)

if __name__ == '__main__':
    main()
