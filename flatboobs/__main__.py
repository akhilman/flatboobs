"""
TODO Write module docstring
"""

from typing import IO, Optional

import click
import yaml

import flatboobs.parser
import flatboobs.schema
from flatboobs import logging

# pylint: disable=no-value-for-parameter

@click.command()
@click.option(
    '-s', '--schema-file',
    help='load schema from file',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True
    ),
)
@click.option(
    '-p', '--schema-package',
    help='load schema from python package',
    type=click.STRING
)
@click.option(
    '-n', '--namespace',
    help='namespace',
    type=click.STRING
)
@click.option(
    '-t', '--type', 'root_type',
    help='root type',
    type=click.STRING
)
@click.argument(
    "message_file",
    type=click.File('rb')
)
def cat(
        schema_file: Optional[str],
        schema_package: Optional[str],
        namespace: Optional[str],
        root_type: Optional[str],
        message_file: IO
):
    types = set()
    if schema_file:
        sch = flatboobs.schema.load_from_file(schema_file)
        root_type = root_type or sch.root_type
        types |= set(flatboobs.schema.extract_types(sch))
    if schema_package:
        raise NotImplementedError

    from pprint import pprint
    pprint(list(types))

    # backend = backend
    # unpackb(backend, types, message_file.read(), root_type)


@click.group()
@click.option('--debug/--no-debug', default=None)
def main(debug):
    logging.setup_logging(debug)


main.add_command(cat)

if __name__ == '__main__':
    main()
