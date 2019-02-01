"""
TODO Write module docstring
"""
# pylint: disable=missing-docstring

from typing import IO, Optional

import click
import toolz.functoolz as ft
import toolz.itertoolz as it

import flatboobs.parser
import flatboobs.schema
from flatboobs import logging
from flatboobs.registry import Registry

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
    # pylint: disable=unused-argument
    registry = Registry()
    if schema_file:
        sch = flatboobs.parser.load_from_file(schema_file)
        registry.add_types(sch)
        root_type = root_type or sch.root_type
    if schema_package:
        raise NotImplementedError

    root_type_decl = ft.compose(
        it.first,
        ft.partial(filter, lambda x: x.name == root_type)
    )(registry.types)

    from pprint import pprint
    pprint(list(registry.types))
    pprint('------')
    pprint(root_type_decl)

    # backend = backend
    # unpackb(backend, types, message_file.read(), root_type)


@click.group()
@click.option('--debug/--no-debug', default=None)
def main(debug):
    logging.setup_logging(debug)


main.add_command(cat)

if __name__ == '__main__':
    main()
