"""
TODO Write module docstring
"""
# pylint: disable=missing-docstring

from pathlib import Path
from typing import Sequence

import click

from flatboobs import logging


@click.group()
@click.option('--debug/-no-debug', default=False)
def main(
        debug: bool = False,
):
    logging.setup_logging(debug)


@main.command(help="Generates C++ [de]serializer code.")
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
@click.option(
    '--header-only/--no-header-only', default=False,
    help="Generated header only library.")
@click.option(
    '--clang-format/--no-clang-format', default=True,
    help="Apply clang-format.")
@click.argument('library_name', type=str)
@click.argument(
    'schema_file', nargs=-1,
    type=click.Path(
        file_okay=True, dir_okay=False, readable=True, resolve_path=True))
def cpp(
        # pylint: disable=too-many-arguments
        output_dir: str = './',
        include_path: Sequence[str] = tuple(),
        library_name: str = "",
        schema_file: Sequence[str] = tuple(),
        **kwargs
):
    from flatboobs.codegen.generate_cpp import generate_cpp

    generate_cpp(
        list(map(Path, schema_file)),
        list(map(Path, include_path)),
        Path(output_dir),
        library_name,
        options=kwargs
    )


@main.command(name="list",
              help="Generates list of schema files with all includes.")
@click.option(
    '--include-path', '-I', multiple=True,
    type=click.Path(
        file_okay=False, dir_okay=True, readable=True,
        resolve_path=True))
@click.argument(
    'schema_file', nargs=-1,
    type=click.Path(
        file_okay=True, dir_okay=False, readable=True, resolve_path=True))
def list_(
        # pylint: disable=too-many-arguments
        include_path: Sequence[str] = tuple(),
        schema_file: Sequence[str] = tuple(),
        **kwargs
):
    from flatboobs.codegen.generate_list import generate_list

    generate_list(
        list(map(Path, schema_file)),
        list(map(Path, include_path)),
        options=kwargs
    )


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    # pylint: disable=unexpected-keyword-arg
    main(obj=dict())
