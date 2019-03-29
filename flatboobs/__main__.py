"""
TODO Write module docstring
"""
# pylint: disable=missing-docstring

from pathlib import Path
from typing import Sequence

import click

from flatboobs import logging
from flatboobs.codegen import generate


@click.command(help="Generates [de]serializer code.")
@click.option('--debug/-no-debug', default=False)
@click.option(
    '--output-dir', '-o', default='./',
    type=click.Path(
        file_okay=False, dir_okay=True, writable=True,
        resolve_path=True))
@click.option(
    '--include-path', '-I', multiple=True,
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True,
        resolve_path=True))
@click.option('--header-only/--no-header-only', default=False,
              help="Generated header only library")
@click.option('--grpclib', default=False)
@click.option('--python/--no-python', default=False,
              help="Generate python module")
@click.argument(
    'schema_file', nargs=-1,
    type=click.Path(
        file_okay=True, dir_okay=False, readable=True, resolve_path=True))
def main(
        # pylint: disable=too-many-arguments
        debug: bool = False,
        output_dir: str = './',
        include_path: Sequence[str] = tuple(),
        schema_file: Sequence[str] = tuple(),
        **kwargs
):
    logging.setup_logging(debug)

    generate(
        list(map(Path, schema_file)),
        list(map(Path, include_path)),
        Path(output_dir),
        options=kwargs
    )


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    # pylint: disable=unexpected-keyword-arg
    main(obj=dict())
