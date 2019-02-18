"""
TODO Write module docstring
"""
# pylint: disable=missing-docstring

from typing import IO, Optional

import click

import flatboobs.parser
import flatboobs.schema
from flatboobs import FlatBuffers, Registry, asnative, logging


@click.command(help="Unpack FlatBuffers message.")
@click.option(
    '-s', '--schema-file',
    help='Load schema from file.',
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
    help='Load schema from python package.',
    type=click.STRING
)
@click.option(
    '-n', '--namespace',
    help='Use schema namespace.',
    type=click.STRING
)
@click.option(
    '-t', '--type', 'root_type',
    help='Override message root type.',
    type=click.STRING
)
@click.option(
    '-f', '--output-format',
    help='Output format.',
    type=click.Choice(['json', 'yaml', 'pprint']),
    default='json'
)
@click.option(
    '-o', '--output', 'output_file',
    help='Output file.',
    type=click.File('w'),
    default='-'
)
@click.argument(
    "input_file",
    type=click.File('rb')
)
def unpack(
        # pylint: disable=too-many-arguments
        schema_file: Optional[str],
        schema_package: Optional[str],
        namespace: Optional[str],
        root_type: Optional[str],
        output_format: str,
        output_file: IO,
        input_file: IO,
):
    # pylint: disable=too-many-locals
    registry = Registry(namespace)
    serializer = FlatBuffers(registry)
    if schema_file:
        sch = flatboobs.parser.load_from_file(schema_file)
        registry.add_types(sch)  # TODO replace with add_schema()
        namespace = sch.namespace
        root_type = root_type or sch.root_type
    if schema_package:
        raise NotImplementedError  # TODO implement loading schema from module

    message = input_file.read()
    container = serializer.unpackb(root_type, message)

    dct = asnative(container)

    if output_format == 'json':
        import json
        json.dump(dct, output_file, indent=2, ensure_ascii=False)
    elif output_format == 'yaml':
        import yaml
        yaml.dump(dct, stream=output_file)
    elif output_format == 'pprint':
        import pprint
        output_file.write(pprint.pformat(dct))
    else:
        raise RuntimeError(f"Unknown output format {output_format}")

    if output_file.name == '<stdout>':
        output_file.write('\n')


@click.group()
@click.option('--debug/--no-debug', default=None)
def main(debug):
    logging.setup_logging(debug)


main.add_command(unpack)

if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter
